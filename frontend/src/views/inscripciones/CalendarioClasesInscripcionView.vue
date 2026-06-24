<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { useInscripcionStore } from '@/stores/inscripcionStore'
import { getTurnosAll, getClasesByTurnoAdmin, getFormOptions, extractBackendError, getClasesByTurno } from '@/services/sessionService'
import type { Turno } from '@/services/sessionService'

// ─── Tipos ────────────────────────────────────────────────────────────────────

export interface ClaseInscribible {
  id: number
  turno_id: number
  date: string       // "YYYY-MM-DD"
  start_time: string
  end_time: string
  capacity: number
  enrolled: number
  activity_id: number
  activity_name: string
  class_price: number
}

const router = useRouter()
const store = useInscripcionStore()

// Garantizado no-null por el guard de flujo del router
const cliente = computed(() => store.clienteSeleccionado!)

// ─── Horizonte de fechas ──────────────────────────────────────────────────────

function isoDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function getMonday(d: Date): Date {
  const date = new Date(d)
  const day = date.getDay()
  date.setDate(date.getDate() + (day === 0 ? -6 : 1 - day))
  date.setHours(0, 0, 0, 0)
  return date
}

const todayDate = new Date()
const today = isoDate(todayDate)
// Mes actual + 2 meses siguientes
const horizonEnd = isoDate(new Date(todayDate.getFullYear(), todayDate.getMonth() + 3, 0))

// ─── Estado ───────────────────────────────────────────────────────────────────

const todasLasClases = ref<ClaseInscribible[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

// ─── Filtro por actividad ─────────────────────────────────────────────────────

const filterActivity = ref<number | ''>('')

const actividadesDisponibles = computed(() => {
  const seen = new Set<number>()
  const opts: { id: number; name: string }[] = []
  todasLasClases.value.forEach(c => {
    if (!seen.has(c.activity_id)) {
      seen.add(c.activity_id)
      opts.push({ id: c.activity_id, name: c.activity_name })
    }
  })
  return opts.sort((a, b) => a.name.localeCompare(b.name))
})

const clasesFiltradas = computed(() =>
  filterActivity.value === ''
    ? todasLasClases.value
    : todasLasClases.value.filter(c => c.activity_id === filterActivity.value)
)

const isEmpty = computed(() =>
  !isLoading.value && !errorMessage.value && todasLasClases.value.length === 0
)

const noResults = computed(() =>
  !isLoading.value && !errorMessage.value &&
  todasLasClases.value.length > 0 &&
  clasesFiltradas.value.length === 0
)

// ─── Navegación semanal ───────────────────────────────────────────────────────

const DAY_NAMES = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

const weekStart = ref<Date>(getMonday(new Date()))

const weekDays = computed(() =>
  Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart.value)
    d.setDate(d.getDate() + i)
    return d
  })
)

const weekLabel = computed(() => {
  const from = weekDays.value[0]!
  const to = weekDays.value[6]!
  const opts: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' }
  return `${from.toLocaleDateString('es-AR', opts)} – ${to.toLocaleDateString('es-AR', opts)} ${to.getFullYear()}`
})

const isCurrentWeek = computed(() =>
  isoDate(weekStart.value) === isoDate(getMonday(new Date()))
)

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

function onDatePick(e: Event) {
  const val = (e.target as HTMLInputElement).value
  if (val) weekStart.value = getMonday(new Date(val + 'T12:00:00'))
}

function clasesDelDia(day: Date): ClaseInscribible[] {
  const iso = isoDate(day)
  return clasesFiltradas.value.filter(c => c.date === iso)
}

// ─── Acción ───────────────────────────────────────────────────────────────────

function handleClaseClick(clase: ClaseInscribible) {
  store.setClase(clase)
  router.push({ name: 'inscripciones-inscribir-clase', params: { claseId: clase.id } })
}

