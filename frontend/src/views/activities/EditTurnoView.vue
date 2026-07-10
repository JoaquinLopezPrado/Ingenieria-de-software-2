<script setup lang="ts">
/**
 * EditTurnoView — HU ACT-07.01 v2: Modificar turno
 * --------------------------------------------------
 * Escenarios cubiertos:
 *   1. Modificación exitosa (turno activo, sin inscriptos) → banner verde + redirige
 *   2. Turno duplicado (409) → banner rojo
 *   3. Cupo máximo inválido (≤ 0) → error inline
 *   4. Precio por clase inválido (≤ 0) → error inline
 *   5. Sin días seleccionados → error inline
 *   6. Campo obligatorio vacío → error inline
 *   7. Turno con inscriptos → se permite editar; antes de aplicar se muestra el
 *      impacto (clases a cancelar, créditos a generar, usuarios a notificar) y
 *      se confirma. El backend genera créditos y notifica por email.
 *
 * Guard: solo admin. Turno inactivo → banner informativo + edición permitida.
 * El campo "actividad" nunca puede modificarse.
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import {
  getTurnosAll,
  getFormOptions,
  getSalones,
  updateTurno,
  editTurno,
  previewTurnoUpdate,
  getTurnoDeactivationImpact,
  extractBackendError,
  type Turno,
  type Salon,
  type EditTurnoPayload,
  type UpdateTurnoPreview,
  type TurnoDeactivationImpact,
} from '@/services/sessionService'
import { useAuthStore } from '@/stores/authStore'

// ─── Ruta ─────────────────────────────────────────────────────────────────────

const route     = useRoute()
const router    = useRouter()
const authStore = useAuthStore()
const turnoId   = Number(route.params.id)

// ─── Guard de rol ─────────────────────────────────────────────────────────────

const isAdmin = computed(() => {
  const u = authStore.user
  if (!u) return true
  return u.role === 'admin' || u.roles?.includes('admin') || u.role === 'Administrador'
})

// ─── Constantes estáticas ─────────────────────────────────────────────────────

const daysOfWeek = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']

const DISPLAY_TO_BACKEND: Record<string, string> = {
  'Lunes': 'lunes', 'Martes': 'martes', 'Miércoles': 'miercoles',
  'Jueves': 'jueves', 'Viernes': 'viernes', 'Sábado': 'sabado',
}
const BACKEND_TO_DISPLAY: Record<string, string> = {
  'lunes': 'Lunes', 'martes': 'Martes', 'miercoles': 'Miércoles',
  'jueves': 'Jueves', 'viernes': 'Viernes', 'sabado': 'Sábado',
}

// Slots de 15 minutos: "06:00" … "23:45"
const TIME_SLOTS: string[] = (() => {
  const slots: string[] = []
  for (let h = 6; h <= 23; h++) {
    for (const m of [0, 15, 30, 45]) {
      slots.push(`${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`)
    }
  }
  return slots
})()

/** Normaliza "9:00" → "09:00" para que coincida con los valores de TIME_SLOTS */
function normalizeTime(t: string): string {
  const [h, m] = t.split(':')
  return `${String(Number(h ?? '0')).padStart(2, '0')}:${m ?? '00'}`
}

// ─── Estado ───────────────────────────────────────────────────────────────────

const turno        = ref<Turno | null>(null)
const activityName = ref('')
const availableSalones = ref<Salon[]>([])
const isLoading    = ref(true)
const isSaving     = ref(false)
const isPreviewing = ref(false)
const isActivating = ref(false)
const loadError    = ref('')
const successMsg   = ref('')
const serverError  = ref('')
const authError    = ref<null | 'session' | 'forbidden'>(null)
const inscriptos   = ref(0)

// Confirmación con impacto antes de aplicar
const showConfirm = ref(false)
const preview     = ref<UpdateTurnoPreview | null>(null)

// Baja total del turno (caso 7)
const showDeactivate    = ref(false)
const deactivateImpact  = ref<TurnoDeactivationImpact | null>(null)
const isDeactivating    = ref(false)

