<template>
  <div class="class-page">
    <div class="class-card">
      <h1 class="title">Clases individuales</h1>
      <p class="subtitle">
        Seleccioná una o más fechas para inscribirte a clases individuales del turno.
      </p>

      <div class="selected-turno-box">
        <h2>{{ actividad }}</h2>
        <p><strong>Horario:</strong> {{ horaInicio }} - {{ horaFin }}</p>
        <p><strong>Días del turno:</strong> {{ dias }}</p>
        <p><strong>Sala:</strong> {{ sala }}</p>
        <p><strong>Instructor/a:</strong> {{ instructor }}</p>
      </div>

      <div v-if="loading" class="state-box">
        Cargando clases...
      </div>

      <div v-else-if="errorMessage" class="state-box error">
        {{ errorMessage }}
      </div>

      <div v-else class="field-group">
        <label class="label">Opciones disponibles</label>

        <div v-if="availableOptions.length > 0" class="options-list">
          <button
            v-for="option in availableOptions"
            :key="option.id"
            class="option-card"
            :class="{
              selected: selectedIds.has(option.id),
              enrolled: option.isEnrolled,
            }"
            :disabled="option.isEnrolled"
            @click="!option.isEnrolled && toggleOption(option.id)"
            type="button"
          >
            <div class="option-header">
              <h3>{{ option.displayDate }}</h3>

              <span v-if="option.isEnrolled" class="status-badge inscripto">
                Inscripto
              </span>
              <span v-else-if="selectedIds.has(option.id)" class="status-badge seleccionado">
                ✓ Seleccionado
              </span>
              <span v-else class="status-badge available">
                Disponible
              </span>
            </div>

            <p><strong>Período:</strong> {{ option.period }}</p>
            <p><strong>Día:</strong> {{ option.dayLabel }}</p>
            <p><strong>Horario:</strong> {{ horaInicio }} - {{ horaFin }}</p>
            <p><strong>Sala:</strong> {{ sala }}</p>

            <div class="cupos-section">
              <div class="cap-row">
                <span class="cap-text" :style="{ color: barColor(option) }">
                  {{ option.availableSpots === 0
                    ? 'Sin lugares disponibles'
                    : `${option.availableSpots} lugar${option.availableSpots !== 1 ? 'es' : ''} disponible${option.availableSpots !== 1 ? 's' : ''}` }}
                </span>
                <span class="cap-num" :style="{ color: barColor(option) }">
                  {{ option.occupied }}/{{ option.capacity }}
                </span>
              </div>
              <div class="bar-bg" :style="{ background: barBgColor(option) }">
                <div class="bar-fill" :style="{ width: pct(option) + '%', background: barColor(option) }"></div>
              </div>
            </div>
          </button>
        </div>

        <p v-else class="empty-message">
          No hay fechas disponibles para este turno.
        </p>
      </div>

      <div v-if="submitError" class="state-box error submit-error">
        {{ submitError }}
      </div>

      <div class="actions">
        <button
          class="back-btn"
          type="button"
          @click="goBack"
          :disabled="submitting"
        >
          Volver
        </button>

        <button
          class="submit-btn"
          :disabled="!canSubmit || submitting"
          @click="handleSubmit"
          type="button"
        >
          {{ submitting
            ? 'Procesando...'
            : selectedIds.size === 0
              ? 'Inscribirse'
              : `Inscribirse a ${selectedIds.size} clase${selectedIds.size !== 1 ? 's' : ''}` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { turnoService } from '@/services/turnoService'
import { enrollmentService } from '@/services/enrollmentService'

const route = useRoute()
const router = useRouter()

const selectedIds = ref(new Set())
const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const submitError = ref('')
const clases = ref([])

const turnoId = computed(() => String(route.query.turnoId || ''))
const actividad = computed(() => String(route.query.actividad || 'Clase'))
const horaInicio = computed(() => String(route.query.horaInicio || ''))
const horaFin = computed(() => String(route.query.horaFin || ''))
const dias = computed(() => String(route.query.dias || ''))
const sala = computed(() => String(route.query.sala || 'Sin sala'))
const instructor = computed(() => String(route.query.instructor || 'Instructor'))

const availableOptions = computed(() => {
  return clases.value
    .filter((clase) => clase.isActive && (clase.isEnrolled || clase.availableSpots > 0))
    .sort((a, b) => a.rawDate.localeCompare(b.rawDate))
})

const selectedOptions = computed(() =>
  availableOptions.value.filter(o => !o.isEnrolled && selectedIds.value.has(o.id))
)

const canSubmit = computed(() => selectedOptions.value.length > 0)

const formatDate = (value) => {
  if (!value) return ''

  const date = new Date(`${value}T00:00:00`)

  return new Intl.DateTimeFormat('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}

const formatPeriod = (value) => {
  if (!value) return ''
  const date = new Date(`${value}T00:00:00`)
  const mes = new Intl.DateTimeFormat('es-AR', { month: 'long' }).format(date)
  return `${mes.charAt(0).toUpperCase() + mes.slice(1)} ${date.getFullYear()}`
}

const formatDay = (value) => {
  if (!value) return ''

  const date = new Date(`${value}T00:00:00`)
  const day = new Intl.DateTimeFormat('es-AR', {
    weekday: 'long',
  }).format(date)

  return day.charAt(0).toUpperCase() + day.slice(1)
}

const fetchClases = async () => {
  try {
    loading.value = true
    errorMessage.value = ''
    submitError.value = ''

    if (!turnoId.value) {
      errorMessage.value = 'No se recibió un turno válido.'
      return
    }

    const [clasesRes, mySingleRes] = await Promise.all([
      turnoService.getClasesByTurno(turnoId.value),
      enrollmentService.getMySingle(),
    ])

    const now = Date.now()
    const enrolledClaseIds = new Set(
      mySingleRes.data
        .filter((e) =>
          String(e.turno_id) === turnoId.value &&
          (e.status === 'confirmed' || (e.status === 'pending' && e.expires_at && new Date(e.expires_at).getTime() > now))
        )
        .map((e) => e.clase_id)
    )

    const items = Array.isArray(clasesRes.data)
      ? clasesRes.data
      : clasesRes.data.items || []

    clases.value = items.map((clase) => {
      const capacity = clase.capacity ?? 0
      const occupied = clase.enrolled ?? clase.occupied ?? 0

      return {
        id: clase.id,
        rawDate: clase.date,
        displayDate: formatDate(clase.date),
        dayLabel: formatDay(clase.date),
        period: formatPeriod(clase.date),
        capacity,
        occupied,
        availableSpots: Math.max(capacity - occupied, 0),
        isActive: clase.is_active ?? true,
        isEnrolled: enrolledClaseIds.has(clase.id),
      }
    })

  } catch (error) {
    console.error('Error al obtener clases', error)
    errorMessage.value = 'No se pudieron cargar las clases disponibles.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchClases()
})

const pct = (option) => Math.min(Math.round((option.occupied / option.capacity) * 100), 100)

const barColor = (option) => {
  const p = pct(option)
  return p >= 100 ? '#E53935' : p >= 75 ? '#FB8C00' : '#00897B'
}

const barBgColor = (option) => {
  const p = pct(option)
  return p >= 100
    ? 'rgba(229, 57, 53, 0.15)'
    : p >= 75
    ? 'rgba(251, 140, 0, 0.15)'
    : 'rgba(0, 137, 123, 0.15)'
}

function toggleOption(id) {
  submitError.value = ''
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedIds.value = s
}

function goBack() {
  router.back()
}

async function handleSubmit() {
  if (selectedOptions.value.length === 0) return

  submitting.value = true
  submitError.value = ''

  try {
    const clase_ids = selectedOptions.value.map(o => o.id)
    const { data } = await enrollmentService.createSingle(clase_ids)

    const count = selectedOptions.value.length
    const diaLabel = count === 1
      ? `${selectedOptions.value[0].dayLabel} ${selectedOptions.value[0].displayDate}`
      : `${count} clases`

    router.push({
      name: 'ticket',
      query: {
        enrollment_id: data.id,
        actividad:     actividad.value,
        dia:           diaLabel,
        duracion:      `${horaInicio.value} - ${horaFin.value}`,
        instructor:    instructor.value,
        numero:        data.id,
        amount:        data.amount,
        precio_clase:  data.amount,
        expires_at:    data.expires_at,
      },
    })
  } catch (error) {
    if (error.response?.status === 409) {
      const backendMsg = error.response?.data?.errors?.general || error.response?.data?.detail
      const isCapacityError = !backendMsg || backendMsg.includes('cupo') || backendMsg.includes('lugar')
      if (isCapacityError) {
        submitError.value = 'Una de las clases ya no tiene cupo disponible. El lugar se liberará si no se completa el pago.'
      } else {
        submitError.value = backendMsg
      }
    } else if (error.response?.status === 404) {
      submitError.value = 'Una de las clases seleccionadas ya no está disponible.'
    } else {
      submitError.value = 'Ocurrió un error al generar la inscripción.'
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.class-page {
  min-height: 100vh;
  background: linear-gradient(
    135deg,
    #e4f3f0 0%,
    #edf7f5 50%,
    #f4faf8 100%
  );
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  padding-top: 100px;
  font-family:
    'Inter',
    'Segoe UI',
    system-ui,
    sans-serif;
}

.class-card {
  width: 100%;
  max-width: 980px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(14px);
  border-radius: 32px;
  padding: 38px;
  border: 1px solid rgba(0, 137, 123, 0.08);
  box-shadow:
    0 18px 40px rgba(0, 0, 0, 0.06),
    0 6px 18px rgba(0, 0, 0, 0.03);
}

.title {
  margin: 0 0 10px;
  color: #00695c;
  font-size: 2.3rem;
  font-weight: 900;
  letter-spacing: -1px;
}

.subtitle {
  margin: 0 0 30px;
  color: #607d8b;
  font-size: 1rem;
  line-height: 1.6;
  max-width: 620px;
}

.selected-turno-box {
  background: linear-gradient(
    135deg,
    rgba(224, 242, 241, 0.75),
    rgba(255, 255, 255, 0.7)
  );
  border: 1px solid rgba(0, 137, 123, 0.08);
  border-radius: 24px;
  padding: 24px;
  margin-bottom: 32px;
}

.selected-turno-box h2 {
  margin: 0 0 14px;
  color: #1f2937;
  font-size: 1.45rem;
  font-weight: 800;
}

.selected-turno-box p {
  margin: 8px 0;
  color: #455a64;
  font-size: 0.96rem;
  line-height: 1.5;
}

.field-group {
  margin-bottom: 30px;
}

.label {
  display: block;
  margin-bottom: 16px;
  color: #00695c;
  font-size: 1rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.options-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
  gap: 18px;
}

.option-card {
  border: 1px solid rgba(0, 137, 123, 0.08);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(10px);
  padding: 22px;
  text-align: left;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
  box-shadow:
    0 10px 24px rgba(0, 0, 0, 0.04),
    0 2px 6px rgba(0, 0, 0, 0.02);
}

.option-card:hover {
  transform: translateY(-3px);
  border-color: #18b4a3;
  box-shadow:
    0 16px 32px rgba(24, 180, 163, 0.12),
    0 4px 10px rgba(0, 0, 0, 0.03);
}

.option-card.selected {
  border: 2px solid #18b4a3;
  background: rgba(243, 255, 253, 0.9);
  box-shadow:
    0 18px 36px rgba(24, 180, 163, 0.16),
    0 4px 10px rgba(0, 0, 0, 0.03);
}

.option-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 16px;
}

.option-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 800;
  color: #1f2937;
}

.status-badge {
  padding: 7px 12px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.status-badge.available {
  background: rgba(24, 180, 163, 0.14);
  color: #0d9b8a;
}

.status-badge.inscripto {
  background: rgba(0, 137, 123, 0.12);
  color: #00695c;
}

.status-badge.seleccionado {
  background: rgba(17, 166, 145, 0.15);
  color: #00695c;
  font-weight: 800;
}

.option-card.enrolled {
  opacity: 0.75;
  cursor: default;
  border-color: rgba(0, 137, 123, 0.2);
  background: rgba(232, 245, 233, 0.6);
}

.option-card p {
  margin: 7px 0;
  color: #546e7a;
  font-size: 0.93rem;
  line-height: 1.5;
}

.option-card strong {
  color: #37474f;
}

.state-box {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 18px;
  padding: 18px;
  margin-bottom: 22px;
  color: #607d8b;
  border: 1px solid rgba(0, 137, 123, 0.08);
}

.state-box.error {
  color: #d32f2f;
  border-color: #ffcdd2;
  background: #fff5f5;
}

.submit-error {
  margin-top: -8px;
}

.empty-message {
  color: #607d8b;
  margin: 0;
  padding: 20px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 18px;
  border: 1px solid rgba(0, 137, 123, 0.08);
}

.actions {
  display: flex;
  gap: 14px;
  margin-top: 8px;
}

.back-btn,
.submit-btn {
  border: none;
  border-radius: 999px;
  padding: 16px 20px;
  font-size: 1rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  transition:
    transform 0.18s ease,
    background 0.18s ease,
    box-shadow 0.18s ease,
    opacity 0.18s ease;
}

.back-btn {
  width: 180px;
  background: transparent;
  color: #00897b;
  border: 1.5px solid #00897b;
  cursor: pointer;
}

.back-btn:hover:not(:disabled) {
  background: rgba(0, 137, 123, 0.08);
  transform: translateY(-1px);
}

.submit-btn {
  flex: 1;
  background: #00897b;
  color: white;
  cursor: pointer;
  box-shadow: 0 12px 24px rgba(0, 137, 123, 0.22);
}

.submit-btn:hover:not(:disabled) {
  background: #00695c;
  transform: translateY(-1px);
}

.back-btn:disabled,
.submit-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
}

.cupos-section {
  margin-top: 12px;
}

.cap-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.cap-text {
  font-size: 13px;
  font-weight: 500;
}

.cap-num {
  font-size: 13px;
  font-weight: 700;
}

.bar-bg {
  border-radius: 999px;
  height: 7px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.5s ease;
}

@media (max-width: 768px) {
  .class-page {
    padding: 24px 14px;
  }

  .class-card {
    padding: 26px 22px;
    border-radius: 26px;
  }

  .title {
    font-size: 1.9rem;
  }

  .subtitle {
    margin-bottom: 24px;
  }

  .selected-turno-box {
    padding: 20px;
    border-radius: 20px;
  }

  .options-list {
    grid-template-columns: 1fr;
  }

  .option-card {
    padding: 18px;
    border-radius: 20px;
  }

  .option-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .actions {
    flex-direction: column;
  }

  .back-btn,
  .submit-btn {
    width: 100%;
  }
}
</style>