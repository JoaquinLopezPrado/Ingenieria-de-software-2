<script setup lang="ts">
/**
 * SessionForm — Formulario de programación de turno (ACT-06.01)
 * -------------------------------------------------------------
 * Historial de cambios relevantes:
 *
 *  v1 (mock)        → campos básicos, sin integración real
 *  v2 (integración) → activity_id, description, snake_case, días en minúscula
 *  v3 (actual)      → agrega mes, año e is_active seleccionables por el admin
 *
 * Nota sobre is_active: el frontend lo envía en el payload, pero el backend
 * actualmente lo ignora (CreateTurnoRequest no tiene el campo todavía).
 * El campo quedará operativo en cuanto se agregue al schema.
 * Ver docs/integracion-backend.md 
 */
import { ref, computed, watch, onMounted } from 'vue'
import { getFormOptions, type ActivityOption, type SessionFormData } from '@/services/sessionService'

defineProps<{ isLoading: boolean }>()

const emit = defineEmits<{
  (e: 'submit-session', payload: SessionFormData): void
}>()

// ─── Opciones estáticas ───────────────────────────────────────────────────────

const daysOfWeek = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']

// ─── Slots de horario (06:00 – 23:45, saltos de 15 minutos) ─────────────────
// Genera: ["06:00", "06:15", "06:30", "06:45", "07:00", ..., "23:45"]
const TIME_SLOTS: string[] = (() => {
  const slots: string[] = []
  for (let h = 6; h <= 23; h++) {
    for (const m of [0, 15, 30, 45]) {
      slots.push(`${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`)
    }
  }
  return slots
})()

// ─── Opciones del formulario (actividades) ────────────────────────────────────

const availableActivities = ref<ActivityOption[]>([])
const loadError = ref('')

onMounted(async () => {
  try {
    const options = await getFormOptions()
    availableActivities.value = options.activities
  } catch (e: any) {
    // 401 → no hay sesión activa; 403 → rol insuficiente; otros → backend caído
    const status = e?.response?.status
    if (status === 401 || status === 403) {
      loadError.value = 'Tu sesión expiró o no tenés permisos. Volvé a iniciar sesión.'
    } else {
      loadError.value = 'No se pudieron cargar las actividades. Verificá que el servidor esté corriendo.'
    }
    console.error('[SessionForm] Error al cargar actividades:', e)
  }
})

// ─── Estado del formulario ────────────────────────────────────────────────────

const todayISO = new Date().toISOString().slice(0, 10)

const form = ref({
  activity_id:  null as number | null,
  description:  '',
  instructor:   '',
  days:         [] as string[],
  startTime:    '',   // "HH:MM" — valores de TIME_SLOTS
  endTime:      '',   // "HH:MM" — siempre > startTime gracias a endTimeSlots
  maxCapacity:  null as number | null,
  class_price:  null as number | null,
  start_date:   todayISO,
  is_active:    false,
})

// computed y watch que dependen de `form` — deben ir DESPUÉS de su declaración
// para evitar el error "Cannot access 'form' before initialization" (TDZ).

// El selector de fin solo muestra opciones estrictamente posteriores al inicio.
const endTimeSlots = computed(() =>
  form.value.startTime
    ? TIME_SLOTS.filter(t => t > form.value.startTime)
    : TIME_SLOTS
)

// Si el admin cambia el inicio a una hora igual o posterior al fin ya elegido,
// se resetea el fin para forzar una nueva selección válida.
watch(() => form.value.startTime, (newStart) => {
  if (form.value.endTime && form.value.endTime <= newStart)
    form.value.endTime = ''
})

// Pre-llena el instructor al elegir la actividad; el admin puede editarlo luego
watch(() => form.value.activity_id, (id) => {
  const found = availableActivities.value.find(a => a.id === id)
  if (found) form.value.instructor = found.instructor ?? ''
})

// ─── Validación ───────────────────────────────────────────────────────────────

const errors = ref<Record<string, string>>({})