// Formulario: mismos campos que SessionForm, sin start_date (no aplica al editar)
const form = ref({
  salon_id:    null as number | null,
  description: '',
  instructor:  '',
  days:        [] as string[],
  startTime:   '',
  endTime:     '',
  maxCapacity: null as number | null,
  class_price: null as number | null,
})

const errors = ref<Record<string, string>>({})

// ─── Computed ─────────────────────────────────────────────────────────────────

const endTimeSlots = computed(() =>
  form.value.startTime
    ? TIME_SLOTS.filter(t => t > form.value.startTime)
    : TIME_SLOTS
)

const selectedSalon = computed(() =>
  availableSalones.value.find(s => s.id === form.value.salon_id) ?? null
)

// ─── Watch ────────────────────────────────────────────────────────────────────

watch(() => form.value.startTime, newStart => {
  if (form.value.endTime && form.value.endTime <= newStart)
    form.value.endTime = ''
})

// Autocompleta el cupo con la capacidad del nuevo salón cuando el admin lo cambia
// a mano (evento nativo, no dispara con la precarga inicial del formulario). El
// admin puede bajarlo después; nunca puede superar la capacidad del salón.
function onSalonChange() {
  if (selectedSalon.value) form.value.maxCapacity = selectedSalon.value.capacity
}

// ─── Carga inicial ────────────────────────────────────────────────────────────

onMounted(async () => {
  if (!isAdmin.value) {
    isLoading.value = false
    return
  }
  try {
    const [turnosRes, { activities }, salones] = await Promise.all([
      getTurnosAll({ page_size: 500 }),
      getFormOptions(),
      getSalones(),
    ])
    availableSalones.value = salones

    const found = turnosRes.items.find(t => t.id === turnoId)
    if (!found) {
      loadError.value = 'No se encontró el turno. Es posible que haya sido eliminado.'
      return
    }

    turno.value        = found
    inscriptos.value   = found.enrolled ?? 0
    activityName.value = activities.find(a => a.id === found.activity_id)?.name
      ?? `Actividad #${found.activity_id}`

    // Pre-cargar el formulario con los valores actuales del turno
    form.value = {
      salon_id:    found.salon_id,
      description: found.description,
      instructor:  found.instructor,
      days:        found.days.map(d => BACKEND_TO_DISPLAY[d] ?? d),
      startTime:   normalizeTime(found.start_time),
      endTime:     normalizeTime(found.end_time),
      maxCapacity: found.capacity,
      class_price: Number(found.class_price) || null,
    }
  } catch (e: unknown) {
    const err = e as { response?: { status?: number }; request?: unknown }
    const status = err?.response?.status
    if (!err.response && err.request) {
      loadError.value = 'No se pudo conectar con el servidor. Verificá que el backend esté corriendo.'
    } else if (status === 401) {
      authError.value = 'session'
    } else if (status === 403) {
      authError.value = 'forbidden'
    } else {
      loadError.value = extractBackendError(e)
    }
  } finally {
    isLoading.value = false
  }
})

// ─── Validación ───────────────────────────────────────────────────────────────

function validate(): boolean {
  errors.value = {}

  if (!form.value.salon_id)
    errors.value.salon = 'Seleccioná un salón.'

  if (!form.value.description.trim())
    errors.value.description = 'Ingresá una descripción para el turno.'

  if (!form.value.instructor.trim())
    errors.value.instructor = 'Ingresá el nombre del instructor.'

  if (form.value.days.length === 0)
    errors.value.days = 'Seleccioná al menos un día de la semana.'

  if (!form.value.startTime)
    errors.value.startTime = 'Seleccioná la hora de inicio.'

  if (!form.value.endTime)
    errors.value.endTime = 'Seleccioná la hora de fin.'

  if (form.value.startTime && form.value.endTime && form.value.startTime >= form.value.endTime)
    errors.value.timeRange = 'La hora de inicio debe ser anterior a la hora de fin.'

  // La capacidad solo afecta a clases futuras nuevas; las existentes conservan su
  // cupo, así que no se valida contra los inscriptos actuales.
  const cap = Number(form.value.maxCapacity)
  if (!form.value.maxCapacity || !Number.isInteger(cap) || cap <= 0)
    errors.value.maxCapacity = 'El cupo máximo debe ser un número entero mayor a 0.'
  else if (selectedSalon.value && cap > selectedSalon.value.capacity)
    errors.value.maxCapacity = `El cupo no puede superar la capacidad del salón (${selectedSalon.value.capacity}).`

  const price = Number(form.value.class_price)
  if (!form.value.class_price || isNaN(price) || price <= 0)
    errors.value.class_price = 'El precio por clase debe ser un número mayor a 0.'

  return Object.keys(errors.value).length === 0
}