// ─── Carga inicial ────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    const [turnosRes, formOpts] = await Promise.all([
      getTurnosAll({ page_size: 500 }),
      getFormOptions(),
    ])

    const activityMap = new Map<number, string>(
      formOpts.activities.map(a => [a.id, a.name])
    )

    const turnosActivos: Turno[] = turnosRes.items.filter(t => t.is_active)

    const clasesChunks = await Promise.all(
      turnosActivos.map(turno =>
        getClasesByTurno(turno.id)
          .then(clases =>
            clases
              .filter(c =>
                c.is_active &&
                c.capacity > 0 &&
                c.enrolled < c.capacity &&
                c.date >= today &&
                c.date <= horizonEnd
              )
              .map(c => ({
                ...c,
                activity_id: turno.activity_id,
                activity_name: activityMap.get(turno.activity_id) ?? `Actividad #${turno.activity_id}`,
                class_price: turno.class_price,
              }) as ClaseInscribible)
          )
          .catch(() => [] as ClaseInscribible[])
      )
    )

    todasLasClases.value = clasesChunks
      .flat()
      .sort((a, b) => a.date.localeCompare(b.date) || a.start_time.localeCompare(b.start_time))
  } catch (err) {
    errorMessage.value = extractBackendError(err)
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <!-- ── Encabezado ── -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Inscribir a clase</h1>
          <p class="page-subtitle">Seleccioná una clase disponible para inscribir al cliente</p>
        </div>
        <button
          type="button"
          class="btn-secondary"
          @click="router.push({ name: 'ficha-cliente', params: { clienteId: cliente?.id } })"
        >
          ← Volver a la ficha
        </button>
      </div>

      <!-- ── Banner cliente ── -->
      <div v-if="cliente" class="cliente-banner">
        <div class="cliente-avatar" aria-hidden="true">
          {{ cliente.first_name[0] }}{{ cliente.last_name[0] }}
        </div>
        <div class="cliente-info">
          <span class="cliente-label">Cliente seleccionado</span>
          <span class="cliente-name">{{ cliente.first_name }} {{ cliente.last_name }}</span>
          <span class="cliente-doc">{{ cliente.doc_type_name }} {{ cliente.doc_number }}</span>
        </div>
      </div>

      <!-- ── Filtro por actividad ── -->
      <div v-if="!isLoading && !errorMessage && !isEmpty" class="filter-bar">
        <label class="filter-label">Actividad</label>
        <select v-model="filterActivity" class="filter-select">
          <option value="">Todas las actividades</option>
          <option v-for="a in actividadesDisponibles" :key="a.id" :value="a.id">
            {{ a.name }}
          </option>
        </select>
      </div>

      <!-- ── Navegación semanal ── -->
      <div v-if="!isLoading && !errorMessage" class="week-nav">
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

      <!-- ── Skeleton ── -->
      <div v-if="isLoading" class="skeleton-grid">
        <div v-for="n in 7" :key="n" class="skeleton-col"></div>
      </div>

      <!-- ── Error ── -->
      <div v-else-if="errorMessage" class="state-card state-error">
        <div class="state-icon">⚠</div>
        <p class="state-desc">{{ errorMessage }}</p>
        <button class="btn-secondary" type="button" @click="router.go(0)">Reintentar</button>
      </div>

      <!-- ── Sin clases en el horizonte ── -->
      <div v-else-if="isEmpty" class="state-card state-empty">
        <div class="state-icon">📅</div>
        <h2 class="state-title">No hay clases disponibles</h2>
        <p class="state-desc">
          No se encontraron clases con cupo disponible en los próximos 3 meses.
        </p>
      </div>

      <!-- ── Sin resultados con filtro ── -->
      <div v-else-if="noResults" class="state-card state-empty">
        <div class="state-icon">🔍</div>
        <h2 class="state-title">No hay clases que coincidan con los filtros aplicados</h2>
        <p class="state-desc">Probá con otra actividad o limpiá el filtro.</p>
        <button class="btn-secondary" type="button" @click="filterActivity = ''">
          Limpiar filtro
        </button>
      </div>

      <!-- ── Calendario ── -->
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

            <button
              v-for="clase in clasesDelDia(day)"
              :key="clase.id"
              type="button"
              class="clase-card"
              @click="handleClaseClick(clase)"
            >
              <span class="clase-actividad">{{ clase.activity_name }}</span>
              <span class="clase-horario">{{ clase.start_time }} – {{ clase.end_time }}</span>
              <div class="clase-meta">
                <span class="clase-cupo">
                  {{ clase.capacity - clase.enrolled }}
                  lugar{{ clase.capacity - clase.enrolled !== 1 ? 'es' : '' }}
                </span>
                <span class="clase-precio">${{ clase.class_price.toLocaleString('es-AR') }}</span>
              </div>
            </button>
          </div>
        </div>
      </div>

    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper {
  width: 100%;
}

/* ── Encabezado ── */

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}

