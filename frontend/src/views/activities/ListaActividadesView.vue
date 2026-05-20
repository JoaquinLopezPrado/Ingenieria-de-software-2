<script setup lang="ts">
/**
 * ListaActividadesView — HU ACT-04.01: Listar actividades
 * --------------------------------------------------------
 * Muestra el listado completo de actividades (activas e inactivas).
 *
 * Escenarios cubiertos:
 *   1. Listado exitoso con actividades cargadas
 *   2. Sin actividades cargadas → mensaje informativo
 *   3. Acceso denegado (rol no admin)
 *   4. Filtrado por nombre
 *   5. Filtrado por estado
 *   6. Filtrado combinado
 *   7. Filtrado sin resultados
 *
 * Filtros y paginado son client-side sobre el total cargado desde GET /api/v1/activities.
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import CreateActivityModal from '@/components/CreateActivityModal.vue'
import {
  createActivity,
  getAllActivities,
  extractBackendError,
  type ActivityOption,
  type CreateActivityPayload,
} from '@/services/sessionService'
import { useAuthStore } from '@/stores/authStore'

const router   = useRouter()
const authStore = useAuthStore()

// ─── Guard de rol ─────────────────────────────────────────────────────────────

const isAdmin = computed(() => {
  const u = authStore.user
  if (!u) return true   // sin datos aún → deja pasar, la API decidirá
  return u.role === 'admin' || u.roles?.includes('admin') || u.role === 'Administrador'
})

// ─── Estado ───────────────────────────────────────────────────────────────────

const activities  = ref<ActivityOption[]>([])
const isLoading   = ref(true)
const loadError   = ref('')
const createError = ref('')
const isCreateActivityVisible = ref(false)
const isCreatingActivity = ref(false)

// ─── Filtros ──────────────────────────────────────────────────────────────────

const filterName   = ref('')
const filterDesc   = ref('')
const filterStatus = ref<'' | 'active' | 'inactive'>('')

// ─── Paginación ───────────────────────────────────────────────────────────────

const PAGE_SIZE   = 10
const currentPage = ref(1)

// ─── Datos filtrados y paginados ──────────────────────────────────────────────

const filtered = computed(() => {
  let list = activities.value

  if (filterName.value.trim()) {
    const q = filterName.value.trim().toLowerCase()
    list = list.filter(a => a.name.toLowerCase().includes(q))
  }

  if (filterDesc.value.trim()) {
    const q = filterDesc.value.trim().toLowerCase()
    list = list.filter(a => (a.description ?? '').toLowerCase().includes(q))
  }

  if (filterStatus.value === 'active')   list = list.filter(a =>  a.is_active)
  if (filterStatus.value === 'inactive') list = list.filter(a => !a.is_active)

  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / PAGE_SIZE)))

const paginated = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filtered.value.slice(start, start + PAGE_SIZE)
})

/** "Mostrando X-Y de Z actividades" */
const rangeLabel = computed(() => {
  const total = filtered.value.length
  if (total === 0) return ''
  const start = (currentPage.value - 1) * PAGE_SIZE + 1
  const end   = Math.min(currentPage.value * PAGE_SIZE, total)
  return `Mostrando ${start}-${end} de ${total} actividad${total === 1 ? '' : 'es'}`
})

// Resetear página cuando cambian los filtros
function resetPage() { currentPage.value = 1 }

function openCreateActivityModal() {
  createError.value = ''
  isCreateActivityVisible.value = true
}

function closeCreateActivityModal() {
  isCreateActivityVisible.value = false
}

async function refreshActivities() {
  activities.value = await getAllActivities()
}

async function handleCreateActivity(payload: CreateActivityPayload) {
  isCreatingActivity.value = true
  createError.value = ''

  try {
    await createActivity(payload)
    await refreshActivities()
    closeCreateActivityModal()
  } catch (error) {
    createError.value = extractBackendError(error)
  } finally {
    isCreatingActivity.value = false
  }
}

// ─── Carga inicial ────────────────────────────────────────────────────────────

