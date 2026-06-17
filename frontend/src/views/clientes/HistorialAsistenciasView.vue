<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { getHistorialAsistencias, type RegistroAsistencia } from '@/services/asistenciasService'
import { getClienteById, type Cliente } from '@/services/clientesService'
import { extractBackendError } from '@/services/sessionService'

const route = useRoute()
const clienteId = Number(route.params.clienteId)

// ─── Estado ──────────────────────────────────────────────────────────────────

const cliente = ref<Cliente | null>(null)
const allRegistros = ref<RegistroAsistencia[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// ─── Filtros ─────────────────────────────────────────────────────────────────

const filtroActividad = ref('')
const filtroDesde = ref('')
const filtroHasta = ref('')

// ─── Carga ────────────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    const [c, registros] = await Promise.all([
      getClienteById(clienteId),
      getHistorialAsistencias(clienteId),
    ])
    cliente.value = c
    allRegistros.value = registros
  } catch (err) {
    error.value = extractBackendError(err) ?? 'No se pudo cargar el historial de asistencias.'
  } finally {
    loading.value = false
  }
})

// ─── Computed ─────────────────────────────────────────────────────────────────

const actividadOptions = computed(() => {
  const set = new Set(allRegistros.value.map(r => r.actividad))
  return Array.from(set).sort()
})

const filteredRegistros = computed(() => {
  return allRegistros.value.filter(r => {
    if (filtroActividad.value && r.actividad !== filtroActividad.value) return false
    if (filtroDesde.value && r.fecha < filtroDesde.value) return false
    if (filtroHasta.value && r.fecha > filtroHasta.value) return false
    return true
  })
})

const hasFilters = computed(
  () => !!filtroActividad.value || !!filtroDesde.value || !!filtroHasta.value,
)

const resumen = computed(() => {
  const total = filteredRegistros.value.length
  if (total === 0) return null
  const asistidas = filteredRegistros.value.filter(r => r.estado === 'presente').length
  const porcentaje = Math.round((asistidas / total) * 100)
  return `Asistió a ${asistidas} de ${total} clases (${porcentaje}%)`
})

// ─── Helpers ─────────────────────────────────────────────────────────────────

const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

function formatFecha(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number)
  return `${d} ${MESES[m - 1]}. ${y}`
}

function limpiarFiltros() {
  filtroActividad.value = ''
  filtroDesde.value = ''
  filtroHasta.value = ''
}
</script>