// ─── Submit y flujo de guardado ───────────────────────────────────────────────

function buildPayload(): EditTurnoPayload {
  return {
    salon_id:    form.value.salon_id!,
    description: form.value.description.trim(),
    instructor:  form.value.instructor.trim(),
    days:        form.value.days.map(d => DISPLAY_TO_BACKEND[d] ?? d.toLowerCase()),
    start_time:  form.value.startTime,
    end_time:    form.value.endTime,
    capacity:    Number(form.value.maxCapacity),
    class_price: Number(form.value.class_price),
  }
}

function handleApiError(e: unknown) {
  const err = e as { response?: { status?: number } }
  const status = err?.response?.status
  if (status === 401) {
    authError.value = 'session'
  } else if (status === 403) {
    authError.value = 'forbidden'
  } else if (status === 409) {
    serverError.value = extractBackendError(e)
  } else {
    serverError.value = extractBackendError(e)
  }
}

// Paso 1: validar y pedir el impacto al backend antes de aplicar.
async function handleSubmit() {
  serverError.value = ''
  if (!validate()) return

  isPreviewing.value = true
  try {
    const result = await previewTurnoUpdate(turnoId, buildPayload())
    if (result.cupo_insuficiente) {
      // El backend rechazaría este guardado igual; se avisa acá para no abrir
      // un modal de "sin impacto" que después falla al confirmar.
      serverError.value = `No se puede reducir el cupo a ${form.value.maxCapacity}: hay clases futuras con ${result.max_inscriptos_futuros} inscriptos.`
      return
    }
    preview.value = result
    showConfirm.value = true
  } catch (e: unknown) {
    handleApiError(e)
  } finally {
    isPreviewing.value = false
  }
}

// Paso 2: confirmar y aplicar la edición.
async function confirmSave() {
  isSaving.value = true
  serverError.value = ''
  try {
    await editTurno(turnoId, buildPayload())
    showConfirm.value = false
    successMsg.value = 'Turno modificado con éxito.'
    setTimeout(() => router.push({ name: 'turnos-grilla' }), 1500)
  } catch (e: unknown) {
    showConfirm.value = false
    handleApiError(e)
  } finally {
    isSaving.value = false
  }
}

async function activateTurno() {
  if (!turno.value) return
  isActivating.value = true
  serverError.value  = ''
  try {
    await updateTurno(turnoId, { is_active: true })
    turno.value.is_active = true
    successMsg.value = 'Turno activado con éxito.'
    setTimeout(() => router.push({ name: 'turnos-grilla' }), 1500)
  } catch (e: unknown) {
    serverError.value = extractBackendError(e)
  } finally {
    isActivating.value = false
  }
}

// Baja total: pedir impacto y mostrar confirmación.
async function openDeactivate() {
  serverError.value = ''
  isDeactivating.value = true
  try {
    deactivateImpact.value = await getTurnoDeactivationImpact(turnoId)
    showDeactivate.value = true
  } catch (e: unknown) {
    handleApiError(e)
  } finally {
    isDeactivating.value = false
  }
}