.page-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
}

.page-subtitle {
  color: #6b7280;
  font-size: 0.88rem;
  margin: 0;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background-color: #f3f4f6;
  color: #374151;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.15s;
}

.btn-secondary:hover {
  background-color: #e5e7eb;
}

/* ── Banner cliente ── */

.cliente-banner {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
  border: 1.5px solid #a7f3d0;
  border-radius: 12px;
  padding: 0.9rem 1.25rem;
  margin-bottom: 1.25rem;
}

.cliente-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #11998e, #0d9b8a);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  font-weight: 700;
  flex-shrink: 0;
}

.cliente-info {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}

.cliente-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: #059669;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.cliente-name {
  font-size: 0.92rem;
  font-weight: 700;
  color: #064e3b;
}

.cliente-doc {
  font-size: 0.82rem;
  color: #065f46;
  font-weight: 500;
}

/* ── Filtro ── */

.filter-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.filter-label {
  font-size: 0.78rem;
  font-weight: 700;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.filter-select {
  appearance: none;
  background: white url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 8L1 3h10z'/%3E%3C/svg%3E") no-repeat right 0.7rem center;
  border: 1px solid #d1d5db;
  border-radius: 7px;
  color: #374151;
  font-size: 0.875rem;
  padding: 0.45rem 2rem 0.45rem 0.7rem;
  cursor: pointer;
  transition: border-color 0.15s;
  min-width: 200px;
}

.filter-select:focus {
  outline: none;
  border-color: #11998e;
  box-shadow: 0 0 0 3px rgba(17, 153, 142, 0.12);
}

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

/* ── Estados ── */

.state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3.5rem 2rem;
  border-radius: 12px;
  text-align: center;
}

.state-empty {
  background-color: #f9fafb;
  border: 2px dashed #d1d5db;
}

.state-error {
  background-color: #fff5f5;
  border: 1px solid #fecaca;
}

.state-icon {
  font-size: 2.5rem;
  line-height: 1;
}

.state-title {
  font-size: 1rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.state-desc {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
  max-width: 400px;
}

.state-error .state-desc {
  color: #991b1b;
}

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

.day-today .day-name {
  color: #11998e;
}

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
  font-size: 0.78rem;
  padding: 0.75rem 0;
  margin: 0;
}

/* ── Tarjeta de clase (clickeable) ── */

.clase-card {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem 0.55rem;
  background: #f0fdf9;
  border: 1.5px solid #a7f3d0;
  border-left: 3px solid #11998e;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  width: 100%;
  transition: background-color 0.12s, border-color 0.12s, transform 0.1s;
}

.clase-card:hover {
  background: #dcfce7;
  border-color: #6ee7b7;
  border-left-color: #059669;
  transform: translateY(-1px);
}

.clase-actividad {
  font-size: 0.72rem;
  font-weight: 700;
  color: #064e3b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.clase-horario {
  font-size: 0.7rem;
  font-weight: 600;
  color: #065f46;
  font-variant-numeric: tabular-nums;
}

.clase-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.25rem;
  margin-top: 0.1rem;
}

.clase-cupo {
  font-size: 0.65rem;
  font-weight: 600;
  color: #0d9b8a;
  white-space: nowrap;
}

.clase-precio {
  font-size: 0.65rem;
  font-weight: 700;
  color: #374151;
  white-space: nowrap;
}

/* ── Responsive ── */

@media (max-width: 1100px) {
  .calendar-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 700px) {
  .calendar-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .week-label {
    min-width: unset;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