<template>
  <AdminLayout>
    <div class="historial-page">
      <header class="page-header">
        <RouterLink :to="`/clientes/${clienteId}`" class="back-link">← Volver a la ficha</RouterLink>
        <div class="header-row">
          <h1 class="page-title">
            Historial de asistencias
            <span v-if="cliente" class="cliente-badge">
              {{ cliente.first_name }} {{ cliente.last_name }}
            </span>
          </h1>
        </div>
      </header>

      <div v-if="loading" class="state-box">
        <p class="state-text">Cargando historial...</p>
      </div>

      <div v-else-if="error" class="state-box error-box">
        <p class="state-text">{{ error }}</p>
      </div>

      <template v-else>
        <!-- Sin ningún registro → vacío absoluto -->
        <div v-if="allRegistros.length === 0" class="state-box">
          <p class="state-text">El cliente no tiene asistencias registradas.</p>
        </div>

        <template v-else>
          <!-- Filtros -->
          <div class="filters-card">
            <div class="filters-row">
              <div class="filter-field">
                <label class="filter-label" for="filtro-actividad">Actividad</label>
                <select id="filtro-actividad" v-model="filtroActividad" class="filter-select">
                  <option value="">Todas</option>
                  <option v-for="act in actividadOptions" :key="act" :value="act">{{ act }}</option>
                </select>
              </div>

              <div class="filter-field">
                <label class="filter-label" for="filtro-desde">Desde</label>
                <input
                  id="filtro-desde"
                  type="date"
                  v-model="filtroDesde"
                  class="filter-input"
                />
              </div>

              <div class="filter-field">
                <label class="filter-label" for="filtro-hasta">Hasta</label>
                <input
                  id="filtro-hasta"
                  type="date"
                  v-model="filtroHasta"
                  class="filter-input"
                />
              </div>

              <button
                v-if="hasFilters"
                type="button"
                class="clear-btn"
                @click="limpiarFiltros"
              >
                Limpiar filtros
              </button>
            </div>
          </div>

          <!-- Resumen -->
          <div v-if="resumen" class="resumen-banner">
            {{ resumen }}
          </div>

          <!-- Filtros activos sin resultados -->
          <div v-if="filteredRegistros.length === 0" class="state-box">
            <p class="state-text">No hay asistencias que coincidan con los filtros aplicados.</p>
          </div>

          <!-- Tabla de registros -->
          <div v-else class="table-wrapper">
            <table class="asistencias-table">
              <thead>
                <tr>
                  <th>Actividad</th>
                  <th>Fecha</th>
                  <th>Horario</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in filteredRegistros" :key="r.id">
                  <td>{{ r.actividad }}</td>
                  <td>{{ formatFecha(r.fecha) }}</td>
                  <td class="horario-cell">{{ r.horario }}</td>
                  <td>
                    <span :class="['estado-chip', r.estado]">
                      {{ r.estado === 'presente' ? 'Presente' : 'Ausente' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </template>
    </div>
  </AdminLayout>
</template>

<style scoped>
.historial-page {
  max-width: 900px;
  margin: 0 auto;
}

/* ── Header ── */
.page-header {
  margin-bottom: 1.75rem;
}

.back-link {
  display: inline-block;
  color: #6b7280;
  text-decoration: none;
  font-size: 0.88rem;
  margin-bottom: 0.75rem;
  transition: color 0.15s;
}

.back-link:hover {
  color: #0d9b8a;
}

.header-row {
  display: flex;
  align-items: baseline;
  gap: 1rem;
  flex-wrap: wrap;
}

.page-title {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 700;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.cliente-badge {
  font-size: 1rem;
  font-weight: 500;
  color: #6b7280;
}

/* ── Estados vacíos / carga / error ── */
.state-box {
  background: white;
  border-radius: 16px;
  padding: 2.5rem;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border: 1px solid #f3f4f6;
}

.error-box {
  border-color: #fecaca;
  background: #fff5f5;
}

.state-text {
  margin: 0;
  color: #6b7280;
  font-size: 0.98rem;
}

.error-box .state-text {
  color: #dc2626;
}

/* ── Filtros ── */
.filters-card {
  background: white;
  border-radius: 14px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border: 1px solid #f3f4f6;
}

.filters-row {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  flex-wrap: wrap;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 150px;
}

.filter-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-select,
.filter-input {
  height: 38px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0 0.75rem;
  font-size: 0.9rem;
  color: #374151;
  background: white;
  outline: none;
  transition: border-color 0.15s;
}

.filter-select:focus,
.filter-input:focus {
  border-color: #0d9b8a;
}

.clear-btn {
  height: 38px;
  padding: 0 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  color: #6b7280;
  font-size: 0.88rem;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  align-self: flex-end;
}

.clear-btn:hover {
  border-color: #0d9b8a;
  color: #0d9b8a;
}

/* ── Resumen ── */
.resumen-banner {
  background: #f0fdf9;
  border: 1px solid #a7f3d0;
  border-radius: 12px;
  padding: 0.9rem 1.25rem;
  margin-bottom: 1.25rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: #065f46;
}

/* ── Tabla ── */
.table-wrapper {
  background: white;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border: 1px solid #f3f4f6;
}

.asistencias-table {
  width: 100%;
  border-collapse: collapse;
}

.asistencias-table th {
  background: #f9fafb;
  padding: 0.85rem 1.25rem;
  text-align: left;
  font-size: 0.78rem;
  font-weight: 700;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  border-bottom: 1px solid #f3f4f6;
}

.asistencias-table td {
  padding: 0.9rem 1.25rem;
  font-size: 0.92rem;
  color: #374151;
  border-bottom: 1px solid #f9fafb;
  vertical-align: middle;
}

.asistencias-table tbody tr:last-child td {
  border-bottom: none;
}

.asistencias-table tbody tr:hover td {
  background: #f9fafb;
}

.horario-cell {
  white-space: nowrap;
  color: #6b7280;
  font-size: 0.88rem;
}

/* ── Chips estado ── */
.estado-chip {
  display: inline-block;
  padding: 0.28rem 0.75rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: capitalize;
}

.estado-chip.presente {
  background: #d1fae5;
  color: #065f46;
}

.estado-chip.ausente {
  background: #fee2e2;
  color: #991b1b;
}
</style>
