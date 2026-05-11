<script setup lang="ts">
/**
 * SessionForm
 * -----------
 * Formulario para programar un nuevo turno de actividad (ACT-06.01).
 *
 * Responsabilidades:
 *   - Renderizar todos los campos requeridos (actividad, instructor, días,
 *     horario, salón y cupo máximo).
 *   - Ejecutar las validaciones de negocio en el cliente antes de emitir.
 *   - Emitir el evento "submit-session" con los datos validados para que
 *     la vista padre llame al servicio correspondiente.
 *
 * ┌─ CONEXIÓN CON BACKEND ─────────────────────────────────────────┐
 * │  Las opciones del formulario (actividades, instructores,        │
 * │  salones) hoy vienen del mock en sessionService.ts.            │
 * │  Ver /docs/integracion-backend.md para detalles de migración.  │
 * └────────────────────────────────────────────────────────────────┘
 */
import { ref, onMounted } from 'vue'
import { getFormOptions, type SessionData } from '@/services/sessionService'

defineProps<{
  isLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'submit-session', payload: SessionData): void
}>()

const daysOfWeek = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']

const availableActivities = ref<string[]>([])
const availableInstructors = ref<string[]>([])
const availableRooms = ref<string[]>([])

// Un error por campo — se limpian al volver a enviar
const errors = ref<Record<string, string>>({})

const newSession = ref<SessionData>({
  activity: '',
  instructor: '',
  days: [],
  startTime: '',
  endTime: '',
  maxCapacity: null,
  room: ''
})

onMounted(async () => {
  const options = await getFormOptions()
  availableActivities.value = options.activities
  availableInstructors.value = options.instructors
  availableRooms.value = options.rooms
})

/**
 * Valida todos los campos según las reglas de negocio de ACT-06.01.
 * Retorna true si el formulario es válido, false si hay errores.
 * Los mensajes de error coinciden exactamente con los Criterios de Aceptación.
 */
const validate = (): boolean => {
  errors.value = {}

  if (!newSession.value.activity)
    errors.value.activity = 'Seleccioná una actividad.'

  if (!newSession.value.instructor)
    errors.value.instructor = 'Seleccioná un instructor.'

  if (newSession.value.days.length === 0)
    errors.value.days = 'Seleccioná al menos un día de la semana.'

  if (!newSession.value.startTime)
    errors.value.startTime = 'Ingresá la hora de inicio.'

  if (!newSession.value.endTime)
    errors.value.endTime = 'Ingresá la hora de fin.'

  // Regla de negocio: inicio debe ser anterior a fin (Escenario 2)
  if (newSession.value.startTime && newSession.value.endTime) {
    if (newSession.value.startTime >= newSession.value.endTime)
      errors.value.timeRange = 'La hora de inicio debe ser anterior a la hora de fin.'
  }

  if (!newSession.value.room)
    errors.value.room = 'Seleccioná un salón.'

  // Regla de negocio: cupo debe ser entero > 0 (Escenario 3)
  const cap = newSession.value.maxCapacity
  if (cap === null || !Number.isInteger(Number(cap)) || Number(cap) <= 0)
    errors.value.maxCapacity = 'El cupo máximo debe ser un número entero mayor a 0.'

  return Object.keys(errors.value).length === 0
}

const handleSubmit = () => {
  if (!validate()) return
  emit('submit-session', newSession.value)
}
</script>

