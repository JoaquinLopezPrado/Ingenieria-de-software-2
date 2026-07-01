<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'

interface Pago {
  id: number
  fecha: string        // YYYY-MM-DD
  concepto: string
  monto: number
  estado: 'pagado' | 'pendiente' | 'vencido'
}

const route  = useRoute()
const router = useRouter()

const clienteId = computed(() => Number(route.params.clienteId))

const pagos      = ref<Pago[]>([])
const isLoading  = ref(true)
const errorMsg   = ref('')

// ── Mock temporal — reemplazar por llamada al backend cuando exista el endpoint ──
async function cargarPagos() {
  isLoading.value = true
  errorMsg.value  = ''
  try {
    await new Promise((res) => setTimeout(res, 400)) // simula latencia

    pagos.value = [
      { id: 1, fecha: '2026-06-01', concepto: 'Cuota mensual - Junio', monto: 15000, estado: 'pagado' },
      { id: 2, fecha: '2026-05-01', concepto: 'Cuota mensual - Mayo',  monto: 15000, estado: 'pagado' },
      { id: 3, fecha: '2026-07-01', concepto: 'Cuota mensual - Julio', monto: 15000, estado: 'pendiente' },
    ]
    // TODO: cuando el endpoint exista, reemplazar por:
    // const { data } = await api.get(`/clientes/${clienteId.value}/pagos`)
    // pagos.value = data
  } catch (err) {
    errorMsg.value = 'No se pudo cargar el historial de pagos.'
    pagos.value = []
  } finally {
    isLoading.value = false
  }
}

function fmtARS(n: number) {
  return '$' + n.toLocaleString('es-AR')
}

function estadoLabel(estado: Pago['estado']) {
  return { pagado: 'Pagado', pendiente: 'Pendiente', vencido: 'Vencido' }[estado]
}

function volver() { router.back() }

onMounted(cargarPagos)
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <div class="page-header">
        <div>
          <h1 class="page-title">Pagos del cliente</h1>
          <p class="page-subtitle">Historial de pagos y estado de cuenta</p>
        </div>
        <button class="btn-volver" type="button" @click="volver">← Volver</button>
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
        <table class="pagos-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Concepto</th>
              <th>Monto</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="pago in pagos" :key="pago.id">
              <td>{{ pago.fecha }}</td>
              <td>{{ pago.concepto }}</td>
              <td>{{ fmtARS(pago.monto) }}</td>
              <td>
                <span class="badge" :class="`badge-${pago.estado}`">
                  {{ estadoLabel(pago.estado) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
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
.page-title { font-size: 1.6rem; font-weight: 700; color: #0d3027; margin: 0 0 0.25rem; }
.page-subtitle { color: #8fa8a2; font-size: 0.88rem; margin: 0; }

.btn-volver {
  background: #0d3027; color: white; border: none; border-radius: 10px;
  padding: 10px 16px; font-size: 13px; font-weight: 600; cursor: pointer;
  transition: 0.15s;
}
.btn-volver:hover { background: #11998e; }

.state-card {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 0.75rem; padding: 3.5rem 2rem; border-radius: 12px; text-align: center;
  background: #f6faf9; border: 1.5px solid #e5e9e8;
}
.state-error { background: #fff5f5; border-color: #fecaca; }
.state-icon { font-size: 2rem; }
.state-desc { color: #6b7280; font-size: 0.9rem; margin: 0; }

.spinner {
  width: 20px; height: 20px; border: 2px solid #e5e9e8; border-top-color: #11998e;
  border-radius: 50%; animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.btn-secondary {
  background: #f3f4f6; color: #374151; font-size: 0.85rem; font-weight: 600;
  padding: 0.5rem 1.1rem; border-radius: 8px; border: 1px solid #d1d5db; cursor: pointer;
}

.table-container { background: white; border-radius: 12px; border: 1px solid #e5e7eb; overflow: hidden; }
.pagos-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.pagos-table thead { background: #f9fafb; border-bottom: 1px solid #e5e7eb; }
.pagos-table th {
  padding: 0.85rem 1rem; text-align: left; font-size: 0.72rem; font-weight: 700;
  color: #6b7280; text-transform: uppercase; letter-spacing: 0.06em;
}
.pagos-table td { padding: 0.9rem 1rem; color: #374151; border-bottom: 1px solid #f3f4f6; }
.pagos-table tbody tr:last-child td { border-bottom: none; }

.badge {
  display: inline-block; padding: 0.2rem 0.6rem; border-radius: 20px;
  font-size: 0.75rem; font-weight: 600;
}
.badge-pagado    { background: #d1fae5; color: #047857; }
.badge-pendiente { background: #fef3c7; color: #92400e; }
.badge-vencido   { background: #fee2e2; color: #b91c1c; }
</style>