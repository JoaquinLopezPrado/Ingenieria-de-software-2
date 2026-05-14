<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { getTurnos, getFormOptions, extractBackendError, type Turno } from '@/services/sessionService'

// ─── Estado ───────────────────────────────────────────────────────────────────

const turnos = ref<Turno[]>([])
const activityMap = ref<Map<number, string>>(new Map())
const isLoading = ref(true)
const errorMessage = ref('')
const errorType = ref<'auth' | 'forbidden' | 'generic' | null>(null)

const router = useRouter()

// ─── Constantes de visualización ──────────────────────────────────────────────

const DAY_LABELS: Record<string, string> = {
  lunes:      'Lun',
  martes:     'Mar',
  miercoles:  'Mié',
  jueves:     'Jue',
  viernes:    'Vie',
  sabado:     'Sáb',
}

const MONTH_NAMES: Record<number, string> = {
  1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
  5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
  9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic',
}

// ─── Computed ─────────────────────────────────────────────────────────────────

const isEmpty = computed(() => !isLoading.value && !errorMessage.value && turnos.value.length === 0)
const hasData = computed(() => !isLoading.value && !errorMessage.value && turnos.value.length > 0)

// ─── Helpers de display ───────────────────────────────────────────────────────

const formatPeriod = (month: number, year: number) =>
  `${MONTH_NAMES[month] ?? month} ${year}`

const activityName = (id: number) =>
  activityMap.value.get(id) ?? `Actividad #${id}`

// ─── Carga inicial ────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    const [turnosRes, { activities }] = await Promise.all([
      getTurnos(),
      getFormOptions(),
    ])
    turnos.value = turnosRes.items
    activityMap.value = new Map(activities.map(a => [a.id, a.name]))
  } catch (error: unknown) {
    const axiosError = error as { response?: { status?: number }; request?: unknown }
    const status = axiosError?.response?.status

    if (!axiosError.response && axiosError.request) {
      errorType.value = 'generic'
      errorMessage.value = 'No se pudo conectar con el servidor. Verificá que el backend esté corriendo.'
    } else if (status === 401) {
      errorType.value = 'auth'
      errorMessage.value = 'Tu sesión expiró o no estás autenticado. Por favor, iniciá sesión nuevamente.'
    } else if (status === 403) {
      errorType.value = 'forbidden'
      errorMessage.value = 'No tenés permisos para ver la grilla de turnos. Esta sección es solo para administradores.'
    } else {
      errorType.value = 'generic'
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

      <!-- ── Estado: cargando ── -->
      <div v-if="isLoading" class="skeleton-wrapper" aria-label="Cargando turnos...">
        <div v-for="n in 4" :key="n" class="skeleton-row"></div>
      </div>

      <!-- ── Estado: error de autenticación ── -->
      <div v-else-if="errorType === 'auth'" class="state-card state-error">
        <div class="state-icon">🔒</div>
        <h2 class="state-title">Sesión no válida</h2>
        <p class="state-desc">{{ errorMessage }}</p>
        <button class="btn-primary" @click="router.push({ name: 'login' })">
          Ir al login
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

      <!-- ── Estado: sin turnos ── -->
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

      <!-- ── Tabla de turnos ── -->
      <div v-else-if="hasData" class="table-container">
        <table class="turnos-table">
          <thead>
            <tr>
              <th>Actividad</th>
              <th>Descripción</th>
              <th>Días</th>
              <th>Horario</th>
              <th>Cupo</th>
              <th>Período</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="turno in turnos" :key="turno.id">
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
              <td class="cell-period">{{ formatPeriod(turno.month, turno.year) }}</td>
              <td class="cell-status">
                <span :class="['status-badge', turno.is_active ? 'badge-active' : 'badge-inactive']">
                  {{ turno.is_active ? 'Activo' : 'Inactivo' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <p class="table-count">
          {{ turnos.length }} turno{{ turnos.length !== 1 ? 's' : '' }} en total
        </p>
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
  margin-bottom: 2rem;
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

/* ── Botones ── */

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

.turnos-table {
  width: 100%;
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

.table-count {
  padding: 0.75rem 1rem;
  font-size: 0.8rem;
  color: #9ca3af;
  margin: 0;
  border-top: 1px solid #f3f4f6;
  text-align: right;
}

/* ── Responsivo ── */

@media (max-width: 900px) {
  .cell-desc {
    display: none;
  }
}

@media (max-width: 640px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .turnos-table th,
  .turnos-table td {
    padding: 0.7rem 0.6rem;
  }

  .cell-period,
  .cell-capacity {
    display: none;
  }
}
</style>
