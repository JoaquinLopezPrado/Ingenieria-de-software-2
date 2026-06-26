<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import {
  getClasesByTurnoAdmin,
  getCancelPreview,
  cancelClase,
  updateClaseHorario,
  extractBackendError,
  type ClaseDetalle,
  type CancelPreviewAlumno,
  type CancelPreviewResponse,
} from '@/services/sessionService'

const route   = useRoute()
const router  = useRouter()
const turnoId = Number(route.params.id)

const actividadNombre = computed(() => String(route.query.actividad  ?? `Turno #${turnoId}`))
const horarioLabel    = computed(() => String(route.query.horario    ?? ''))
const diasLabel       = computed(() => String(route.query.dias       ?? ''))
const descripcionLabel = computed(() => String(route.query.descripcion ?? ''))
const instructorLabel  = computed(() => String(route.query.instructor  ?? ''))

// ─── Datos ───────────────────────────────────────────────────────────────────

const clases    = ref<ClaseDetalle[]>([])
const isLoading = ref(true)
const error     = ref('')

// ─── Semana ───────────────────────────────────────────────────────────────────

const DAY_NAMES = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

function getMonday(d: Date): Date {
  const date = new Date(d)
  const day  = date.getDay()
  date.setDate(date.getDate() + (day === 0 ? -6 : 1 - day))
  date.setHours(0, 0, 0, 0)
  return date
}

function isoDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const today      = isoDate(new Date())
const weekStart  = ref<Date>(getMonday(new Date()))

const weekDays = computed(() =>
  Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart.value)
    d.setDate(d.getDate() + i)
    return d
  })
)

const weekLabel = computed(() => {
  const from = weekDays.value[0]!
  const to   = weekDays.value[6]!
  const opts: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' }
  return `${from.toLocaleDateString('es-AR', opts)} – ${to.toLocaleDateString('es-AR', opts)} ${to.getFullYear()}`
})

function prevWeek() {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() - 7)
  weekStart.value = d
}

function nextWeek() {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() + 7)
  weekStart.value = d
}

function goToToday() {
  weekStart.value = getMonday(new Date())
}

const isCurrentWeek = computed(() => isoDate(weekStart.value) === isoDate(getMonday(new Date())))

function onDatePick(e: Event) {
  const val = (e.target as HTMLInputElement).value
  if (val) weekStart.value = getMonday(new Date(val + 'T12:00:00'))
}

// ─── Clases por día ──────────────────────────────────────────────────────────

function clasesDelDia(day: Date): ClaseDetalle[] {
  const iso = isoDate(day)
  return clases.value.filter(c => c.date === iso)
}

// ─── Estado ───────────────────────────────────────────────────────────────────

type ClaseStatus = 'cancelada' | 'finalizada' | 'hoy' | 'programada'

function claseStatus(c: ClaseDetalle): ClaseStatus {
  if (c.cancelled_at)   return 'cancelada'
  if (c.date < today)   return 'finalizada'
  if (c.date === today) return 'hoy'
  return 'programada'
}

const STATUS_LABEL: Record<ClaseStatus, string> = {
  cancelada:  'Cancelada',
  finalizada: 'Finalizada',
  hoy:        'Hoy',
  programada: 'Programada',
}

// ─── Cupo ────────────────────────────────────────────────────────────────────

function cupoClass(c: ClaseDetalle): string {
  if (c.capacity === 0) return 'cupo-libre'
  if (c.enrolled >= c.capacity) return 'cupo-completo'
  const pct = c.enrolled / c.capacity
  if (pct >= 0.70) return 'cupo-alto'
  return 'cupo-libre'
}

// ─── Indicador asistencia ────────────────────────────────────────────────────

function asistenciaBadgeClass(c: ClaseDetalle): string {
  if (c.presentes_count === 0)                return 'asist-vacia'
  if (c.presentes_count < c.enrolled)         return 'asist-parcial'
  return 'asist-completa'
}

// ─── Modal cancelar ───────────────────────────────────────────────────────────