const validate = (): boolean => {
  errors.value = {}

  if (!form.value.activity_id)
    errors.value.activity = 'Seleccioná una actividad.'

  if (!form.value.instructor?.trim())
    errors.value.instructor = 'Ingresá el nombre del instructor.'

  if (!form.value.description.trim())
    errors.value.description = 'Ingresá una descripción para el turno.'

  if (form.value.days.length === 0)
    errors.value.days = 'Seleccioná al menos un día de la semana.'

  if (!form.value.startTime)
    errors.value.startTime = 'Seleccioná la hora de inicio.'

  if (!form.value.endTime)
    errors.value.endTime = 'Seleccioná la hora de fin.'

  // La validación inicio < fin es casi imposible de violar via UI (endTimeSlots
  // solo muestra opciones posteriores), pero se mantiene como defensa ante
  // ediciones programáticas o tests.
  if (form.value.startTime && form.value.endTime) {
    if (form.value.startTime >= form.value.endTime)
      errors.value.timeRange = 'La hora de inicio debe ser anterior a la hora de fin.'
  }

  const cap = form.value.maxCapacity
  if (cap === null || !Number.isInteger(Number(cap)) || Number(cap) <= 0)
    errors.value.maxCapacity = 'El cupo máximo debe ser un número entero mayor a 0.'

  const class_price = form.value.class_price
  if (class_price === null || isNaN(Number(class_price)) || Number(class_price) <= 0)
    errors.value.class_price = 'El precio por clase debe ser un número mayor a 0.'

  return Object.keys(errors.value).length === 0
}

const handleSubmit = () => {
  if (!validate()) return
  emit('submit-session', {
    activity_id:  form.value.activity_id!,
    description:  form.value.description.trim(),
    instructor:   form.value.instructor?.trim() ?? '',
    days:         form.value.days,
    startTime:    form.value.startTime,
    endTime:      form.value.endTime,
    maxCapacity:  form.value.maxCapacity!,
    class_price:  form.value.class_price!,
    start_date:   form.value.start_date,
    is_active:    form.value.is_active,
  })
}
</script>