async function confirmDeactivate() {
  if (!turno.value) return
  isDeactivating.value = true
  serverError.value = ''
  try {
    await updateTurno(turnoId, { is_active: false })
    showDeactivate.value = false
    successMsg.value = 'Turno dado de baja con éxito.'
    setTimeout(() => router.push({ name: 'turnos-grilla' }), 1500)
  } catch (e: unknown) {
    showDeactivate.value = false
    handleApiError(e)
  } finally {
    isDeactivating.value = false
  }
}
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <!-- ── Encabezado ── -->
      <div class="page-header">
        <div class="header-left">
          <button class="btn-back" @click="router.push({ name: 'turnos-grilla' })">
            ← Volver
          </button>
          <div>
            <p v-if="activityName" class="page-activity">{{ activityName }}</p>
            <h1 class="page-title">Modificar turno</h1>
            <p class="page-subtitle">Editá los campos y guardá los cambios</p>
          </div>
        </div>
      </div>

      <!-- ── Sesión expirada (401) ── -->
      <div v-if="authError === 'session'" class="state-panel state-panel--auth">
        <div class="state-icon">🔒</div>
        <h2 class="state-title">Tu sesión expiró</h2>
        <p class="state-desc">Iniciá sesión nuevamente para continuar.</p>
        <button class="btn-primary" @click="router.push({ name: 'login' })">Iniciar sesión</button>
      </div>

      <!-- ── Sin permisos (403 o no admin) ── -->
      <div v-else-if="authError === 'forbidden' || !isAdmin" class="state-panel state-panel--forbidden">
        <div class="state-icon">⛔</div>
        <h2 class="state-title">Acceso denegado</h2>
        <p class="state-desc">Solo los administradores pueden modificar turnos.</p>
        <button class="btn-secondary" @click="router.push({ name: 'home' })">Volver al inicio</button>
      </div>

      <!-- ── Cargando ── -->
      <div v-else-if="isLoading" class="skeleton-wrapper" aria-label="Cargando turno...">
        <div class="skeleton-header"></div>
        <div class="skeleton-form"></div>
      </div>

      <!-- ── Error de carga ── -->
      <div v-else-if="loadError" class="state-panel state-panel--error">
        <div class="state-icon">⚠</div>
        <h2 class="state-title">No se pudo cargar el turno</h2>
        <p class="state-desc">{{ loadError }}</p>
        <button class="btn-secondary" @click="router.go(0)">Reintentar</button>
      </div>

      <!-- ── Formulario ── -->
      <template v-else-if="turno">

        <!-- Banner turno inactivo -->
        <div v-if="turno && !turno.is_active" class="alert alert-inactive">
          <span class="alert-icon inactive-icon">!</span>
          <span>Este turno está <strong>inactivo</strong> y no es visible para los clientes. Podés editarlo o reactivarlo.</span>
        </div>

        <!-- Banner éxito -->
        <Transition name="fade">
          <div v-if="successMsg" class="alert alert-success" role="status">
            <span class="alert-icon success-icon">✓</span>
            <span>{{ successMsg }}</span>
          </div>
        </Transition>

        <!-- Banner error servidor -->
        <Transition name="fade">
          <div v-if="serverError" class="alert alert-error" role="alert">
            <span class="alert-icon error-icon">!</span>
            <span>{{ serverError }}</span>
            <button class="alert-close" @click="serverError = ''">×</button>
          </div>
        </Transition>

        <div class="form-card">
          <form @submit.prevent="handleSubmit" novalidate>

            <!-- ── Actividad (solo lectura) + Instructor ── -->
            <div class="form-grid-2">

              <div class="input-group">
                <label>Actividad</label>
                <div class="readonly-field">{{ activityName }}</div>
                <p class="field-hint">La actividad no puede modificarse.</p>
              </div>

              <div class="input-group">
                <label>Instructor</label>
                <input
                  type="text"
                  v-model="form.instructor"
                  maxlength="200"
                  placeholder="Nombre del instructor"
                  :class="{ 'input-error': errors.instructor }"
                />
                <span v-if="errors.instructor" class="field-error">{{ errors.instructor }}</span>
              </div>

            </div>

            <!-- ── Salón ── -->
            <div class="input-group">
              <label>Salón</label>
              <select v-model="form.salon_id" @change="onSalonChange" :class="{ 'input-error': errors.salon }">
                <option :value="null" disabled>Seleccioná un salón...</option>
                <option v-for="salon in availableSalones" :key="salon.id" :value="salon.id">
                  {{ salon.name }} (capacidad {{ salon.capacity }})
                </option>
              </select>
              <span v-if="errors.salon" class="field-error">{{ errors.salon }}</span>
            </div>

            <!-- ── Descripción ── -->
            <div class="input-group">
              <label>Descripción del turno</label>
              <input
                type="text"
                v-model="form.description"
                maxlength="200"
                placeholder="Ej: Turno tarde"
                :class="{ 'input-error': errors.description }"
              />
              <span v-if="errors.description" class="field-error">{{ errors.description }}</span>
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

            <!-- ── Horarios y Cupo ── -->
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
                <span v-if="errors.timeRange" class="field-error">{{ errors.timeRange }}</span>
              </div>

              <div class="input-group">
                <label>Cupo máximo</label>
                <input
                  type="number"
                  v-model.number="form.maxCapacity"
                  min="1"
                  :max="selectedSalon?.capacity"
                  step="1"
                  placeholder="Ej: 20"
                  :class="{ 'input-error': errors.maxCapacity }"
                />
                <span v-if="errors.maxCapacity" class="field-error">{{ errors.maxCapacity }}</span>
                <p v-if="selectedSalon" class="field-hint">
                  Capacidad del salón: <strong>{{ selectedSalon.capacity }}</strong>
                </p>
                <p v-if="inscriptos > 0" class="field-hint">
                  Inscriptos actuales: <strong>{{ inscriptos }}</strong> — el cupo no puede ser menor.
                </p>
              </div>

            </div>

            <!-- ── Precio por clase ── -->
            <div class="input-group monto-group">
              <label>Precio por clase</label>
              <input
                type="number"
                v-model.number="form.class_price"
                min="0.01"
                step="0.01"
                placeholder="Ej: 5000"
                :class="{ 'input-error': errors.class_price }"
              />
              <span v-if="errors.class_price" class="field-error">{{ errors.class_price }}</span>
            </div>

            <!-- ── Acciones ── -->
            <div class="form-actions">
              <button
                type="button"
                class="btn-cancel"
                :disabled="isSaving || isActivating"
                @click="router.push({ name: 'turnos-grilla' })"
              >
                Cancelar
              </button>
              <button
                v-if="turno && !turno.is_active"
                type="button"
                class="btn-activate"
                :disabled="isActivating || isSaving"
                @click="activateTurno"
              >
                {{ isActivating ? 'Activando...' : '✓ Activar turno' }}
              </button>
              <button
                v-if="turno && turno.is_active"
                type="button"
                class="btn-danger"
                :disabled="isDeactivating || isSaving || isPreviewing"
                @click="openDeactivate"
              >
                {{ isDeactivating ? 'Calculando...' : 'Dar de baja' }}
              </button>
              <button type="submit" class="btn-submit" :disabled="isSaving || isActivating || isPreviewing || isDeactivating">
                {{ isPreviewing ? 'Calculando...' : 'Guardar cambios' }}
              </button>
            </div>

          </form>
        </div>

      </template>
    </div>

    <!-- ── Modal de confirmación con impacto ── -->
    <Transition name="fade">
      <div v-if="showConfirm && preview" class="modal-overlay" @click.self="showConfirm = false">
        <div class="modal-card" role="dialog" aria-modal="true">
          <h2 class="modal-title">Confirmar cambios</h2>
          <p class="modal-desc">
            Revisá el impacto antes de aplicar. Esta acción genera créditos y
            envía notificaciones por email.
          </p>

          <ul class="impact-list">
            <li v-if="preview.dias_quitados.length">
              <span class="impact-num impact-warn">{{ preview.clases_a_cancelar }}</span>
              clase(s) futura(s) se cancelarán (días quitados:
              {{ preview.dias_quitados.join(', ') }}).
            </li>
            <li v-if="preview.creditos_a_generar">
              <span class="impact-num impact-warn">{{ preview.creditos_a_generar }}</span>
              crédito(s) de clase para {{ preview.clientes_afectados }} cliente(s).
            </li>
            <li v-if="preview.dias_agregados.length">
              <span class="impact-num impact-ok">{{ preview.clases_a_generar }}</span>
              clase(s) nueva(s) se generarán (días agregados:
              {{ preview.dias_agregados.join(', ') }}).
            </li>
            <li v-if="preview.horario_cambia">
              <span class="impact-num impact-ok">⏱</span>
              El nuevo horario se aplicará a las clases futuras.
            </li>
            <li v-if="preview.usuarios_a_notificar">
              <span class="impact-num impact-ok">{{ preview.usuarios_a_notificar }}</span>
              usuario(s) recibirán un email de aviso.
            </li>
            <li v-if="!preview.clases_a_cancelar && !preview.clases_a_generar && !preview.horario_cambia && !preview.usuarios_a_notificar">
              Sin impacto sobre clases ni inscriptos.
            </li>
          </ul>

          <div class="modal-actions">
            <button class="btn-cancel" :disabled="isSaving" @click="showConfirm = false">
              Volver
            </button>
            <button class="btn-submit" :disabled="isSaving" @click="confirmSave">
              {{ isSaving ? 'Aplicando...' : 'Confirmar y aplicar' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ── Modal de baja total del turno (caso 7) ── -->
    <Transition name="fade">
      <div v-if="showDeactivate && deactivateImpact" class="modal-overlay" @click.self="showDeactivate = false">
        <div class="modal-card" role="dialog" aria-modal="true">
          <h2 class="modal-title">Dar de baja el turno</h2>
          <p class="modal-desc">
            El turno dejará de dictarse. Se cancelan todas las clases futuras y
            las suscripciones, generando créditos canjeables en cualquier actividad.
          </p>

          <ul class="impact-list">
            <li>
              <span class="impact-num impact-warn">{{ deactivateImpact.clases_a_cancelar }}</span>
              clase(s) futura(s) se cancelarán.
            </li>
            <li v-if="deactivateImpact.suscripciones_a_baja">
              <span class="impact-num impact-warn">{{ deactivateImpact.suscripciones_a_baja }}</span>
              suscripción(es) se darán de baja.
            </li>
            <li v-if="deactivateImpact.creditos_a_generar">
              <span class="impact-num impact-warn">{{ deactivateImpact.creditos_a_generar }}</span>
              crédito(s) de clase para {{ deactivateImpact.clientes_afectados }} cliente(s).
            </li>
            <li v-if="deactivateImpact.usuarios_a_notificar">
              <span class="impact-num impact-ok">{{ deactivateImpact.usuarios_a_notificar }}</span>
              usuario(s) recibirán un email de aviso.
            </li>
          </ul>

          <div class="modal-actions">
            <button class="btn-cancel" :disabled="isDeactivating" @click="showDeactivate = false">
              Volver
            </button>
            <button class="btn-danger" :disabled="isDeactivating" @click="confirmDeactivate">
              {{ isDeactivating ? 'Aplicando...' : 'Confirmar baja' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

  </AdminLayout>
</template>

<style scoped>
.page-wrapper { width: 100%; }

/* ── Encabezado ── */

.page-header { display: flex; align-items: flex-start; margin-bottom: 1.75rem; }

.header-left { display: flex; align-items: flex-start; gap: 1rem; }

.btn-back {
  margin-top: 4px;
  background: none;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0.4rem 0.9rem;
  font-size: 0.82rem;
  color: #6b7280;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.15s, color 0.15s;
}
.btn-back:hover { background-color: #f3f4f6; color: #374151; }

.page-activity {
  margin: 0 0 0.2rem 0;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: #11998e;
}

.page-title { font-size: 1.5rem; font-weight: 700; color: #1f2937; margin: 0 0 0.2rem 0; }
.page-subtitle { color: #6b7280; font-size: 0.88rem; margin: 0; }

/* ── Paneles de estado ── */

.state-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 4rem 2rem;
  border-radius: 12px;
  text-align: center;
}

.state-panel--auth     { background: #fff5f5; border: 1px solid #fecaca; }
.state-panel--forbidden { background: #fff7ed; border: 1px solid #fed7aa; }
.state-panel--error    { background: #fff5f5; border: 1px solid #fecaca; }
.state-panel--inactive { background: #f9fafb; border: 2px dashed #d1d5db; }

.state-icon { font-size: 2.5rem; line-height: 1; }
.state-title { font-size: 1.05rem; font-weight: 700; margin: 0; color: #991b1b; }
.state-panel--inactive .state-title,
.state-panel--forbidden .state-title { color: #374151; }
.state-desc { font-size: 0.9rem; color: #7f1d1d; margin: 0; max-width: 420px; }
.state-panel--inactive .state-desc,
.state-panel--forbidden .state-desc { color: #6b7280; }

/* ── Skeleton ── */

.skeleton-wrapper { display: flex; flex-direction: column; gap: 1rem; }

.skeleton-header {
  height: 40px; width: 260px; border-radius: 8px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.skeleton-form {
  height: 500px; border-radius: 12px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Alertas ── */

.alert {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.9rem 1.25rem;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 1.25rem;
}

.alert-success  { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
.alert-error    { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.alert-inactive { background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }

.alert-icon {
  width: 1.4rem; height: 1.4rem; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.78rem; font-weight: 700; flex-shrink: 0;
}
.success-icon  { background: #16a34a; color: white; }
.error-icon    { background: #dc2626; color: white; }
.inactive-icon { background: #d97706; color: white; }

.alert-close {
  margin-left: auto; background: none; border: none; font-size: 1.4rem;
  cursor: pointer; color: inherit; opacity: 0.5; transition: opacity 0.15s;
}
.alert-close:hover { opacity: 1; }

/* ── Formulario ── */

.form-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 2rem 2.5rem;
}

.form-grid-2, .form-grid-3 { display: grid; grid-template-columns: 1fr; gap: 0; }

@media (min-width: 640px) {
  .form-grid-2 { grid-template-columns: 1fr 1fr; gap: 1.5rem; }
  .form-grid-3 { grid-template-columns: 1fr 1fr; gap: 1.5rem; }
}
@media (min-width: 1024px) {
  .form-grid-3 { grid-template-columns: 1fr 1fr 1fr; }
}

.input-group { margin-bottom: 1.5rem; }
.monto-group { max-width: 260px; }

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

input:focus, select:focus {
  border-color: #11998e;
  background-color: #fff;
  box-shadow: 0 0 0 3px rgba(17,153,142,0.15);
}

.input-error {
  border-color: #ef4444 !important;
  background-color: #fff5f5 !important;
}

.field-error { display: block; margin-top: 0.35rem; font-size: 0.78rem; color: #dc2626; font-weight: 500; }
.field-hint  { margin: 0.3rem 0 0; font-size: 0.78rem; color: #9ca3af; }

.readonly-field {
  width: 100%;
  padding: 0.7rem 0.9rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #f3f4f6;
  font-size: 0.95rem;
  color: #6b7280;
  box-sizing: border-box;
  font-style: italic;
}

/* ── Pills días ── */

.days-container { display: flex; gap: 0.6rem; flex-wrap: wrap; padding: 0.25rem 0; }
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
  transition: all 0.15s;
  user-select: none;
}
.day-pill:hover { border-color: #11998e; color: #11998e; }
.hidden-checkbox:checked + .day-pill { background-color: #11998e; color: white; border-color: #11998e; }

select:disabled { opacity: 0.55; cursor: not-allowed; }

/* ── Badge período ── */

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
.inscriptos-warn { color: #d97706; font-weight: 600; }

/* ── Acciones ── */

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 1.5rem;
  margin-top: 1rem;
  border-top: 1px solid #f3f4f6;
}

.btn-cancel {
  background: #f3f4f6; color: #374151; font-size: 0.9rem; font-weight: 600;
  padding: 0.7rem 1.5rem; border-radius: 8px; border: 1px solid #d1d5db;
  cursor: pointer; transition: background-color 0.15s;
}
.btn-cancel:hover:not(:disabled) { background: #e5e7eb; }
.btn-cancel:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-submit {
  background: #11998e; color: white; font-weight: 600; font-size: 0.95rem;
  padding: 0.7rem 2rem; border-radius: 8px; border: none; cursor: pointer;
  min-width: 160px; transition: background-color 0.2s, transform 0.1s;
}
.btn-submit:hover:not(:disabled) { background: #0c8a70; }
.btn-submit:active:not(:disabled) { transform: scale(0.98); }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-activate {
  background: #16a34a; color: white; font-weight: 600; font-size: 0.95rem;
  padding: 0.7rem 1.5rem; border-radius: 8px; border: none; cursor: pointer;
  transition: background-color 0.2s;
}
.btn-activate:hover:not(:disabled) { background: #15803d; }
.btn-activate:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-danger {
  background: #fff; color: #dc2626; font-weight: 600; font-size: 0.95rem;
  padding: 0.7rem 1.5rem; border-radius: 8px; border: 1px solid #fecaca; cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}
.btn-danger:hover:not(:disabled) { background: #dc2626; color: white; }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-primary {
  background: #11998e; color: white; font-size: 0.9rem; font-weight: 600;
  padding: 0.65rem 1.75rem; border-radius: 8px; border: none;
  cursor: pointer; transition: background-color 0.15s;
}
.btn-primary:hover { background: #0c8a70; }

.btn-secondary {
  margin-top: 0.25rem; background: #f3f4f6; color: #374151;
  font-size: 0.88rem; font-weight: 600; padding: 0.6rem 1.4rem;
  border-radius: 8px; border: 1px solid #d1d5db; cursor: pointer;
  transition: background-color 0.15s;
}
.btn-secondary:hover { background: #e5e7eb; }

/* ── Modal de confirmación ── */

.modal-overlay {
  position: fixed; inset: 0; z-index: 50;
  background: rgba(17, 24, 39, 0.5);
  display: flex; align-items: center; justify-content: center;
  padding: 1rem;
}

.modal-card {
  background: #fff; border-radius: 14px;
  padding: 1.75rem 2rem; max-width: 460px; width: 100%;
  box-shadow: 0 12px 40px rgba(0,0,0,0.2);
}

.modal-title { font-size: 1.2rem; font-weight: 700; color: #1f2937; margin: 0 0 0.5rem; }
.modal-desc { font-size: 0.88rem; color: #6b7280; margin: 0 0 1.25rem; line-height: 1.5; }

.impact-list {
  list-style: none; padding: 0; margin: 0 0 1.5rem;
  display: flex; flex-direction: column; gap: 0.7rem;
}
.impact-list li {
  display: flex; align-items: center; gap: 0.6rem;
  font-size: 0.9rem; color: #374151; line-height: 1.4;
}

.impact-num {
  flex-shrink: 0; min-width: 1.9rem; height: 1.9rem; padding: 0 0.4rem;
  display: inline-flex; align-items: center; justify-content: center;
  border-radius: 8px; font-weight: 700; font-size: 0.9rem;
}
.impact-warn { background: #fef3c7; color: #92400e; }
.impact-ok   { background: #d1fae5; color: #065f46; }

.modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; }

/* ── Transiciones ── */

.fade-enter-active, .fade-leave-active { transition: opacity 0.25s, transform 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-6px); }

@media (max-width: 480px) {
  .form-card { padding: 1.5rem 1.25rem; }
  .btn-submit, .btn-cancel { width: 100%; }
  .form-actions { flex-direction: column-reverse; }
  .monto-group { max-width: 100%; }
}
</style>