const claseAConfirmar   = ref<ClaseDetalle | null>(null)
const previewData       = ref<CancelPreviewResponse | null>(null)
const previewLoading    = ref(false)
const previewError      = ref('')
const motivo            = ref('')
const cancelando        = ref(false)
const cancelError       = ref('')
const toastMsg          = ref('')

const TIPO_LABEL: Record<CancelPreviewAlumno['tipo'], string> = {
  suscripcion:          'Descuento en próximo cobro',
  individual_completo:  'Crédito 30 días',
  individual_senia:     'Reembolso de seña',
}

async function abrirModalCancelar(c: ClaseDetalle) {
  claseAConfirmar.value = c
  previewData.value     = null
  previewError.value    = ''
  motivo.value          = ''
  cancelError.value     = ''
  previewLoading.value  = true
  try {
    previewData.value = await getCancelPreview(c.id)
  } catch (e) {
    previewError.value = extractBackendError(e)
  } finally {
    previewLoading.value = false
  }
}

function cerrarModalCancelar() {
  claseAConfirmar.value = null
  previewData.value     = null
}

async function confirmarCancelacion() {
  if (!claseAConfirmar.value || !motivo.value.trim()) return
  cancelando.value  = true
  cancelError.value = ''
  try {
    await cancelClase(claseAConfirmar.value.id, motivo.value.trim())
    clases.value = await getClasesByTurnoAdmin(turnoId)
    toastMsg.value = 'Clase cancelada. Los alumnos fueron notificados por email.'
    setTimeout(() => { toastMsg.value = '' }, 5000)
    cerrarModalCancelar()
  } catch (e) {
    cancelError.value = extractBackendError(e)
  } finally {
    cancelando.value = false
  }
}

// ─── Modal editar horario ──────────────────────────────────────────────────────

const claseAEditar  = ref<ClaseDetalle | null>(null)
const editFecha     = ref('')
const editInicio    = ref('')
const editFin       = ref('')
const editCupo      = ref(0)
const guardando     = ref(false)
const editError     = ref('')

// El input time exige "HH:MM"; el backend devuelve "H:MM" (ej "9:30").
function toInputTime(t: string): string {
  const [h, m] = t.split(':')
  return `${(h ?? '0').padStart(2, '0')}:${m ?? '00'}`
}

function abrirModalEditar(c: ClaseDetalle) {
  claseAEditar.value = c
  editFecha.value    = c.date
  editInicio.value   = toInputTime(c.start_time)
  editFin.value      = toInputTime(c.end_time)
  editCupo.value     = c.capacity
  editError.value    = ''
}

function cerrarModalEditar() {
  claseAEditar.value = null
}

// El cupo nunca puede quedar por debajo de los ya inscriptos (ni en 0/negativo).
const cupoMinimo = computed(() => Math.max(1, claseAEditar.value?.enrolled ?? 1))

const edicionValida = computed(() =>
  !!editFecha.value &&
  !!editInicio.value &&
  !!editFin.value &&
  editFin.value > editInicio.value &&
  editCupo.value >= cupoMinimo.value &&
  editFecha.value >= today
)

async function confirmarEdicion() {
  if (!claseAEditar.value || !edicionValida.value) return
  guardando.value = true
  editError.value = ''
  try {
    await updateClaseHorario(claseAEditar.value.id, {
      date:       editFecha.value,
      start_time: editInicio.value,
      end_time:   editFin.value,
      capacity:   editCupo.value,
    })
    clases.value = await getClasesByTurnoAdmin(turnoId)
    toastMsg.value = 'Horario actualizado. Los alumnos fueron notificados por email.'
    setTimeout(() => { toastMsg.value = '' }, 5000)
    cerrarModalEditar()
  } catch (e) {
    editError.value = extractBackendError(e)
  } finally {
    guardando.value = false
  }
}

