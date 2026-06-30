<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import {
  adminGenerateNextMonthCharges,
  adminGetPendingCharges,
  adminCashConfirmCharge,
  type GenerateChargesResponse,
  type AdminPendingCharge,
} from '@/services/subscriptionService'
import { extractBackendError } from '@/services/sessionService'

const _MESES = [
  '', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

const today = new Date()
const nextMonth = today.getMonth() === 11 ? 1 : today.getMonth() + 2
const nextYear = today.getMonth() === 11 ? today.getFullYear() + 1 : today.getFullYear()

// — Generar cargos —
const loadingGenerar = ref(false)
const errorGenerar = ref<string | null>(null)
const resultGenerar = ref<GenerateChargesResponse | null>(null)

async function handleGenerar() {
  if (loadingGenerar.value) return
  loadingGenerar.value = true
  errorGenerar.value = null
  resultGenerar.value = null
  try {
    resultGenerar.value = await adminGenerateNextMonthCharges()
    await cargarPendientes()
  } catch (e) {
    errorGenerar.value = extractBackendError(e)
  } finally {
    loadingGenerar.value = false
  }
}

// — Cuotas pendientes —
const pendientes = ref<AdminPendingCharge[]>([])
const loadingPendientes = ref(false)
const confirmandoId = ref<number | null>(null)
const errorCobro = ref<string | null>(null)

async function cargarPendientes() {
  loadingPendientes.value = true
  try {
    pendientes.value = await adminGetPendingCharges()
  } finally {
    loadingPendientes.value = false
  }
}

async function handleCobrarEfectivo(charge: AdminPendingCharge) {
  confirmandoId.value = charge.charge_id
  errorCobro.value = null
  try {
    await adminCashConfirmCharge(charge.charge_id)
    pendientes.value = pendientes.value.filter(c => c.charge_id !== charge.charge_id)
  } catch (e) {
    errorCobro.value = extractBackendError(e)
  } finally {
    confirmandoId.value = null
  }
}

function formatPeriodo(month: number, year: number) {
  return `${_MESES[month]} ${year}`
}

function formatMonto(amount: number) {
  return `$ ${Number(amount).toLocaleString('es-AR', { minimumFractionDigits: 2 })}`
}

onMounted(cargarPendientes)
</script>

<template>
  <AdminLayout>
    <section class="suscripciones-admin">
      <div class="page-header">
        <h1>Gestión de suscripciones</h1>
        <p class="subtitle">Generá los cargos del mes próximo y registrá pagos en efectivo.</p>
      </div>

      <!-- Generar cargos -->
      <div class="card">
        <div class="card-header">
          <h2>Cuotas de {{ _MESES[nextMonth] }} {{ nextYear }}</h2>
          <p class="card-description">
            Al confirmar, se generará el cargo de <strong>{{ _MESES[nextMonth] }} {{ nextYear }}</strong>
            para todos los clientes con suscripción activa que aún no lo tengan,
            y se les enviará un mail de recordatorio.
          </p>
        </div>

        <div v-if="errorGenerar" class="alert alert-error">
          <span class="alert-icon">!</span> {{ errorGenerar }}
        </div>
        <div v-if="resultGenerar" class="alert alert-success">
          <span class="alert-icon">✓</span>
          <span v-if="resultGenerar.charges_created > 0">
            Se generaron <strong>{{ resultGenerar.charges_created }}</strong> cargo(s) y se enviaron los mails.
          </span>
          <span v-else>
            No había cargos pendientes de generar para {{ _MESES[resultGenerar.period_month] }} {{ resultGenerar.period_year }}.
          </span>
        </div>

        <div class="card-actions">
          <button class="btn btn-primary" :disabled="loadingGenerar" @click="handleGenerar">
            <span v-if="loadingGenerar" class="spinner" />
            <span v-else>Generar cargos y notificar</span>
          </button>
        </div>
      </div>

      <!-- Cuotas pendientes de cobro -->
      <div class="card">
        <div class="card-header">
          <h2>Cuotas pendientes de pago</h2>
          <p class="card-description">Registrá el pago en efectivo cuando el cliente se acerque al gimnasio.</p>
        </div>

        <div v-if="errorCobro" class="alert alert-error">
          <span class="alert-icon">!</span> {{ errorCobro }}
        </div>

        <div v-if="loadingPendientes" class="empty-state">Cargando...</div>
        <div v-else-if="pendientes.length === 0" class="empty-state">
          No hay cuotas pendientes de pago.
        </div>
        <table v-else class="tabla-pendientes">
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Actividad / Turno</th>
              <th>Período</th>
              <th>Monto</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in pendientes" :key="c.charge_id">
              <td>
                <div class="cliente-nombre">{{ c.first_name }} {{ c.last_name }}</div>
                <div class="cliente-email">{{ c.email }}</div>
              </td>
              <td>
                <div class="actividad-nombre">{{ c.activity_name }}</div>
                <div class="turno-desc">{{ c.turno_description }}</div>
              </td>
              <td class="periodo-cell">{{ formatPeriodo(c.period_month, c.period_year) }}</td>
              <td class="monto-cell">{{ formatMonto(c.amount) }}</td>
              <td class="accion-cell">
                <button
                  class="btn btn-cobrar"
                  :disabled="confirmandoId === c.charge_id"
                  @click="handleCobrarEfectivo(c)"
                >
                  <span v-if="confirmandoId === c.charge_id" class="spinner spinner--dark" />
                  <span v-else>Cobrar en efectivo</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </AdminLayout>
</template>

<style scoped>
.suscripciones-admin {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.page-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #111;
  margin: 0 0 0.25rem;
}

.subtitle { color: #666; font-size: 0.95rem; margin: 0; }

.card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.card-header h2 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #111;
  margin: 0 0 0.5rem;
  text-transform: capitalize;
}

.card-description { color: #555; font-size: 0.9rem; line-height: 1.6; margin: 0; }

.alert {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  line-height: 1.5;
}
.alert-error  { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
.alert-success { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.alert-icon { font-weight: 700; flex-shrink: 0; }

.card-actions { display: flex; justify-content: flex-end; }

.empty-state { color: #888; font-size: 0.9rem; text-align: center; padding: 1rem 0; }

.tabla-pendientes {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
.tabla-pendientes th {
  text-align: left;
  padding: 8px 10px;
  color: #666;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  border-bottom: 1px solid #e5e7eb;
}
.tabla-pendientes td {
  padding: 10px 10px;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}
.tabla-pendientes tr:last-child td { border-bottom: none; }

.cliente-nombre { font-weight: 600; color: #111; }
.cliente-email  { color: #888; font-size: 0.8rem; }
.actividad-nombre { font-weight: 500; color: #222; }
.turno-desc  { color: #888; font-size: 0.8rem; }
.periodo-cell { text-transform: capitalize; color: #444; white-space: nowrap; }
.monto-cell  { font-weight: 600; color: #111; white-space: nowrap; }
.accion-cell { text-align: right; }

.btn {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  transition: opacity 0.15s;
}
.btn:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-primary { background: #11a691; color: #fff; }
.btn-primary:not(:disabled):hover { background: #0e8f7c; }

.btn-cobrar { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.btn-cobrar:not(:disabled):hover { background: #dcfce7; }

.spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
.spinner--dark { border-color: rgba(21,128,61,0.3); border-top-color: #15803d; }

@keyframes spin { to { transform: rotate(360deg); } }
</style>
