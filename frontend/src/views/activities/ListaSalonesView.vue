<script setup lang="ts">
/**
 * ListaSalonesView — Gestión de salones del centro
 * ---------------------------------------------------
 * El admin da de alta los salones (nombre + capacidad física) que luego se
 * eligen al programar un turno. Empleado puede consultar el listado pero no
 * puede crear ni editar (guard de rol en el router: solo admin).
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import SalonModal from '@/components/SalonModal.vue'
import {
  getSalonesAll,
  createSalon,
  updateSalon,
  extractBackendError,
  type Salon,
} from '@/services/sessionService'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const authStore = useAuthStore()

// ─── Guard de rol ─────────────────────────────────────────────────────────────

const isAdmin = computed(() => {
  const u = authStore.user
  if (!u) return true
  return u.role === 'admin' || u.roles?.includes('admin') || u.role === 'Administrador'
})

// ─── Estado ───────────────────────────────────────────────────────────────────

const salones     = ref<Salon[]>([])
const isLoading    = ref(true)
const loadError    = ref('')
const formError    = ref('')
const isModalVisible = ref(false)
const isSaving     = ref(false)
const editingSalon = ref<Salon | null>(null)

// ─── Filtros ──────────────────────────────────────────────────────────────────

const filterName   = ref('')
const filterStatus = ref<'' | 'active' | 'inactive'>('')

const filtered = computed(() => {
  let list = salones.value

  if (filterName.value.trim()) {
    const q = filterName.value.trim().toLowerCase()
    list = list.filter(s => s.name.toLowerCase().includes(q))
  }

  if (filterStatus.value === 'active')   list = list.filter(s =>  s.is_active)
  if (filterStatus.value === 'inactive') list = list.filter(s => !s.is_active)

  return list
})

function openCreateModal() {
  editingSalon.value = null
  formError.value = ''
  isModalVisible.value = true
}

function openEditModal(salon: Salon) {
  editingSalon.value = salon
  formError.value = ''
  isModalVisible.value = true
}

function closeModal() {
  isModalVisible.value = false
  formError.value = ''
}

async function refreshSalones() {
  salones.value = await getSalonesAll()
}

async function handleSubmit(payload: { name: string; capacity: number }) {
  isSaving.value = true
  formError.value = ''

  try {
    if (editingSalon.value) {
      await updateSalon(editingSalon.value.id, payload)
    } else {
      await createSalon(payload)
    }
    await refreshSalones()
    closeModal()
  } catch (error) {
    formError.value = extractBackendError(error)
  } finally {
    isSaving.value = false
  }
}

// ─── Carga inicial ────────────────────────────────────────────────────────────

onMounted(async () => {
  if (!isAdmin.value) { isLoading.value = false; return }
  try {
    salones.value = await getSalonesAll()
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

      <div class="page-header">
        <div>
          <h1 class="page-title">Salones</h1>
          <p class="page-subtitle">Gestión de los salones físicos del centro</p>
        </div>
        <button class="btn-primary" @click="openCreateModal">
          + Crear nuevo salón
        </button>
      </div>


      <div v-if="!isAdmin || loadError === '__forbidden__'" class="state-card state-forbidden">
        <div class="state-icon">⛔</div>
        <h2 class="state-title">No tiene permisos para acceder a esta sección</h2>
        <p class="state-desc">Esta sección es exclusiva para administradores.</p>
        <button class="btn-secondary" @click="router.push({ name: 'home' })">Volver al inicio</button>
      </div>

      <div v-else-if="loadError" class="state-card state-error">
        <div class="state-icon">⚠</div>
        <h2 class="state-title">Error al cargar los salones</h2>
        <p class="state-desc">{{ loadError }}</p>
        <button class="btn-secondary" @click="router.go(0)">Reintentar</button>
      </div>

      <template v-else-if="isLoading">
        <div class="table-skeleton">
          <div v-for="i in 4" :key="i" class="sk-row"></div>
        </div>
      </template>

      <template v-else>

        <div v-if="salones.length === 0" class="state-card state-empty">
          <div class="state-icon">🏢</div>
          <h2 class="state-title">No hay salones cargados en el sistema</h2>
          <p class="state-desc">Creá el primer salón usando el botón de arriba.</p>
        </div>

        <template v-else>

          <div class="filters-bar">
            <div class="filter-group">
              <label class="filter-label" for="filter-name">Nombre</label>
              <input
                id="filter-name"
                v-model="filterName"
                type="text"
                class="filter-input"
                placeholder="Buscar por nombre..."
              />
            </div>

            <button
              v-if="filterName"
              class="btn-clear"
              @click="filterName = ''"
            >
              Limpiar filtros
            </button>
          </div>

          <div v-if="filtered.length === 0" class="state-card state-empty">
            <div class="state-icon">🔍</div>
            <h2 class="state-title">No hay salones que coincidan con los filtros aplicados</h2>
            <p class="state-desc">Probá con otros términos o limpiá los filtros.</p>
          </div>

          <div v-else class="table-wrapper">
            <table class="salones-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Capacidad física</th>
                  <th class="th-actions">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="salon in filtered" :key="salon.id">
                  <td class="td-name">{{ salon.name }}</td>
                  <td>{{ salon.capacity }}</td>
                  <td class="td-actions">
                    <button class="btn-edit" @click="openEditModal(salon)" title="Editar salón">
                      Editar
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

        </template>
      </template>

      <SalonModal
        :visible="isModalVisible"
        :loading="isSaving"
        :salon="editingSalon"
        :server-error="formError"
        @close="closeModal"
        @submit="handleSubmit"
      />

    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper { width: 100%; }

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

.error-icon { background-color: #dc2626; color: white; }

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
}

.alert-close:hover { opacity: 1; }

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
  white-space: nowrap;
}

.btn-clear:hover { background-color: #f3f4f6; color: #374151; }

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

.filters-bar {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  margin-bottom: 1rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  max-width: 540px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  width: 220px;
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
}

.filter-input:focus,
.filter-select:focus {
  border-color: #11998e;
  box-shadow: 0 0 0 3px rgba(17,153,142,0.12);
}

.table-wrapper {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  max-width: 540px;
}

.salones-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.salones-table thead tr {
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.salones-table th {
  padding: 0.75rem 1.25rem;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #6b7280;
}

.salones-table tbody tr {
  border-bottom: 1px solid #f3f4f6;
}

.salones-table tbody tr:last-child { border-bottom: none; }
.salones-table tbody tr:hover { background-color: #f9fafb; }

.salones-table td {
  padding: 0.9rem 1.25rem;
  color: #374151;
  vertical-align: middle;
}

.td-name { font-weight: 600; color: #1f2937; min-width: 140px; }

.th-actions,
.td-actions { width: 100px; text-align: center; }

.btn-edit {
  background-color: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
  border-radius: 7px;
  padding: 0.35rem 0.85rem;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.btn-edit:hover { background-color: #dbeafe; border-color: #93c5fd; }

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

@media (max-width: 640px) {
  .page-header { flex-direction: column; align-items: flex-start; }
  .btn-primary { align-self: flex-start; }
  .filters-bar { padding: 0.75rem; }
  .filter-group { min-width: 100%; }
}
</style>
