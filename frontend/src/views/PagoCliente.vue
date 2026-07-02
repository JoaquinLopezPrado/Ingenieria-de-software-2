<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import api from '@/services/api'
import { extractBackendError } from '@/services/sessionService'

interface PagoItem {
  tipo: 'suscripcion' | 'clase_individual'
  fecha: string | null
  actividad: string
  monto: number
  estado: string
  periodo: string | null
}

const route  = useRoute()
const router = useRouter()

const clienteId = computed(() => Number(route.params.clienteId))

const pagos      = ref<PagoItem[]>([])
const isLoading  = ref(true)
const errorMsg   = ref('')

async function cargarPagos() {
  isLoading.value = true
  errorMsg.value  = ''
  try {
    const res = await api.get(`/users/${clienteId.value}/pagos`)
    pagos.value = res.data
  } catch (err) {
    errorMsg.value = extractBackendError(err) ?? 'No se pudo cargar el historial de pagos.'
    pagos.value = []
  } finally {
    isLoading.value = false
  }
}

function fmtARS(n: number) {
  return '$' + n.toLocaleString('es-AR')
}

function fmtFecha(f: string | null) {
  if (!f) return '—'
  const [y, m, d] = f.split('-')
  return `${d}/${m}/${y}`
}

const ESTADO_CLASS: Record<string, string> = {
  Pagado: 'badge-pagado',
  Confirmado: 'badge-pagado',
  Pendiente: 'badge-pendiente',
  Vencido: 'badge-vencido',
  'Seña pagada': 'badge-senia',
  'Seña perdida': 'badge-vencido',
  Cancelado: 'badge-cancelado',
  Reembolsado: 'badge-cancelado',
  Eximido: 'badge-cancelado',
}

function badgeClass(estado: string) {
  return ESTADO_CLASS[estado] ?? 'badge-cancelado'
}

onMounted(cargarPagos)
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <div class="page-header">
        <div>
          <h1 class="page-title">Pagos del cliente</h1>
          <p class="page-subtitle">Historial de cargos y clases individuales</p>
        </div>
        <button class="btn-volver" type="button" @click="router.back()">← Volver</button>
      </div>

      <div v-if="isLoading" class="state-card">
        <div class="spinner" />
        <span>Cargando pagos...</span>
      </div>

      <div v-else-if="errorMsg" class="state-card state-error">
        <div class="state-icon">⚠</div>
        <p class="state-desc">{{ errorMsg }}</p>
        <button class="btn-secondary" type="button" @click="cargarPagos">Reintentar</button>
      </div>

      <div v-else-if="!pagos.length" class="state-card state-empty">
        <div class="state-icon">◎</div>
        <p class="state-desc">Este cliente no tiene pagos registrados.</p>
      </div>

      <div v-else class="table-container">
        <div class="table-scroll">
          <table class="pagos-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Tipo</th>
                <th>Actividad</th>
                <th>Período</th>
                <th>Monto</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(pago, i) in pagos" :key="i">
                <td class="cell-fecha">{{ fmtFecha(pago.fecha) }}</td>
                <td>
                  <span class="tipo-badge" :class="pago.tipo === 'suscripcion' ? 'tipo-sus' : 'tipo-clase'">
                    {{ pago.tipo === 'suscripcion' ? 'Suscripción' : 'Clase suelta' }}
                  </span>
                </td>
                <td class="cell-actividad">{{ pago.actividad }}</td>
                <td class="cell-periodo">{{ pago.periodo ?? '—' }}</td>
                <td class="cell-monto">{{ fmtARS(pago.monto) }}</td>
                <td>
                  <span class="badge" :class="badgeClass(pago.estado)">
                    {{ pago.estado }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper { width: 100%; }

.page-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 1.5rem; gap: 1rem; flex-wrap: wrap;
}
.page-title { font-size: 1.6rem; font-weight: 700; color: #111827; margin: 0 0 0.25rem; }
.page-subtitle { color: #6b7280; font-size: 0.88rem; margin: 0; }

.btn-volver {
  background: #111827; color: white; border: none; border-radius: 10px;
  padding: 10px 16px; font-size: 13px; font-weight: 600; cursor: pointer;
  transition: background 0.15s;
}
.btn-volver:hover { background: #11998e; }

.state-card {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 0.75rem; padding: 3.5rem 2rem; border-radius: 12px; text-align: center;
  background: #f9fafb; border: 1.5px solid #e5e7eb;
}
.state-error { background: #fff5f5; border-color: #fecaca; }
.state-empty { border-style: dashed; }
.state-icon { font-size: 2rem; }
.state-desc { color: #6b7280; font-size: 0.9rem; margin: 0; }

.spinner {
  width: 20px; height: 20px; border: 2px solid #e5e7eb; border-top-color: #11998e;
  border-radius: 50%; animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.btn-secondary {
  background: #f3f4f6; color: #374151; font-size: 0.85rem; font-weight: 600;
  padding: 0.5rem 1.1rem; border-radius: 8px; border: 1px solid #d1d5db; cursor: pointer;
}

.table-container {
  background: white; border-radius: 12px; border: 1px solid #e5e7eb; overflow: hidden;
}
.table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
.pagos-table { width: 100%; min-width: 700px; border-collapse: collapse; font-size: 0.875rem; }
.pagos-table thead { background: #f9fafb; border-bottom: 1px solid #e5e7eb; }
.pagos-table th {
  padding: 0.85rem 1rem; text-align: left; font-size: 0.72rem; font-weight: 700;
  color: #6b7280; text-transform: uppercase; letter-spacing: 0.06em; white-space: nowrap;
}
.pagos-table td { padding: 0.9rem 1rem; color: #374151; border-bottom: 1px solid #f3f4f6; vertical-align: middle; }
.pagos-table tbody tr:last-child td { border-bottom: none; }

.cell-fecha { white-space: nowrap; color: #6b7280; font-size: 0.85rem; }
.cell-actividad { max-width: 240px; }
.cell-periodo { white-space: nowrap; color: #6b7280; font-size: 0.85rem; }
.cell-monto { white-space: nowrap; font-weight: 600; }

.tipo-badge {
  display: inline-block; padding: 0.2rem 0.55rem; border-radius: 20px;
  font-size: 0.72rem; font-weight: 700; white-space: nowrap;
}
.tipo-sus   { background: #eff6ff; color: #1d4ed8; }
.tipo-clase { background: #faf5ff; color: #7c3aed; }

.badge {
  display: inline-block; padding: 0.2rem 0.6rem; border-radius: 20px;
  font-size: 0.75rem; font-weight: 600; white-space: nowrap;
}
.badge-pagado    { background: #d1fae5; color: #047857; }
.badge-pendiente { background: #fef3c7; color: #92400e; }
.badge-vencido   { background: #fee2e2; color: #b91c1c; }
.badge-senia     { background: #e0f2fe; color: #0369a1; }
.badge-cancelado { background: #f3f4f6; color: #6b7280; }
</style>