// ─── Carga ────────────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    clases.value = await getClasesByTurnoAdmin(turnoId)
  } catch {
    error.value = 'No se pudieron cargar las clases del turno.'
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <!-- Encabezado -->
      <div class="page-header">
        <div class="header-left">
          <button class="btn-back" type="button" @click="router.push({ name: 'turnos-grilla' })">
            ← Volver
          </button>
          <div>
            <h1 class="page-title">{{ actividadNombre }}</h1>
            <p v-if="descripcionLabel || instructorLabel" class="page-desc">
              <span v-if="descripcionLabel">{{ descripcionLabel }}</span>
              <span v-if="descripcionLabel && instructorLabel"> · </span>
              <span v-if="instructorLabel">{{ instructorLabel }}</span>
            </p>
            <p v-if="diasLabel || horarioLabel" class="page-subtitle">
              {{ diasLabel }}<span v-if="diasLabel && horarioLabel"> · </span>{{ horarioLabel }}
            </p>
          </div>
        </div>
      </div>

      <!-- Navegación semanal -->
      <div class="week-nav">
        <button class="week-btn" type="button" @click="prevWeek" aria-label="Semana anterior">←</button>
        <span class="week-label">{{ weekLabel }}</span>
        <button class="week-btn" type="button" @click="nextWeek" aria-label="Semana siguiente">→</button>
        <button
          v-if="!isCurrentWeek"
          class="week-btn today-btn"
          type="button"
          @click="goToToday"
        >Hoy</button>
        <input
          type="date"
          class="week-picker"
          :value="isoDate(weekStart)"
          title="Ir a semana"
          @change="onDatePick"
        />
      </div>

      <!-- Skeleton -->
      <div v-if="isLoading" class="skeleton-grid">
        <div v-for="n in 7" :key="n" class="skeleton-col"></div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="state-card">
        <div class="state-icon">⚠</div>
        <p class="state-desc">{{ error }}</p>
        <button class="btn-secondary" type="button" @click="router.go(0)">Reintentar</button>
      </div>

      <!-- Calendario -->
      <div v-else class="calendar-grid">
        <div
          v-for="(day, idx) in weekDays"
          :key="isoDate(day)"
          :class="['day-column', { 'day-today': isoDate(day) === today }]"
        >
          <div class="day-header">
            <span class="day-name">{{ DAY_NAMES[idx] }}</span>
            <span class="day-date">{{ day.getDate() }}/{{ String(day.getMonth() + 1).padStart(2, '0') }}</span>
          </div>

          <div class="day-body">
            <p v-if="clasesDelDia(day).length === 0" class="empty-day">Sin clases</p>

            <div
              v-for="clase in clasesDelDia(day)"
              :key="clase.id"
              :class="['clase-card', `card-${claseStatus(clase)}`]"
            >
              <div class="cupo-bar-wrapper">
                <span :class="['cupo-label', cupoClass(clase)]">
                  {{ clase.enrolled >= clase.capacity ? 'COMPLETO' : `Cupo: ${clase.enrolled}/${clase.capacity}` }}
                </span>
                <div class="cupo-bar-track">
                  <div
                    class="cupo-bar-fill"
                    :class="cupoClass(clase)"
                    :style="{ width: `${Math.min(clase.capacity > 0 ? (clase.enrolled / clase.capacity) * 100 : 0, 100)}%` }"
                  ></div>
                </div>
              </div>
              <span
                v-if="claseStatus(clase) !== 'hoy'"
                :class="['status-badge', `badge-${claseStatus(clase)}`]"
              >
                {{ STATUS_LABEL[claseStatus(clase)] }}
              </span>
              <div
                v-if="(claseStatus(clase) === 'finalizada' || claseStatus(clase) === 'hoy') && clase.enrolled > 0"
                class="cupo-bar-wrapper"
              >
                <span :class="['cupo-label', asistenciaBadgeClass(clase)]">
                  Asist.: {{ clase.presentes_count }}/{{ clase.enrolled }}
                </span>
                <div class="cupo-bar-track">
                  <div
                    class="cupo-bar-fill"
                    :class="asistenciaBadgeClass(clase)"
                    :style="{ width: `${clase.enrolled > 0 ? (clase.presentes_count / clase.enrolled) * 100 : 0}%` }"
                  ></div>
                </div>
              </div>
              <p v-if="clase.cancelled_reason" class="cancelada-motivo">
                {{ clase.cancelled_reason }}
              </p>
              <div class="clase-actions">
                <RouterLink
                  v-if="claseStatus(clase) !== 'cancelada'"
                  :to="{
                    name: 'clase-asistencias',
                    params: { claseId: clase.id },
                    query: {
                      actividad: actividadNombre,
                      descripcion: descripcionLabel,
                      instructor: instructorLabel,
                      fecha: clase.date,
                      horario: `${clase.start_time} – ${clase.end_time}`,
                    }
                  }"
                  class="btn-action btn-ver"
                >
                  Ver inscriptos
                </RouterLink>
                <button
                  v-if="claseStatus(clase) === 'programada' || claseStatus(clase) === 'hoy'"
                  type="button"
                  class="btn-action btn-editar"
                  @click="abrirModalEditar(clase)"
                >
                  Editar clase
                </button>
                <button
                  v-if="claseStatus(clase) === 'programada' || claseStatus(clase) === 'hoy'"
                  type="button"
                  class="btn-action btn-cancelar"
                  @click="abrirModalCancelar(clase)"
                >
                  Cancelar clase
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- Toast -->
    <Teleport to="body">
      <div v-if="toastMsg" class="toast-success">{{ toastMsg }}</div>
    </Teleport>

    <!-- Modal cancelar -->
    <Teleport to="body">
      <div v-if="claseAConfirmar" class="modal-overlay" @click.self="cerrarModalCancelar">
        <div class="modal-box" role="dialog" aria-modal="true">
          <h2 class="modal-title">Cancelar clase</h2>
          <p class="modal-subtitle">
            {{ claseAConfirmar.date }} · {{ claseAConfirmar.start_time }} – {{ claseAConfirmar.end_time }}
          </p>

          <!-- Cargando preview -->
          <div v-if="previewLoading" class="modal-loading">Cargando alumnos afectados…</div>

          <!-- Error en preview -->
          <div v-else-if="previewError" class="modal-error">{{ previewError }}</div>

          <!-- Preview cargado -->
          <template v-else-if="previewData">
            <div v-if="previewData.total_afectados === 0" class="modal-empty">
              No hay alumnos inscriptos en esta clase.
            </div>
            <div v-else class="afectados-list">
              <p class="afectados-header">
                {{ previewData.total_afectados }} alumno{{ previewData.total_afectados !== 1 ? 's' : '' }} afectado{{ previewData.total_afectados !== 1 ? 's' : '' }}:
              </p>
              <div
                v-for="a in previewData.afectados"
                :key="a.user_id"
                class="afectado-item"
              >
                <span class="afectado-name">{{ a.full_name }}</span>
                <span class="afectado-tipo">{{ TIPO_LABEL[a.tipo] }}</span>
              </div>
            </div>

            <div class="motivo-field">
              <label class="motivo-label">Motivo de cancelación <span class="required">*</span></label>
              <textarea
                v-model="motivo"
                class="motivo-textarea"
                placeholder="Ej: fuerza mayor, problema con el local, etc."
                rows="3"
              />
            </div>

            <p v-if="cancelError" class="modal-error">{{ cancelError }}</p>

            <div class="modal-actions">
              <button type="button" class="modal-btn-cancel" :disabled="cancelando" @click="cerrarModalCancelar">
                Volver
              </button>
              <button
                type="button"
                class="modal-btn-confirm"
                :disabled="!motivo.trim() || cancelando"
                @click="confirmarCancelacion"
              >
                {{ cancelando ? 'Cancelando…' : 'Confirmar cancelación' }}
              </button>
            </div>
          </template>
        </div>
      </div>
    </Teleport>

    <!-- Modal editar horario -->
    <Teleport to="body">
      <div v-if="claseAEditar" class="modal-overlay" @click.self="cerrarModalEditar">
        <div class="modal-box" role="dialog" aria-modal="true">
          <h2 class="modal-title">Editar clase</h2>
          <p class="modal-subtitle">
            Solo se modifica esta clase. El resto del turno no cambia.
          </p>

          <div class="edit-field">
            <label class="motivo-label">Fecha <span class="required">*</span></label>
            <input v-model="editFecha" type="date" :min="today" class="edit-input" />
          </div>

          <div class="edit-row">
            <div class="edit-field">
              <label class="motivo-label">Inicio <span class="required">*</span></label>
              <input v-model="editInicio" type="time" class="edit-input" />
            </div>
            <div class="edit-field">
              <label class="motivo-label">Fin <span class="required">*</span></label>
              <input v-model="editFin" type="time" class="edit-input" />
            </div>
          </div>

          <div class="edit-field">
            <label class="motivo-label">Cupo <span class="required">*</span></label>
            <input v-model.number="editCupo" type="number" :min="cupoMinimo" class="edit-input" />
            <p v-if="claseAEditar && claseAEditar.enrolled > 0" class="edit-hint">
              {{ claseAEditar.enrolled }} inscripto{{ claseAEditar.enrolled !== 1 ? 's' : '' }} en esta clase.
            </p>
          </div>

          <p
            v-if="editFin && editInicio && editFin <= editInicio"
            class="modal-error"
          >La hora de fin debe ser posterior a la de inicio.</p>
          <p
            v-if="editCupo < cupoMinimo"
            class="modal-error"
          >El cupo no puede ser menor a {{ cupoMinimo }} (inscriptos actuales).</p>
          <p v-if="editError" class="modal-error">{{ editError }}</p>

          <div class="modal-actions">
            <button type="button" class="modal-btn-cancel" :disabled="guardando" @click="cerrarModalEditar">
              Volver
            </button>
            <button
              type="button"
              class="modal-btn-save"
              :disabled="!edicionValida || guardando"
              @click="confirmarEdicion"
            >
              {{ guardando ? 'Guardando…' : 'Guardar cambios' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

  </AdminLayout>
</template>

<style scoped>
.page-wrapper { width: 100%; }

/* ── Encabezado ── */

.page-header {
  margin-bottom: 1.5rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-back {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 7px;
  color: #374151;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.45rem 0.9rem;
  transition: background-color 0.12s;
  white-space: nowrap;
}

.btn-back:hover { background: #e5e7eb; }

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.2rem;
}

.page-desc {
  color: #374151;
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0.15rem 0 0;
}

.page-subtitle {
  color: #6b7280;
  font-size: 0.82rem;
  margin: 0.1rem 0 0;
}

.btn-secondary {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 7px;
  color: #374151;
  cursor: pointer;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
  transition: background-color 0.12s;
}

.btn-secondary:hover { background: #e5e7eb; }

/* ── Navegación semanal ── */

.week-nav {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}

.week-btn {
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 7px;
  color: #374151;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  padding: 0.4rem 0.75rem;
  transition: background-color 0.12s, border-color 0.12s;
}

.week-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.today-btn {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #1d4ed8;
}

.today-btn:hover {
  background: #dbeafe;
  border-color: #2563eb;
}

.week-label {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1f2937;
  min-width: 200px;
  text-align: center;
}

.week-picker {
  border: 1px solid #d1d5db;
  border-radius: 7px;
  color: #374151;
  font-size: 0.85rem;
  padding: 0.4rem 0.6rem;
  cursor: pointer;
  margin-left: auto;
}

.week-picker:focus {
  outline: none;
  border-color: #11998e;
  box-shadow: 0 0 0 3px rgba(17, 153, 142, 0.12);
}

/* ── Skeleton ── */

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.75rem;
}

.skeleton-col {
  height: 160px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  border-radius: 10px;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Estado de error ── */

.state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 3rem 2rem;
  background: #fff5f5;
  border: 1px solid #fecaca;
  border-radius: 12px;
  text-align: center;
}

.state-icon { font-size: 2rem; }
.state-desc { color: #991b1b; margin: 0; font-size: 0.9rem; }

/* ── Calendario ── */

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.6rem;
}

.day-column {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  min-height: 140px;
}

.day-column.day-today {
  border-color: #11998e;
  box-shadow: 0 0 0 2px rgba(17, 153, 142, 0.15);
}

.day-header {
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem 0.4rem;
}

.day-today .day-header {
  background: #f0fdf9;
}

.day-name {
  font-size: 0.7rem;
  font-weight: 700;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.day-today .day-name { color: #11998e; }

.day-date {
  font-size: 0.82rem;
  font-weight: 600;
  color: #374151;
  margin-top: 1px;
}

.day-body {
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.empty-day {
  text-align: center;
  color: #d1d5db;
  font-size: 0.8rem;
  padding: 0.75rem 0;
  margin: 0;
}

/* ── Tarjeta de clase ── */

.clase-card {
  border-left: 3px solid transparent;
  border-radius: 6px;
  background: #fafafa;
  padding: 0.5rem 0.55rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.card-programada { border-left-color: #3b82f6; background: #eff6ff; }
.card-hoy        { border-left-color: #11998e; background: #f0fdf9; }
.card-finalizada { border-left-color: #d1d5db; background: #f9fafb; }
.card-cancelada  { border-left-color: #fca5a5; background: #fff5f5; }

.clase-horario {
  font-size: 0.78rem;
  font-weight: 700;
  color: #1f2937;
}

.cupo-bar-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.cupo-label {
  font-size: 0.68rem;
  font-weight: 600;
  text-align: right;
}

.cupo-bar-track {
  height: 4px;
  background: #e5e7eb;
  border-radius: 99px;
  overflow: hidden;
}

.cupo-bar-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.3s ease;
}

.cupo-libre    { color: #dc2626; }
.cupo-alto     { color: #d97706; }
.cupo-completo { color: #15803d; font-weight: 700; }

.cupo-bar-fill.cupo-libre    { background: #dc2626; }
.cupo-bar-fill.cupo-alto     { background: #d97706; }
.cupo-bar-fill.cupo-completo { background: #15803d; }

/* ── Badges ── */

.status-badge {
  align-self: center;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 0.15rem 0.45rem;
  border-radius: 99px;
  text-transform: uppercase;
}

.badge-programada { background: #ffedd5; color: #c2410c; }
.badge-hoy        { background: #dcfce7; color: #15803d; }
.badge-finalizada { background: #f3f4f6; color: #6b7280; }
.badge-cancelada  { background: #fff1f2; color: #be123c; }

/* ── Badge asistencia ── */

.asistencia-badge {
  align-self: flex-start;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  border-radius: 99px;
}

.asist-completa { color: #15803d; }
.asist-parcial  { color: #d97706; }
.asist-vacia    { color: #dc2626; }

.cupo-bar-fill.asist-completa { background: #15803d; }
.cupo-bar-fill.asist-parcial  { background: #d97706; }
.cupo-bar-fill.asist-vacia    { background: #dc2626; }

/* ── Acciones ── */

.clase-actions {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin-top: 0.2rem;
}

.btn-action {
  display: block;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.25rem 0.4rem;
  border-radius: 5px;
  text-align: center;
  text-decoration: none;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background-color 0.12s;
}

.btn-ver {
  background: #eff6ff;
  color: #1d4ed8;
  border-color: #bfdbfe;
}
.btn-ver:hover { background: #dbeafe; }

.btn-editar {
  background: #f0fdf9;
  color: #0f766e;
  border-color: #99f6e4;
}
.btn-editar:hover { background: #ccfbf1; }

.btn-cancelar {
  background: #fff1f2;
  color: #be123c;
  border-color: #fecdd3;
}
.btn-cancelar:hover { background: #ffe4e6; }

/* ── Modal ── */

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 1200;
}

.modal-box {
  background: white;
  border-radius: 20px;
  padding: 28px 24px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
  text-align: center;
}

.modal-title {
  margin: 0 0 12px;
  font-size: 1.2rem;
  font-weight: 700;
  color: #1f2937;
}

.modal-text {
  margin: 0 0 10px;
  font-size: 0.95rem;
  color: #374151;
  line-height: 1.5;
}

.modal-subtitle {
  margin: -4px 0 14px;
  font-size: 0.85rem;
  color: #6b7280;
}

.modal-loading {
  padding: 1rem 0;
  color: #6b7280;
  font-size: 0.88rem;
}

.modal-empty {
  padding: 0.75rem 0;
  color: #6b7280;
  font-size: 0.88rem;
  font-style: italic;
}

.modal-error {
  color: #b91c1c;
  font-size: 0.82rem;
  margin: 0 0 10px;
  background: #fff1f2;
  border-radius: 6px;
  padding: 0.4rem 0.7rem;
}

.afectados-list {
  text-align: left;
  margin-bottom: 14px;
  max-height: 180px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.5rem;
}

.afectados-header {
  margin: 0 0 6px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
}

.afectado-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.3rem 0;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.8rem;
}
.afectado-item:last-child { border-bottom: none; }

.afectado-name { color: #1f2937; font-weight: 500; }
.afectado-tipo { color: #6b7280; font-size: 0.72rem; }

.motivo-field {
  text-align: left;
  margin-bottom: 16px;
}

.motivo-label {
  display: block;
  font-size: 0.82rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 6px;
}

.required { color: #dc2626; }

.motivo-textarea {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.85rem;
  padding: 0.5rem 0.7rem;
  resize: vertical;
  font-family: inherit;
  box-sizing: border-box;
  color: #1f2937;
}
.motivo-textarea:focus {
  outline: none;
  border-color: #11998e;
  box-shadow: 0 0 0 3px rgba(17,153,142,0.12);
}

.cancelada-motivo {
  font-size: 0.7rem;
  color: #be123c;
  font-style: italic;
  margin: 0;
  line-height: 1.3;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.modal-btn-cancel,
.modal-btn-confirm {
  border: none;
  border-radius: 999px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  padding: 10px 20px;
}

.modal-btn-cancel {
  background: #f3f4f6;
  color: #374151;
}
.modal-btn-cancel:hover:not(:disabled) { background: #e5e7eb; }
.modal-btn-cancel:disabled { opacity: 0.5; cursor: not-allowed; }

.modal-btn-confirm {
  background: #fee2e2;
  color: #b91c1c;
}
.modal-btn-confirm:hover:not(:disabled) { background: #fecaca; }
.modal-btn-confirm:disabled { opacity: 0.45; cursor: not-allowed; }

.modal-btn-save {
  border: none;
  border-radius: 999px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  padding: 10px 20px;
  background: #11998e;
  color: white;
}
.modal-btn-save:hover:not(:disabled) { background: #0e857c; }
.modal-btn-save:disabled { opacity: 0.45; cursor: not-allowed; }

/* ── Campos de edición ── */

.edit-field {
  text-align: left;
  margin-bottom: 14px;
  flex: 1;
}

.edit-row {
  display: flex;
  gap: 12px;
}

.edit-input {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.85rem;
  padding: 0.5rem 0.7rem;
  font-family: inherit;
  box-sizing: border-box;
  color: #1f2937;
}
.edit-input:focus {
  outline: none;
  border-color: #11998e;
  box-shadow: 0 0 0 3px rgba(17,153,142,0.12);
}

.edit-hint {
  margin: 6px 0 0;
  font-size: 0.74rem;
  color: #6b7280;
}

/* ── Toast ── */

.toast-success {
  position: fixed;
  bottom: 28px;
  left: 50%;
  transform: translateX(-50%);
  background: #166534;
  color: white;
  padding: 12px 24px;
  border-radius: 99px;
  font-size: 0.9rem;
  font-weight: 600;
  z-index: 9999;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
  white-space: nowrap;
}

/* ── Responsivo ── */

@media (max-width: 1100px) {
  .calendar-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 700px) {
  .calendar-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .week-label { min-width: unset; }
}
</style>