onMounted(async () => {
  if (!isAdmin.value) { isLoading.value = false; return }
  try {
    activities.value = await getAllActivities()
  } catch (e: unknown) {
    const status = (e as { response?: { status?: number } })?.response?.status
    loadError.value = status === 403
      ? '__forbidden__'
      : 'No se pudo cargar el listado. Verificá que el servidor esté corriendo.'
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
          <h1 class="page-title">Actividades</h1>
          <p class="page-subtitle">Gestión de la oferta de actividades del centro</p>
        </div>
        <button class="btn-primary" @click="openCreateActivityModal">
          + Crear nueva actividad
        </button>
      </div>

      <transition name="fade">
        <div v-if="createError" class="alert alert-error" role="alert">
          <span class="alert-icon error-icon">!</span>
          <span>{{ createError }}</span>
          <button class="alert-close" @click="createError = ''" aria-label="Cerrar">×</button>
        </div>
      </transition>

      <!-- ── Escenario 3: Sin permisos ── -->
      <div v-if="!isAdmin || loadError === '__forbidden__'" class="state-card state-forbidden">
        <div class="state-icon">⛔</div>
        <h2 class="state-title">No tiene permisos para acceder a esta sección</h2>
        <p class="state-desc">Esta sección es exclusiva para administradores.</p>
        <button class="btn-secondary" @click="router.push({ name: 'home' })">Volver al inicio</button>
      </div>

      <!-- ── Error de carga ── -->
      <div v-else-if="loadError" class="state-card state-error">
        <div class="state-icon">⚠</div>
        <h2 class="state-title">Error al cargar las actividades</h2>
        <p class="state-desc">{{ loadError }}</p>
        <button class="btn-secondary" @click="router.go(0)">Reintentar</button>
      </div>

      <!-- ── Skeleton ── -->
      <template v-else-if="isLoading">
        <div class="filters-skeleton">
          <div class="sk-input"></div>
          <div class="sk-input"></div>
          <div class="sk-select"></div>
        </div>
        <div class="table-skeleton">
          <div v-for="i in 5" :key="i" class="sk-row"></div>
        </div>
      </template>

      <!-- ── Contenido principal ── -->
      <template v-else>

        <!-- Escenario 2: sin actividades en el sistema -->
        <div v-if="activities.length === 0" class="state-card state-empty">
          <div class="state-icon">📋</div>
          <h2 class="state-title">No hay actividades cargadas en el sistema</h2>
          <p class="state-desc">Creá la primera actividad usando el botón de arriba.</p>
        </div>

        <template v-else>

          <!-- ── Filtros ── -->
          <div class="filters-bar">
            <div class="filter-group">
              <label class="filter-label" for="filter-name">Nombre</label>
              <input
                id="filter-name"
                v-model="filterName"
                type="text"
                class="filter-input"
                placeholder="Buscar por nombre..."
                @input="resetPage"
              />
            </div>

            <div class="filter-group">
              <label class="filter-label" for="filter-desc">Descripción</label>
              <input
                id="filter-desc"
                v-model="filterDesc"
                type="text"
                class="filter-input"
                placeholder="Buscar por descripción..."
                @input="resetPage"
              />
            </div>

            <div class="filter-group">
              <label class="filter-label" for="filter-status">Estado</label>
              <select
                id="filter-status"
                v-model="filterStatus"
                class="filter-select"
                @change="resetPage"
              >
                <option value="">Todos</option>
                <option value="active">Activa</option>
                <option value="inactive">Inactiva</option>
              </select>
            </div>

            <button
              v-if="filterName || filterDesc || filterStatus"
              class="btn-clear"
              @click="filterName = ''; filterDesc = ''; filterStatus = ''; resetPage()"
            >
              Limpiar filtros
            </button>
          </div>

          <!-- ── Contador ── -->
          <p v-if="rangeLabel" class="range-label">{{ rangeLabel }}</p>

          <!-- ── Escenario 7: filtros sin resultados ── -->
          <div v-if="filtered.length === 0" class="state-card state-empty">
            <div class="state-icon">🔍</div>
            <h2 class="state-title">No hay actividades que coincidan con los filtros aplicados</h2>
            <p class="state-desc">Probá con otros términos o limpiá los filtros.</p>
          </div>

          <!-- ── Tabla (Escenarios 1, 4, 5, 6) ── -->
          <div v-else class="table-wrapper">
            <table class="activities-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Descripción</th>
                  <th>Estado</th>
                  <th class="th-actions">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="activity in paginated" :key="activity.id">
                  <td class="td-name">{{ activity.name }}</td>
                  <td class="td-desc">{{ activity.description || '—' }}</td>
                  <td>
                    <span :class="['status-badge', activity.is_active ? 'badge-active' : 'badge-inactive']">
                      {{ activity.is_active ? 'Activa' : 'Inactiva' }}
                    </span>
                  </td>
                  <td class="td-actions">
                    <button
                      class="btn-edit"
                      @click="router.push({ name: 'editar-actividad', params: { id: activity.id } })"
                      title="Editar actividad"
                    >
                      Editar
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- ── Paginación ── -->
          <div v-if="totalPages > 1" class="pagination">
            <button
              class="page-btn"
              :disabled="currentPage === 1"
              @click="currentPage--"
            >
              ← Anterior
            </button>

            <button
              v-for="p in totalPages"
              :key="p"
              class="page-btn"
              :class="{ 'page-btn--active': p === currentPage }"
              @click="currentPage = p"
            >
              {{ p }}
            </button>

            <button
              class="page-btn"
              :disabled="currentPage === totalPages"
              @click="currentPage++"
            >
              Siguiente →
            </button>
          </div>

        </template>
      </template>

      <CreateActivityModal
        :visible="isCreateActivityVisible"
        :loading="isCreatingActivity"
        @close="closeCreateActivityModal"
        @submit="handleCreateActivity"
      />

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
  margin-bottom: 1.75rem;
  flex-wrap: wrap;
}

.page-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.2rem 0;
}

.page-subtitle {
  color: #6b7280;
  font-size: 0.88rem;
  margin: 0;
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
  margin-bottom: 1rem;
}

.alert-error {
  background-color: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.alert-icon {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
}

.error-icon {
  background-color: #dc2626;
  color: white;
}

.alert-close {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 1.4rem;
  line-height: 1;
  cursor: pointer;
  color: inherit;
  opacity: 0.5;
  padding: 0 0.2rem;
  flex-shrink: 0;
  transition: opacity 0.15s;
}

.alert-close:hover {
  opacity: 1;
}

/* ── Botones ── */

.btn-primary {
  background-color: #11998e;
  color: white;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.6rem 1.25rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.15s;
  align-self: center;
}

.btn-primary:hover { background-color: #0c8a70; }

.btn-secondary {
  background-color: #f3f4f6;
  color: #374151;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.6rem 1.4rem;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-secondary:hover { background-color: #e5e7eb; }

.btn-clear {
  align-self: flex-end;
  background: none;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0.48rem 1rem;
  font-size: 0.82rem;
  color: #6b7280;
  cursor: pointer;
  transition: background-color 0.15s, color 0.15s;
  white-space: nowrap;
}

.btn-clear:hover { background-color: #f3f4f6; color: #374151; }

/* ── Estados ── */

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

.state-forbidden { background-color: #fff7ed; border: 1px solid #fed7aa; }
.state-error     { background-color: #fff5f5; border: 1px solid #fecaca; }
.state-empty     { background-color: #f9fafb; border: 1px solid #e5e7eb; }

.state-icon  { font-size: 2.5rem; line-height: 1; }

.state-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #374151;
  margin: 0;
}

.state-forbidden .state-title { color: #9a3412; }
.state-error .state-title     { color: #991b1b; }

.state-desc {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
  max-width: 400px;
}

.state-forbidden .state-desc { color: #7c2d12; }
.state-error .state-desc     { color: #7f1d1d; }

/* ── Filtros ── */

.filters-bar {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 1rem 1.25rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  flex: 1;
  min-width: 160px;
}

.filter-label {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #6b7280;
}

.filter-input,
.filter-select {
  border: 1px solid #d1d5db;
  border-radius: 7px;
  padding: 0.48rem 0.75rem;
  font-size: 0.88rem;
  color: #1f2937;
  background: white;
  outline: none;
  transition: border-color 0.15s;
}

.filter-input:focus,
.filter-select:focus {
  border-color: #11998e;
  box-shadow: 0 0 0 3px rgba(17,153,142,0.12);
}

/* ── Contador ── */

.range-label {
  font-size: 0.82rem;
  color: #6b7280;
  margin: 0 0 0.75rem 0;
}

/* ── Tabla ── */

.table-wrapper {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

.activities-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.activities-table thead tr {
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.activities-table th {
  padding: 0.75rem 1.25rem;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #6b7280;
}

.activities-table tbody tr {
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.1s;
}

.activities-table tbody tr:last-child {
  border-bottom: none;
}

.activities-table tbody tr:hover {
  background-color: #f9fafb;
}

.activities-table td {
  padding: 0.9rem 1.25rem;
  color: #374151;
  vertical-align: middle;
}

.td-name {
  font-weight: 600;
  color: #1f2937;
  min-width: 140px;
}

.td-desc {
  color: #6b7280;
  max-width: 380px;
}

.th-actions,
.td-actions {
  width: 100px;
  text-align: center;
}

.btn-edit {
  background-color: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
  border-radius: 7px;
  padding: 0.35rem 0.85rem;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s, border-color 0.15s;
  white-space: nowrap;
}

.btn-edit:hover {
  background-color: #dbeafe;
  border-color: #93c5fd;
}

/* ── Badge de estado ── */

.status-badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  white-space: nowrap;
}

.badge-active   { background-color: #dcfce7; color: #15803d; }
.badge-inactive { background-color: #f3f4f6; color: #6b7280; }

/* ── Paginación ── */

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.4rem;
  margin-top: 1.25rem;
  flex-wrap: wrap;
}

.page-btn {
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 7px;
  padding: 0.45rem 0.9rem;
  font-size: 0.85rem;
  color: #374151;
  cursor: pointer;
  transition: background-color 0.15s, border-color 0.15s;
  font-weight: 500;
}

.page-btn:hover:not(:disabled) {
  background-color: #f3f4f6;
  border-color: #9ca3af;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-btn--active {
  background-color: #11998e;
  border-color: #11998e;
  color: white;
  font-weight: 700;
}

.page-btn--active:hover {
  background-color: #0c8a70 !important;
}

/* ── Skeletons ── */

.filters-skeleton {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.sk-input, .sk-select {
  height: 38px;
  border-radius: 7px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.sk-input  { flex: 1; min-width: 160px; }
.sk-select { width: 140px; }

.table-skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.sk-row {
  height: 52px;
  border-radius: 8px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Responsive ── */

@media (max-width: 640px) {
  .page-header { flex-direction: column; align-items: flex-start; }
  .btn-primary { align-self: flex-start; }
  .filters-bar { padding: 0.75rem; }
  .filter-group { min-width: 100%; }
  .td-desc { display: none; }
}
</style>