<template>
  <div class="form-card">
    <form @submit.prevent="handleSubmit" novalidate>

      <!-- Aviso cuando se usan datos locales por falta del endpoint -->
      <div v-if="loadError" class="alert alert-warning">
        ⚠ {{ loadError }}
      </div>

      <!-- ── Actividad & Instructor ── -->
      <div class="form-grid-2">
        <div class="input-group">
          <label>Actividad</label>
          <select v-model="form.activity_id" :class="{ 'input-error': errors.activity }">
            <option :value="null" disabled>Seleccioná una actividad...</option>
            <option v-for="act in availableActivities" :key="act.id" :value="act.id">
              {{ act.name }}
            </option>
          </select>
          <span v-if="errors.activity" class="field-error">{{ errors.activity }}</span>
        </div>

        <div class="input-group">
          <label>Instructor</label>
          <input
            type="text"
            v-model="form.instructor"
            maxlength="200"
            placeholder="Nombre del instructor"
            :class="{ 'input-error': errors.instructor }"
          >
          <span v-if="errors.instructor" class="field-error">{{ errors.instructor }}</span>
        </div>
      </div>

      <!-- ── Descripción ── -->
      <div class="input-group">
        <label>Descripción del turno</label>
        <input
          type="text"
          v-model="form.description"
          maxlength="200"
          placeholder="Ej: Turno mañana, Turno tarde avanzado..."
          :class="{ 'input-error': errors.description }"
        >
        <span v-if="errors.description" class="field-error">{{ errors.description }}</span>
      </div>

      <!-- ── Fecha de inicio ── -->
      <div class="input-group">
        <label>Fecha de inicio</label>
        <input type="date" v-model="form.start_date" :class="{ 'input-error': errors.start_date }" />
        <span v-if="errors.start_date" class="field-error">{{ errors.start_date }}</span>
      </div>

      <!-- ── Días de la semana ── -->
      <div class="input-group">
        <label>Días</label>
        <div class="days-container" :class="{ 'days-error': errors.days }">
          <label v-for="day in daysOfWeek" :key="day" class="day-label">
            <input type="checkbox" :value="day" v-model="form.days" class="hidden-checkbox" />
            <span class="day-pill">{{ day }}</span>
          </label>
        </div>
        <span v-if="errors.days" class="field-error">{{ errors.days }}</span>
      </div>

      <!-- ── Horarios & Cupo ── -->
      <div class="form-grid-3">
        <div class="input-group">
          <label>Hora de inicio</label>
          <select
            v-model="form.startTime"
            :class="{ 'input-error': errors.startTime || errors.timeRange }"
          >
            <option value="" disabled>Seleccioná hora...</option>
            <option v-for="t in TIME_SLOTS" :key="t" :value="t">{{ t }}</option>
          </select>
          <span v-if="errors.startTime" class="field-error">{{ errors.startTime }}</span>
        </div>

        <div class="input-group">
          <label>Hora de fin</label>
          <!-- endTimeSlots solo incluye opciones posteriores al inicio elegido -->
          <select
            v-model="form.endTime"
            :class="{ 'input-error': errors.endTime || errors.timeRange }"
            :disabled="!form.startTime"
          >
            <option value="" disabled>
              {{ form.startTime ? 'Seleccioná hora...' : 'Elegí primero la hora de inicio' }}
            </option>
            <option v-for="t in endTimeSlots" :key="t" :value="t">{{ t }}</option>
          </select>
          <span v-if="errors.endTime" class="field-error">{{ errors.endTime }}</span>
        </div>

        <div class="input-group">
          <label>Cupo máximo</label>
          <input
            type="number"
            v-model.number="form.maxCapacity"
            min="1"
            step="1"
            placeholder="Ej: 15"
            :class="{ 'input-error': errors.maxCapacity }"
          >
          <span v-if="errors.maxCapacity" class="field-error">{{ errors.maxCapacity }}</span>
        </div>
      </div>

      <!-- Precio por clase -->
      <div class="input-group">
        <label>Precio por clase</label>
        <input
          type="number"
          v-model.number="form.class_price"
          min="0.01"
          step="0.01"
          placeholder="Ej: 150.00"
          :class="{ 'input-error': errors.class_price }"
        >
        <span v-if="errors.class_price" class="field-error">{{ errors.class_price }}</span>
      </div>

      <!-- Error rango horario -->
      <div v-if="errors.timeRange" class="alert alert-error">
        {{ errors.timeRange }}
      </div>

      <!-- ── Estado del turno (is_active) ── -->
      <div class="status-section">
        <div class="status-header">
          <span class="status-label-text">Estado del turno</span>
          <span class="status-hint">
            Los turnos se crean inactivos. Activalo cuando confirmes que se dictará.
          </span>
        </div>

        <label class="toggle-row">
          <div class="toggle-wrapper">
            <input type="checkbox" v-model="form.is_active" class="toggle-input" />
            <span class="toggle-track">
              <span class="toggle-thumb"></span>
            </span>
          </div>
          <div class="toggle-labels">
            <span class="toggle-state" :class="form.is_active ? 'active' : 'inactive'">
              {{ form.is_active ? 'Activo' : 'Inactivo' }}
            </span>
            <span class="toggle-description">
              {{ form.is_active
                ? 'El turno estará visible y disponible para reservas.'
                : 'El turno se guardará pero no será visible para los socios.' }}
            </span>
          </div>
        </label>

        
      </div>

      <!-- ── Resumen ── -->
      <div class="period-badge">
        <span>📅</span>
        <span>
          Inicio:
          <strong>{{ form.start_date || '—' }}</strong>
          —
          <span :class="form.is_active ? 'badge-active' : 'badge-inactive'">
            {{ form.is_active ? 'Activo al guardar' : 'Inactivo al guardar' }}
          </span>
        </span>
      </div>

      <!-- ── Acciones ── -->
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

