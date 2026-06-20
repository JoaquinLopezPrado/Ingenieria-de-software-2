<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { getClasesByTurnoAdmin, type ClaseDetalle } from '@/services/sessionService'

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
  if (!c.is_active)    return 'cancelada'
  if (c.date < today)  return 'finalizada'
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

// ─── Modal cancelar (stub) ────────────────────────────────────────────────────

const claseAConfirmar = ref<ClaseDetalle | null>(null)

function abrirModalCancelar(c: ClaseDetalle) { claseAConfirmar.value = c }
function cerrarModalCancelar()               { claseAConfirmar.value = null }

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
                  Ver asistencias
                </RouterLink>
                <button
                  v-if="claseStatus(clase) === 'programada' || claseStatus(clase) === 'hoy'"
                  type="button"
                  class="btn-action btn-cancelar"
                  @click="abrirModalCancelar(clase)"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- Modal cancelar (stub) -->
    <Teleport to="body">
      <div v-if="claseAConfirmar" class="modal-overlay" @click.self="cerrarModalCancelar">
        <div class="modal-box" role="dialog" aria-modal="true">
          <h2 class="modal-title">Cancelar clase</h2>
          <p class="modal-text">
            ¿Confirmás la cancelación de la clase del
            <strong>{{ claseAConfirmar.date }}</strong>
            ({{ claseAConfirmar.start_time }} – {{ claseAConfirmar.end_time }})?
          </p>
          <p class="modal-pending">Esta funcionalidad estará disponible próximamente.</p>
          <div class="modal-actions">
            <button type="button" class="modal-btn-cancel" @click="cerrarModalCancelar">Volver</button>
            <button type="button" class="modal-btn-confirm" disabled>Confirmar cancelación</button>
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
  align-self: flex-start;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 0.15rem 0.45rem;
  border-radius: 99px;
  text-transform: uppercase;
}

.badge-programada { background: #dbeafe; color: #1d4ed8; }
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

.modal-pending {
  margin: 0 0 20px;
  font-size: 0.82rem;
  color: #9ca3af;
  font-style: italic;
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
.modal-btn-cancel:hover { background: #e5e7eb; }

.modal-btn-confirm {
  background: #fee2e2;
  color: #b91c1c;
  opacity: 0.5;
  cursor: not-allowed;
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
