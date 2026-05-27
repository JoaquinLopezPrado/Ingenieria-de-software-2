<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import {
  getTurnosAll,
  getAllActivities,
  extractBackendError,
  type Turno,
  type ActivityOption,
} from '@/services/sessionService'

// ─── Estado principal ──────────────────────────────────────────────────────────

const allTurnos = ref<Turno[]>([])
const allActivities = ref<ActivityOption[]>([])
const activityMap = ref<Map<number, string>>(new Map())
const isLoading = ref(true)
const errorMessage = ref('')
const errorType = ref<'auth' | 'forbidden' | 'generic' | null>(null)

const router = useRouter()

// ─── Constantes ────────────────────────────────────────────────────────────────

const DAY_OPTIONS = [
  { value: 'lunes',     label: 'Lun' },
  { value: 'martes',    label: 'Mar' },
  { value: 'miercoles', label: 'Mié' },
  { value: 'jueves',    label: 'Jue' },
  { value: 'viernes',   label: 'Vie' },
  { value: 'sabado',    label: 'Sáb' },
]

const DAY_LABELS: Record<string, string> = {
  lunes: 'Lun', martes: 'Mar', miercoles: 'Mié',
  jueves: 'Jue', viernes: 'Vie', sabado: 'Sáb',
}

const MONTH_NAMES: Record<number, string> = {
  1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
  5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
  9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic',
}

const PAGE_SIZE = 10

// ─── Estado de filtros ─────────────────────────────────────────────────────────

const filterActivity = ref<number | ''>('')
const filterDays = ref<string[]>([])
const filterInstructor = ref('')
const filterAvailability = ref<'' | 'active' | 'inactive'>('')

// ─── Paginación ────────────────────────────────────────────────────────────────

const currentPage = ref(1)

// ─── Opciones para los selects de filtro ──────────────────────────────────────

const instructorOptions = computed(() => {
  const seen = new Set<string>()
  const opts: string[] = []
  allTurnos.value.forEach((t: Turno) => {
    if (t.instructor && !seen.has(t.instructor)) {
      seen.add(t.instructor)
      opts.push(t.instructor)
    }
  })
  return opts.sort()
})

// ─── Filtrado (client-side) ───────────────────────────────────────────────────

const filteredTurnos = computed(() => {
  let result: Turno[] = allTurnos.value

  if (filterActivity.value !== '') {
    result = result.filter((t: Turno) => t.activity_id === filterActivity.value)
  }

  if (filterDays.value.length > 0) {
    result = result.filter((t: Turno) =>
      filterDays.value.some((d: string) => t.days.includes(d))
    )
  }

  if (filterInstructor.value) {
    result = result.filter((t: Turno) => t.instructor === filterInstructor.value)
  }

  if (filterAvailability.value === 'active') {
    result = result.filter((t: Turno) => t.is_active)
  } else if (filterAvailability.value === 'inactive') {
    result = result.filter((t: Turno) => !t.is_active)
  }

  return result
})

// ─── Paginación (client-side) ─────────────────────────────────────────────────

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredTurnos.value.length / PAGE_SIZE))
)

const paginatedTurnos = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredTurnos.value.slice(start, start + PAGE_SIZE)
})

const paginationRange = computed((): (number | '...')[] => {
  const total = totalPages.value
  const cur = currentPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 4)        return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 3) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]
  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})

const showingFrom = computed(() => (currentPage.value - 1) * PAGE_SIZE + 1)
const showingTo   = computed(() => Math.min(currentPage.value * PAGE_SIZE, filteredTurnos.value.length))

// ─── Flags de UI ──────────────────────────────────────────────────────────────

const hasFilters = computed(() =>
  filterActivity.value !== '' ||
  filterDays.value.length > 0 ||
  filterInstructor.value !== '' ||
  filterAvailability.value !== ''
)

const isEmpty = computed(() =>
  !isLoading.value && !errorMessage.value && allTurnos.value.length === 0
)

const noResults = computed(() =>
  !isLoading.value && !errorMessage.value &&
  allTurnos.value.length > 0 && filteredTurnos.value.length === 0
)

const hasData = computed(() =>
  !isLoading.value && !errorMessage.value && filteredTurnos.value.length > 0
)

// ─── Watches ──────────────────────────────────────────────────────────────────

watch([filterActivity, filterDays, filterInstructor, filterAvailability], () => {
  currentPage.value = 1
})