<template>
  <div class="form-card">
    <form @submit.prevent="handleSubmit" novalidate>

      <!-- ── Actividad & Instructor ── -->
      <div class="form-grid-2">
        <div class="input-group">
          <label>Actividad</label>
          <select v-model="newSession.activity" :class="{ 'input-error': errors.activity }">
            <option value="" disabled>Seleccioná una actividad...</option>
            <option v-for="act in availableActivities" :key="act" :value="act">{{ act }}</option>
          </select>
          <span v-if="errors.activity" class="field-error">{{ errors.activity }}</span>
        </div>

        <div class="input-group">
          <label>Instructor</label>
          <select v-model="newSession.instructor" :class="{ 'input-error': errors.instructor }">
            <option value="" disabled>Seleccioná un instructor...</option>
            <option v-for="prof in availableInstructors" :key="prof" :value="prof">{{ prof }}</option>
          </select>
          <span v-if="errors.instructor" class="field-error">{{ errors.instructor }}</span>
        </div>
      </div>

      <!-- ── Días de la semana ── -->
      <div class="input-group">
        <label>Días</label>
        <div class="days-container" :class="{ 'days-error': errors.days }">
          <label v-for="day in daysOfWeek" :key="day" class="day-label">
            <input type="checkbox" :value="day" v-model="newSession.days" class="hidden-checkbox" />
            <span class="day-pill">{{ day }}</span>
          </label>
        </div>
        <span v-if="errors.days" class="field-error">{{ errors.days }}</span>
      </div>

      <!-- ── Horarios & Salón ── -->
      <div class="form-grid-3">
        <div class="input-group">
          <label>Hora de inicio</label>
          <input
            type="time"
            v-model="newSession.startTime"
            :class="{ 'input-error': errors.startTime || errors.timeRange }"
          >
          <span v-if="errors.startTime" class="field-error">{{ errors.startTime }}</span>
        </div>

        <div class="input-group">
          <label>Hora de fin</label>
          <input
            type="time"
            v-model="newSession.endTime"
            :class="{ 'input-error': errors.endTime || errors.timeRange }"
          >
          <span v-if="errors.endTime" class="field-error">{{ errors.endTime }}</span>
        </div>

        <div class="input-group">
          <label>Salón</label>
          <select v-model="newSession.room" :class="{ 'input-error': errors.room }">
            <option value="" disabled>Seleccioná un salón...</option>
            <option v-for="room in availableRooms" :key="room" :value="room">{{ room }}</option>
          </select>
          <span v-if="errors.room" class="field-error">{{ errors.room }}</span>
        </div>
      </div>

      <!-- Error de rango horario (cubre ambos campos de hora) -->
      <div v-if="errors.timeRange" class="alert alert-error">
        {{ errors.timeRange }}
      </div>

      <!-- ── Cupo máximo ── -->
      <div class="input-group capacity-group">
        <label>Cupo máximo</label>
        <input
          type="number"
          v-model.number="newSession.maxCapacity"
          min="1"
          step="1"
          placeholder="Ej: 15"
          :class="{ 'input-error': errors.maxCapacity }"
        >
        <span v-if="errors.maxCapacity" class="field-error">{{ errors.maxCapacity }}</span>
      </div>

      <!-- ── Botón de envío ── -->
      <div class="form-actions">
        <button type="submit" :disabled="isLoading" class="btn-submit">
          {{ isLoading ? 'Guardando...' : 'Programar turno' }}
        </button>
      </div>

    </form>
  </div>
</template>

<style scoped>
.form-card {
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 2rem 2.5rem;
  border: 1px solid #f0f0f0;
  width: 100%;
}

/* ── Grillas responsive ── */

.form-grid-2 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
}

.form-grid-3 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
}

/* Tablet: 2 columnas */
@media (min-width: 640px) {
  .form-grid-2 {
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }
  .form-grid-3 {
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }
}

/* Desktop: 3 columnas para la grilla de horarios/salón */
@media (min-width: 1024px) {
  .form-grid-3 {
    grid-template-columns: 1fr 1fr 1fr;
  }
}

/* ── Campos ── */

.input-group {
  margin-bottom: 1.5rem;
}

.capacity-group {
  max-width: 100%;
}

@media (min-width: 640px) {
  .capacity-group {
    max-width: 35%;
  }
}

label {
  display: block;
  font-size: 0.83rem;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 0.45rem;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

input[type="time"],
input[type="number"],
select {
  width: 100%;
  padding: 0.7rem 0.9rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #fafafa;
  font-size: 0.95rem;
  color: #1f2937;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s, background-color 0.2s;
}

input:focus,
select:focus {
  border-color: #11998e;
  background-color: #fff;
  box-shadow: 0 0 0 3px rgba(17, 153, 142, 0.15);
}

.input-error {
  border-color: #ef4444 !important;
  background-color: #fff5f5 !important;
}

.input-error:focus {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15) !important;
}

.field-error {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.78rem;
  color: #dc2626;
  font-weight: 500;
}

/* ── Pills de días ── */

.days-container {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  padding: 0.25rem 0;
}

.days-error .day-pill {
  border-color: #fca5a5;
}

.day-label {
  cursor: pointer;
}

.hidden-checkbox {
  display: none;
}

.day-pill {
  display: inline-block;
  padding: 0.45rem 1rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 500;
  background-color: #f3f4f6;
  color: #6b7280;
  border: 1.5px solid transparent;
  transition: all 0.15s ease;
  user-select: none;
}

.day-pill:hover {
  border-color: #11998e;
  color: #11998e;
}

.hidden-checkbox:checked + .day-pill {
  background-color: #11998e;
  color: white;
  border-color: #11998e;
}

/* ── Alertas inline ── */

.alert {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 500;
  margin-bottom: 1.25rem;
}

.alert-error {
  background-color: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

/* ── Acciones ── */

.form-actions {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #f3f4f6;
  display: flex;
  justify-content: flex-end;
}

.btn-submit {
  background-color: #11998e;
  color: white;
  font-weight: 600;
  font-size: 0.95rem;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  min-width: 160px;
}

.btn-submit:hover:not(:disabled) {
  background-color: #0c8a70;
}

.btn-submit:active:not(:disabled) {
  transform: scale(0.98);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .form-card {
    padding: 1.5rem 1.25rem;
  }
  .btn-submit {
    width: 100%;
  }
  .form-actions {
    justify-content: stretch;
  }
}
</style>
