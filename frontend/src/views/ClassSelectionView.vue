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
        <p><strong>Días:</strong> {{ dias }}</p>
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
            :class="{ selected: selectedOptionId === option.id }"
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
          </button>
        </div>

        <p v-else class="empty-message">
          No hay fechas disponibles para este turno.
        </p>
      </div>

      <button
        class="submit-btn"
        :disabled="!canSubmit"
        @click="handleSubmit"
        type="button"
      >
        Inscribirme
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { turnoService } from '@/services/turnoService'

const route = useRoute()
const router = useRouter()

const selectedOptionId = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const clases = ref([])

const turnoId = computed(() => String(route.query.turnoId || ''))
const activityId = computed(() => String(route.query.activityId || ''))
const actividad = computed(() => String(route.query.actividad || 'Clase'))
const horaInicio = computed(() => String(route.query.horaInicio || ''))
const horaFin = computed(() => String(route.query.horaFin || ''))
const dias = computed(() => String(route.query.dias || 'Sin días'))
const sala = computed(() => String(route.query.sala || 'Sin sala'))
const instructor = computed(() => String(route.query.instructor || 'Instructor'))

const availableOptions = computed(() => {
  return clases.value
    .filter((clase) => clase.isActive)
    .sort((a, b) => a.rawDate.localeCompare(b.rawDate))
})

const canSubmit = computed(() => {
  if (!selectedOptionId.value) return false

  const selectedOption = clases.value.find(
    (clase) => String(clase.id) === String(selectedOptionId.value)
  )

  if (!selectedOption) return false

  return selectedOption.availableSpots > 0
})

const fetchClases = async () => {
  try {
    loading.value = true
    errorMessage.value = ''

    const response = await turnoService.getClasesByActividad(activityId.value)

    const items = Array.isArray(response.data) ? response.data : []

    const clasesDelTurno = items.filter(
      (clase) => String(clase.turno_id) === String(turnoId.value)
    )

    clases.value = clasesDelTurno.map((clase) => {
      const capacity = clase.capacity ?? 0
      const occupied = 0

      return {
        id: clase.id,
        rawDate: clase.date,
        displayDate: formatDate(clase.date),
        dayLabel: formatDay(clase.date),
        capacity,
        occupied,
        availableSpots: capacity - occupied,
        isActive: clase.is_active,
      }
    })
  } catch (error) {
    console.error('Error al obtener clases', error)
    errorMessage.value = 'No se pudieron cargar las clases de prueba individual.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (activityId.value && turnoId.value) {
    fetchClases()
  } else {
    errorMessage.value = 'No se recibió un turno válido.'
  }
})

function selectOption(id) {
  selectedOptionId.value = id
}

function handleSubmit() {
  const selectedOption = clases.value.find(
    (clase) => String(clase.id) === String(selectedOptionId.value)
  )

  if (!selectedOption) return
  if (selectedOption.availableSpots <= 0) return

  router.push({
    name: 'ticket',
    query: {
      actividad: actividad.value,
      fecha: selectedOption.rawDate,
      dia: selectedOption.dayLabel,
      hora: `${horaInicio.value} - ${horaFin.value}`,
      instructor: instructor.value,
      sala: sala.value,
      tipo: 'Clase individual',
      claseId: String(selectedOption.id),
      turnoId: turnoId.value,
    },
  })
}

function formatDate(value) {
  const date = new Date(`${value}T00:00:00`)
  return new Intl.DateTimeFormat('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}

function formatDay(value) {
  const date = new Date(`${value}T00:00:00`)
  const day = new Intl.DateTimeFormat('es-AR', {
    weekday: 'long',
  }).format(date)

  return day.charAt(0).toUpperCase() + day.slice(1)
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

.submit-btn {
  width: 100%;
  border: none;
  border-radius: 999px;
  padding: 16px 20px;
  background: #00897b;
  color: white;
  font-size: 1rem;
  font-weight: 800;
  cursor: pointer;
  letter-spacing: 0.02em;
  transition:
    transform 0.18s ease,
    background 0.18s ease,
    box-shadow 0.18s ease;
  box-shadow: 0 12px 24px rgba(0, 137, 123, 0.22);
}
.submit-btn:hover:not(:disabled) {
  background: #00695c;
  transform: translateY(-1px);
}
.submit-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
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
.empty-message {
  color: #607d8b;
  margin: 0;
  padding: 20px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 18px;
  border: 1px solid rgba(0, 137, 123, 0.08);
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
  .submit-btn {
    padding: 15px 18px;
  }
}
</style>