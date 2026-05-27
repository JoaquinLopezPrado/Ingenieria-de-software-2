<template>
  <div class="class-page">
    <div class="class-card">
      <h1 class="title">Clase individual</h1>
      <p class="subtitle">
        Elegí una fecha disponible para tu clase individual del turno seleccionado.
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

      <div v-else-if="hasActiveSingleEnrollment" class="state-box error">
        Ya tenés una clase de prueba reservada. Solo podés tener una activa a la vez.
      </div>

      <div v-else class="field-group">
        <label class="label">Opciones disponibles</label>

        <div v-if="availableOptions.length > 0" class="options-list">
          <button
            v-for="option in availableOptions"
            :key="option.id"
            class="option-card"
            :class="{ selected: String(selectedOptionId) === String(option.id) }"
            @click="selectOption(option.id)"
            type="button"
          >
            <div class="option-header">
              <h3>{{ option.displayDate }}</h3>

              <span class="status-badge available">
                Disponible
              </span>
            </div>

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
          {{ submitting ? 'Procesando...' : 'Continuar al ticket' }}
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

const selectedOptionId = ref(null)
const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const submitError = ref('')
const clases = ref([])
const hasActiveSingleEnrollment = ref(false)

const turnoId = computed(() => String(route.query.turnoId || ''))
const actividad = computed(() => String(route.query.actividad || 'Clase'))
const horaInicio = computed(() => String(route.query.horaInicio || ''))
const horaFin = computed(() => String(route.query.horaFin || ''))
const dias = computed(() => String(route.query.dias || ''))
const sala = computed(() => String(route.query.sala || 'Sin sala'))
const instructor = computed(() => String(route.query.instructor || 'Instructor'))

const availableOptions = computed(() => {
  return clases.value
    .filter((clase) => clase.isActive && clase.availableSpots > 0)
    .sort((a, b) => a.rawDate.localeCompare(b.rawDate))
})

const selectedOption = computed(() => {
  return clases.value.find(
    (clase) => String(clase.id) === String(selectedOptionId.value),
  ) || null
})

const canSubmit = computed(() => {
  return !!selectedOption.value && selectedOption.value.availableSpots > 0
})

const formatDate = (value) => {
  if (!value) return ''

  const date = new Date(`${value}T00:00:00`)

  return new Intl.DateTimeFormat('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
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
        capacity,
        occupied,
        availableSpots: Math.max(capacity - occupied, 0),
        isActive: clase.is_active ?? true,
      }
    })

    hasActiveSingleEnrollment.value = mySingleRes.data
      .some((e) =>
        (e.status === 'confirmed' || e.status === 'pending') &&
        String(e.turno_id) === turnoId.value
      )
  } catch (error) {
    console.error('Error al obtener clases', error)
    errorMessage.value = 'No se pudieron cargar las clases de prueba individual.'
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

function selectOption(id) {
  selectedOptionId.value = id
  submitError.value = ''
}

function goBack() {
  router.back()
}

async function handleSubmit() {
  if (!selectedOption.value) return
  if (selectedOption.value.availableSpots <= 0) return

  try {
    submitting.value = true
    submitError.value = ''

    const { data } = await enrollmentService.createSingle(selectedOption.value.id)

    router.push({
      name: 'ticket',
      query: {
        enrollment_id: data.id,
        actividad: actividad.value,
        dia: `${selectedOption.value.dayLabel} ${selectedOption.value.displayDate}`,
        hora: `${horaInicio.value} - ${horaFin.value}`,
        instructor: instructor.value,
        numero: data.id,
        amount: data.amount,
      },
    })
  } catch (error) {
    console.error('Error al crear inscripción individual', error)

    const detail = error.response?.data?.errors?.general

    if (error.response?.status === 409) {
      submitError.value = detail ?? 'La clase ya no tiene lugares disponibles.'
    } else if (error.response?.status === 404) {
      submitError.value = 'La clase seleccionada no está disponible.'
    } else {
      submitError.value = 'Ocurrió un error al generar la inscripción individual.'
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