.form-grid-2,
.form-grid-3 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
}

@media (min-width: 640px) {
  .form-grid-2 { grid-template-columns: 1fr 1fr; gap: 1.5rem; }
  .form-grid-3 { grid-template-columns: 1fr 1fr; gap: 1.5rem; }
}

@media (min-width: 1024px) {
  .form-grid-3 { grid-template-columns: 1fr 1fr 1fr; }
}

/* ── Campos base ── */

.input-group { margin-bottom: 1.5rem; }

label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 0.45rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

input[type="text"],
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

/* ── Solo lectura ── */

.readonly-field {
  width: 100%;
  padding: 0.7rem 0.9rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #f3f4f6;
  font-size: 0.95rem;
  color: #1f2937;
  box-sizing: border-box;
  min-height: 2.6rem;
}

.readonly-field.placeholder {
  color: #9ca3af;
  font-style: italic;
}

/* ── Pills de días ── */

.days-container {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  padding: 0.25rem 0;
}

.days-error .day-pill { border-color: #fca5a5; }

.day-label { cursor: pointer; }
.hidden-checkbox { display: none; }

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

.day-pill:hover { border-color: #11998e; color: #11998e; }

.hidden-checkbox:checked + .day-pill {
  background-color: #11998e;
  color: white;
  border-color: #11998e;
}

/* ── Alerta rango ── */

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

.alert-warning {
  background-color: #fffbeb;
  color: #92400e;
  border: 1px solid #fde68a;
}

/* ── Sección de estado (is_active) ── */

.status-section {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
  background-color: #fafafa;
}

.status-header {
  margin-bottom: 1rem;
}

.status-label-text {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #4b5563;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.2rem;
}

.status-hint {
  font-size: 0.8rem;
  color: #9ca3af;
}

/* Toggle switch */
.toggle-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  cursor: pointer;
  text-transform: none;
  letter-spacing: normal;
  font-weight: normal;
  color: inherit;
  margin-bottom: 0;
}

.toggle-wrapper { flex-shrink: 0; padding-top: 2px; }

.toggle-input { display: none; }

.toggle-track {
  display: block;
  width: 44px;
  height: 24px;
  border-radius: 999px;
  background-color: #d1d5db;
  position: relative;
  transition: background-color 0.2s;
}

.toggle-input:checked + .toggle-track {
  background-color: #11998e;
}

.toggle-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  transition: transform 0.2s;
}

.toggle-input:checked + .toggle-track .toggle-thumb {
  transform: translateX(20px);
}

.toggle-labels { display: flex; flex-direction: column; gap: 0.15rem; }

.toggle-state {
  font-size: 0.9rem;
  font-weight: 600;
}

.toggle-state.active  { color: #0c8a70; }
.toggle-state.inactive { color: #6b7280; }

.toggle-description {
  font-size: 0.82rem;
  color: #9ca3af;
}

.pending-note {
  margin: 0.75rem 0 0 0;
  font-size: 0.75rem;
  color: #b45309;
  background-color: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 6px;
  padding: 0.4rem 0.75rem;
}

/* ── Badge de período ── */

.period-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  border-radius: 8px;
  padding: 0.6rem 1rem;
  font-size: 0.85rem;
  margin-bottom: 1.5rem;
}

.badge-active   { color: #0c8a70; font-weight: 600; }
.badge-inactive { color: #6b7280; font-weight: 600; }

/* ── Acciones ── */

.form-actions {
  margin-top: 1.5rem;
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

.btn-submit:hover:not(:disabled)  { background-color: #0c8a70; }
.btn-submit:active:not(:disabled) { transform: scale(0.98); }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }

@media (max-width: 480px) {
  .form-card { padding: 1.5rem 1.25rem; }
  .btn-submit { width: 100%; }
  .form-actions { justify-content: stretch; }
}

/* El select de hora de fin muestra un cursor "no permitido" cuando está deshabilitado
   (mientras no se haya elegido hora de inicio). */
select:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>