// ─── Helpers ──────────────────────────────────────────────────────────────────

const formatPeriod = (month: number, year: number) =>
  `${MONTH_NAMES[month] ?? month} ${year}`

const activityName = (id: number) =>
  activityMap.value.get(id) ?? `Actividad #${id}`

function toggleDay(day: string) {
  const idx = filterDays.value.indexOf(day)
  if (idx === -1) filterDays.value.push(day)
  else            filterDays.value.splice(idx, 1)
}

function clearFilters() {
  filterActivity.value = ''
  filterDays.value = []
  filterInstructor.value = ''
  filterAvailability.value = ''
  currentPage.value = 1
}

function goToPage(page: number | '...') {
  if (typeof page === 'number') currentPage.value = page
}

// ─── Carga inicial ─────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    const [turnosRes, activities] = await Promise.all([
      getTurnosAll({ page_size: 500 }),
      getAllActivities(),
    ])
    allTurnos.value = turnosRes.items
    allActivities.value = activities
    activityMap.value = new Map(activities.map(a => [a.id, a.name]))
  } catch (error: unknown) {
    const axiosError = error as { response?: { status?: number }; request?: unknown }
    const status = axiosError?.response?.status

    if (!axiosError.response && axiosError.request) {
      errorType.value    = 'generic'
      errorMessage.value = 'No se pudo conectar con el servidor. Verificá que el backend esté corriendo.'
    } else if (status === 401) {
      errorType.value    = 'auth'
      errorMessage.value = 'Tu sesión expiró o no estás autenticado. Por favor, iniciá sesión nuevamente.'
    } else if (status === 403) {
      errorType.value    = 'forbidden'
      errorMessage.value = 'No tenés permisos para ver la grilla de turnos. Esta sección es solo para administradores.'
    } else {
      errorType.value    = 'generic'
      errorMessage.value = extractBackendError(error)
    }
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
          <h1 class="page-title">Grilla de Turnos</h1>
          <p class="page-subtitle">Turnos programados para las actividades del centro</p>
        </div>
        <RouterLink
          v-if="!errorType"
          to="/activities/schedule"
          class="btn-primary"
        >
          <span class="btn-icon">+</span>
          Programar nuevo turno
        </RouterLink>
      </div>

      <!-- ── Panel de filtros ── -->
      <div v-if="!isLoading && !errorType" class="filters-card">
        <div class="filters-grid">

          <div class="filter-group">
            <label class="filter-label">Actividad</label>
            <select v-model="filterActivity" class="filter-select">
              <option value="">Todas las actividades</option>
              <option v-for="a in allActivities" :key="a.id" :value="a.id">
                {{ a.name }}
              </option>
            </select>
          </div>

          <div class="filter-group">
            <label class="filter-label">Profesor</label>
            <select v-model="filterInstructor" class="filter-select">
              <option value="">Todos los profesores</option>
              <option v-for="inst in instructorOptions" :key="inst" :value="inst">
                {{ inst }}
              </option>
            </select>
          </div>

          <div class="filter-group">
            <label class="filter-label">Disponibilidad</label>
            <select v-model="filterAvailability" class="filter-select">
              <option value="">Todos los turnos</option>
              <option value="active">Solo activos</option>
              <option value="inactive">Solo inactivos</option>
            </select>
          </div>

        </div>

        <div class="filters-days-row">
          <span class="filter-label">Días</span>
          <div class="day-filter-pills">
            <button
              v-for="day in DAY_OPTIONS"
              :key="day.value"
              type="button"
              :class="['day-filter-pill', { 'pill-active': filterDays.includes(day.value) }]"
              @click="toggleDay(day.value)"
            >
              {{ day.label }}
            </button>
          </div>
          <button
            v-if="hasFilters"
            type="button"
            class="btn-clear"
            @click="clearFilters"
          >
            ✕ Limpiar filtros
          </button>
        </div>
      </div>

      <!-- ── Estado: cargando ── -->
      <div v-if="isLoading" class="skeleton-wrapper" aria-label="Cargando turnos...">
        <div v-for="n in 5" :key="n" class="skeleton-row"></div>
      </div>

      <!-- ── Estado: error de autenticación ── -->
      <div v-else-if="errorType === 'auth'" class="state-card state-error">
        <div class="state-icon">🔒</div>
        <h2 class="state-title">Sesión no válida</h2>
        <p class="state-desc">{{ errorMessage }}</p>
        <button class="btn-primary" @click="router.push({ name: 'login' })">
          Iniciar sesion
        </button>
      </div>

      <!-- ── Estado: sin permisos ── -->
      <div v-else-if="errorType === 'forbidden'" class="state-card state-error">
        <div class="state-icon">⛔</div>
        <h2 class="state-title">Acceso denegado</h2>
        <p class="state-desc">{{ errorMessage }}</p>
      </div>

      <!-- ── Estado: error genérico ── -->
      <div v-else-if="errorType === 'generic'" class="state-card state-error">
        <div class="state-icon">⚠</div>
        <h2 class="state-title">Error al cargar los turnos</h2>
        <p class="state-desc">{{ errorMessage }}</p>
        <button class="btn-secondary" @click="router.go(0)">
          Reintentar
        </button>
      </div>

      <!-- ── Estado: sin turnos en el sistema ── -->
      <div v-else-if="isEmpty" class="state-card state-empty">
        <div class="state-icon">📅</div>
        <h2 class="state-title">No hay turnos programados</h2>
        <p class="state-desc">
          Todavía no se programó ningún turno. Usá el botón de arriba para crear el primero.
        </p>
        <RouterLink to="/activities/schedule" class="btn-primary">
          Programar primer turno
        </RouterLink>
      </div>

      <!-- ── Estado: filtros sin resultados ── -->
      <div v-else-if="noResults" class="state-card state-empty">
        <div class="state-icon">🔍</div>
        <h2 class="state-title">Sin resultados</h2>
        <p class="state-desc">
          Ningún turno coincide con los filtros aplicados.
        </p>
        <button class="btn-secondary" @click="clearFilters">
          Limpiar filtros
        </button>
      </div>

      <!-- ── Tabla de turnos ── -->
      <div v-else-if="hasData" class="table-container">
        <div class="table-scroll">
        <table class="turnos-table">
          <thead>
            <tr>
              <th>Actividad</th>
              <th>Descripción</th>
              <th>Días</th>
              <th>Horario</th>
              <th>Cupo</th>
              <th>Valor de clase</th>
              <th>Valor del turno</th>
              <th>Período</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="turno in paginatedTurnos" :key="turno.id">
              <td class="cell-activity">{{ activityName(turno.activity_id) }}</td>
              <td class="cell-desc">{{ turno.description || '—' }}</td>
              <td class="cell-days">
                <span
                  v-for="day in turno.days"
                  :key="day"
                  class="day-pill"
                >
                  {{ DAY_LABELS[day] ?? day }}
                </span>
              </td>
              <td class="cell-time">{{ turno.start_time }} – {{ turno.end_time }}</td>
              <td class="cell-capacity">{{ turno.capacity }}</td>
              <td class="cell-price">${{ turno.class_price }}</td>
              <td class="cell-price">${{ turno.price }}</td>
              <td class="cell-period">{{ formatPeriod(turno.month, turno.year) }}</td>
              <td class="cell-status">
                <span :class="['status-badge', turno.is_active ? 'badge-active' : 'badge-inactive']">
                  {{ turno.is_active ? 'Activo' : 'Inactivo' }}
                </span>
              </td>
              <td class="cell-actions">
                <RouterLink
                  :to="`/activities/turnos/${turno.id}/edit`"
                  class="btn-edit"
                >
                  Editar
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>

        </div><!-- /table-scroll -->

        <!-- ── Footer: conteo + paginación ── -->
        <div class="table-footer">
          <span class="table-count">
            Mostrando {{ showingFrom }}–{{ showingTo }} de
            {{ filteredTurnos.length }} turno{{ filteredTurnos.length !== 1 ? 's' : '' }}
          </span>

          <div v-if="totalPages > 1" class="pagination">
            <button
              class="page-btn"
              :disabled="currentPage === 1"
              @click="currentPage--"
              aria-label="Página anterior"
            >
              ←
            </button>
            <button
              v-for="(page, idx) in paginationRange"
              :key="idx"
              :class="['page-btn', {
                'page-btn-active': page === currentPage,
                'page-btn-dots':   page === '...',
              }]"
              :disabled="page === '...'"
              @click="goToPage(page)"
            >
              {{ page }}
            </button>
            <button
              class="page-btn"
              :disabled="currentPage === totalPages"
              @click="currentPage++"
              aria-label="Página siguiente"
            >
              →
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
  margin-bottom: 1.5rem;
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

