<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import {
  getClienteById,
  getSubscripcionesByCliente,
  getSingleEnrollmentsByCliente,
  type Cliente,
  type ClienteSubscripcion,
  type ClienteSingleEnrollment,
} from '@/services/clientesService'
import { extractBackendError } from '@/services/sessionService'

interface InscripcionRow {
  id: string
  actividad: string
  horario: string
  tipo: 'Turno Fijo' | 'Clase Individual'
  instructor: string
  estado: string
  detalle: string
}

const route = useRoute()
const clienteId = Number(route.params.clienteId)

const cliente = ref<Cliente | null>(null)
const allInscripciones = ref<InscripcionRow[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const filterActividad = ref('')
const filtroTipo = ref('')

function formatTime(t: string): string {
  return t.padStart(5, '0')
}

function mapSubscripcion(s: ClienteSubscripcion): InscripcionRow {
  const horario = `${formatTime(s.start_time)} – ${formatTime(s.end_time)}`
  const dias = s.days.join(', ')
  return {
    id: `sub-${s.subscription_id}`,
    actividad: s.activity_name,
    horario: `${horario} (${dias})`,
    tipo: 'Turno Fijo',
    instructor: s.instructor,
    estado: s.status,
    detalle: s.turno_description,
  }
}

function mapSingle(e: ClienteSingleEnrollment): InscripcionRow {
  const horario = `${formatTime(e.start_time)} – ${formatTime(e.end_time)}`
  return {
    id: `single-${e.enrollment_id}`,
    actividad: e.activity_name,
    horario: `${horario} (${e.clase_date})`,
    tipo: 'Clase Individual',
    instructor: e.instructor,
    estado: e.status,
    detalle: e.turno_description,
  }
}

onMounted(async () => {
  try {
    const [c, subs, singles] = await Promise.all([
      getClienteById(clienteId),
      getSubscripcionesByCliente(clienteId),
      getSingleEnrollmentsByCliente(clienteId),
    ])
    cliente.value = c
    allInscripciones.value = [
      ...subs.map(mapSubscripcion),
      ...singles.map(mapSingle),
    ]
  } catch (err) {
    error.value = extractBackendError(err) ?? 'No se pudo cargar el listado de inscripciones.'
  } finally {
    loading.value = false
  }
})

const actividadOptions = computed(() => {
  const set = new Set(allInscripciones.value.map(i => i.actividad))
  return Array.from(set).sort()
})

const filteredInscripciones = computed(() => {
  return allInscripciones.value.filter(i => {
    if (filterActividad.value && i.actividad !== filterActividad.value) return false
    if (filtroTipo.value && i.tipo !== filtroTipo.value) return false
    return true
  })
})

const hasFilters = computed(() => !!filterActividad.value || !!filtroTipo.value)

const resumen = computed(() => {
  const total = filteredInscripciones.value.length
  if (total === 0) return null
  return `El cliente registra ${total} inscripción${total === 1 ? ' activa' : 'es activas'} con los filtros aplicados.`
})

function limpiarFiltros() {
  filterActividad.value = ''
  filtroTipo.value = ''
}

function estadoLabel(estado: string): string {
  const map: Record<string, string> = {
    active: 'Activa',
    pending: 'Pendiente',
    cancelled: 'Cancelada',
    scheduled_cancellation: 'Baja prog.',
    confirmed: 'Confirmada',
    deposit_paid: 'Seña pagada',
  }
  return map[estado] ?? estado
}

function estadoClass(estado: string): string {
  if (['active', 'confirmed', 'deposit_paid'].includes(estado)) return 'badge-active'
  if (estado === 'pending') return 'badge-pending'
  return 'badge-cancelled'
}
</script>

<template>
  <AdminLayout>
    <div class="inscripciones-page">
      <header class="page-header">
        <RouterLink :to="`/clientes/${clienteId}`" class="back-link">← Volver a la ficha</RouterLink>
        <div class="header-row">
          <h1 class="page-title">
            Inscripciones activas
            <span v-if="cliente" class="cliente-badge">
              {{ cliente.first_name }} {{ cliente.last_name }}
            </span>
          </h1>
        </div>
      </header>

      <div v-if="loading" class="state-box">
        <p class="state-text">Cargando inscripciones...</p>
      </div>

      <div v-else-if="error" class="state-box error-box">
        <p class="state-text">{{ error }}</p>
      </div>

      <template v-else>
        <div v-if="allInscripciones.length === 0" class="state-box">
          <p class="state-text">El cliente no registra inscripciones actualmente.</p>
        </div>

        <template v-else>
          <div class="filters-card">
            <div class="filters-row">
              <div class="filter-field">
                <label class="filter-label" for="filtro-actividad">Actividad</label>
                <select id="filtro-actividad" v-model="filterActividad" class="filter-select">
                  <option value="">Todas</option>
                  <option v-for="act in actividadOptions" :key="act" :value="act">{{ act }}</option>
                </select>
              </div>

              <div class="filter-field">
                <label class="filter-label" for="filtro-tipo">Tipo de inscripción</label>
                <select id="filtro-tipo" v-model="filtroTipo" class="filter-select">
                  <option value="">Todos</option>
                  <option value="Turno Fijo">Turno Fijo</option>
                  <option value="Clase Individual">Clase Individual</option>
                </select>
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

          <div v-if="resumen" class="resumen-banner">
            {{ resumen }}
          </div>

          <div v-if="filteredInscripciones.length === 0" class="state-box">
            <p class="state-text">No hay inscripciones que coincidan con los filtros aplicados.</p>
          </div>

          <div v-else class="table-wrapper">
            <table class="inscripciones-table">
              <thead>
                <tr>
                  <th>Actividad</th>
                  <th>Tipo</th>
                  <th>Horario</th>
                  <th>Instructor</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in filteredInscripciones" :key="item.id">
                  <td class="actividad-cell">
                    {{ item.actividad }}
                    <span class="detalle-text">{{ item.detalle }}</span>
                  </td>
                  <td>
                    <span :class="['tipo-badge', item.tipo === 'Turno Fijo' ? 'badge-turno' : 'badge-clase']">
                      {{ item.tipo }}
                    </span>
                  </td>
                  <td class="horario-cell">{{ item.horario }}</td>
                  <td class="instructor-cell">{{ item.instructor }}</td>
                  <td>
                    <span :class="['estado-badge', estadoClass(item.estado)]">
                      {{ estadoLabel(item.estado) }}
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
.inscripciones-page {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header { margin-bottom: 1.75rem; }

.back-link {
  display: inline-block;
  color: #6b7280;
  text-decoration: none;
  font-size: 0.88rem;
  margin-bottom: 0.75rem;
  transition: color 0.15s;
}
.back-link:hover { color: #0d9b8a; }

.header-row { display: flex; align-items: baseline; gap: 1rem; flex-wrap: wrap; }

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

.cliente-badge { font-size: 1rem; font-weight: 500; color: #6b7280; }

.state-box {
  background: white;
  border-radius: 16px;
  padding: 2.5rem;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border: 1px solid #f3f4f6;
}
.error-box { border-color: #fecaca; background: #fff5f5; }
.state-text { margin: 0; color: #6b7280; font-size: 0.98rem; }
.error-box .state-text { color: #dc2626; }

.filters-card {
  background: white;
  border-radius: 14px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border: 1px solid #f3f4f6;
}
.filters-row { display: flex; align-items: flex-end; gap: 1rem; flex-wrap: wrap; }
.filter-field { display: flex; flex-direction: column; gap: 0.35rem; min-width: 180px; }
.filter-label { font-size: 0.78rem; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }

.filter-select {
  height: 38px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0 0.75rem;
  font-size: 0.9rem;
  color: #374151;
  background: white;
  outline: none;
  width: 100%;
}
.filter-select:focus { border-color: #0d9b8a; }

.clear-btn {
  height: 38px;
  padding: 0 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  color: #6b7280;
  font-size: 0.88rem;
  cursor: pointer;
  align-self: flex-end;
}
.clear-btn:hover { border-color: #0d9b8a; color: #0d9b8a; }

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

.table-wrapper {
  background: white;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border: 1px solid #f3f4f6;
}
.inscripciones-table { width: 100%; border-collapse: collapse; }
.inscripciones-table th {
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
.inscripciones-table td {
  padding: 0.9rem 1.25rem;
  font-size: 0.92rem;
  color: #374151;
  border-bottom: 1px solid #f9fafb;
  vertical-align: middle;
}
.inscripciones-table tbody tr:last-child td { border-bottom: none; }
.inscripciones-table tbody tr:hover td { background: #f9fafb; }

.actividad-cell { font-weight: 600; color: #111827; }
.detalle-text {
  display: block;
  font-size: 0.8rem;
  font-weight: 400;
  color: #9ca3af;
  margin-top: 2px;
}
.horario-cell { white-space: nowrap; color: #374151; font-weight: 500; font-size: 0.87rem; }
.instructor-cell { color: #6b7280; }

.tipo-badge {
  display: inline-block;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
}
.tipo-badge.badge-turno { background: #d1fae5; color: #065f46; }
.tipo-badge.badge-clase { background: #e0f2fe; color: #0369a1; }

.estado-badge {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}
.badge-active { background: #d1fae5; color: #065f46; }
.badge-pending { background: #fef3c7; color: #92400e; }
.badge-cancelled { background: #f3f4f6; color: #6b7280; }
</style>