/* ── Botones globales ── */

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background-color: #11998e;
  color: white;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  text-decoration: none;
  white-space: nowrap;
  transition: background-color 0.15s;
}

.btn-primary:hover {
  background-color: #0c8a70;
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
  text-decoration: none;
  transition: background-color 0.15s;
}

.btn-secondary:hover {
  background-color: #e5e7eb;
}

.btn-icon {
  font-size: 1.1rem;
  line-height: 1;
  margin-bottom: 1px;
}

/* ── Panel de filtros ── */

.filters-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.filter-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: #6b7280;
  letter-spacing: 0.05em;
  text-transform: uppercase;
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
  width: 100%;
}

.filter-select:focus {
  outline: none;
  border-color: #11998e;
  box-shadow: 0 0 0 3px rgba(17, 153, 142, 0.12);
}

.filters-days-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.day-filter-pills {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.day-filter-pill {
  background: white;
  border: 1.5px solid #d1d5db;
  border-radius: 99px;
  color: #374151;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.65rem;
  transition: background-color 0.12s, border-color 0.12s, color 0.12s;
  white-space: nowrap;
}

.day-filter-pill:hover {
  border-color: #11998e;
  color: #11998e;
}

.day-filter-pill.pill-active {
  background-color: #11998e;
  border-color: #11998e;
  color: white;
}

.btn-clear {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  margin-left: auto;
  padding: 0.25rem 0.5rem;
  transition: color 0.12s;
  white-space: nowrap;
}

.btn-clear:hover {
  color: #dc2626;
}

/* ── Skeleton loader ── */

.skeleton-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.skeleton-row {
  height: 52px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  border-radius: 8px;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Estados vacío / error ── */

.state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 4rem 2rem;
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
  font-size: 1.1rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.state-desc {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
  max-width: 420px;
}

.state-error .state-title,
.state-error .state-desc {
  color: #991b1b;
}

/* ── Tabla ── */

.table-container {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.table-scroll {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.turnos-table {
  width: 100%;
  min-width: 750px;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.turnos-table thead {
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.turnos-table th {
  padding: 0.85rem 1rem;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  color: #6b7280;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
}

.turnos-table td {
  padding: 0.9rem 1rem;
  color: #374151;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}

.turnos-table tbody tr:last-child td {
  border-bottom: none;
}

.turnos-table tbody tr:hover {
  background-color: #fafafa;
}

.cell-activity {
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
}

.cell-desc {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #6b7280;
}

.cell-days {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.day-pill {
  background-color: #eff6ff;
  color: #1d4ed8;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  white-space: nowrap;
}

.cell-time {
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.cell-capacity {
  text-align: center;
}

.cell-period {
  white-space: nowrap;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.2rem 0.6rem;
  border-radius: 99px;
  white-space: nowrap;
}

.badge-active {
  background-color: #dcfce7;
  color: #15803d;
}

.badge-inactive {
  background-color: #f3f4f6;
  color: #6b7280;
}

.cell-actions {
  white-space: nowrap;
}

.btn-edit {
  display: inline-flex;
  align-items: center;
  background-color: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.3rem 0.75rem;
  text-decoration: none;
  transition: background-color 0.12s, border-color 0.12s;
  white-space: nowrap;
}

.btn-edit:hover {
  background-color: #dbeafe;
  border-color: #93c5fd;
}

/* ── Footer de la tabla ── */

.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid #f3f4f6;
  flex-wrap: wrap;
}

.table-count {
  font-size: 0.8rem;
  color: #9ca3af;
}

/* ── Paginación ── */

.pagination {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.page-btn {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #374151;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 500;
  min-width: 2rem;
  padding: 0.3rem 0.5rem;
  transition: background-color 0.12s, border-color 0.12s, color 0.12s;
}

.page-btn:hover:not(:disabled) {
  background-color: #f3f4f6;
  border-color: #d1d5db;
}

.page-btn:disabled {
  cursor: default;
  opacity: 0.4;
}

.page-btn-active {
  background-color: #11998e;
  border-color: #11998e;
  color: white;
  font-weight: 700;
}

.page-btn-active:hover:not(:disabled) {
  background-color: #0c8a70;
}

.page-btn-dots {
  border-color: transparent;
  cursor: default;
}

/* ── Responsivo ── */

@media (max-width: 1024px) {
  .filters-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .filters-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .turnos-table th,
  .turnos-table td {
    padding: 0.7rem 0.6rem;
  }

  .table-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}
</style>
