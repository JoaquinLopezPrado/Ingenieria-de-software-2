<script setup lang="ts">
import { ref } from 'vue'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { adminGenerateNextMonthCharges, type GenerateChargesResponse } from '@/services/subscriptionService'
import { extractBackendError } from '@/services/sessionService'

const _MESES = [
  '', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

const today = new Date()
const nextMonth = today.getMonth() === 11 ? 1 : today.getMonth() + 2
const nextYear = today.getMonth() === 11 ? today.getFullYear() + 1 : today.getFullYear()

const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<GenerateChargesResponse | null>(null)

async function handleGenerar() {
  if (loading.value) return
  loading.value = true
  error.value = null
  result.value = null
  try {
    result.value = await adminGenerateNextMonthCharges()
  } catch (e) {
    error.value = extractBackendError(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AdminLayout>
    <section class="suscripciones-admin">
      <div class="page-header">
        <h1>Gestión de suscripciones</h1>
        <p class="subtitle">Generá los cargos del mes próximo y notificá a los abonados por mail.</p>
      </div>

      <div class="card">
        <div class="card-header">
          <h2>Cuotas de {{ _MESES[nextMonth] }} {{ nextYear }}</h2>
          <p class="card-description">
            Al confirmar, se generará el cargo de <strong>{{ _MESES[nextMonth] }} {{ nextYear }}</strong>
            para todos los clientes con suscripción mensual activa que aún no lo tengan,
            y se les enviará un mail de recordatorio con el monto y la fecha de vencimiento.
          </p>
        </div>

        <div v-if="error" class="alert alert-error">
          <span class="alert-icon">!</span>
          {{ error }}
        </div>

        <div v-if="result" class="alert alert-success">
          <span class="alert-icon">✓</span>
          <span v-if="result.charges_created > 0">
            Se generaron <strong>{{ result.charges_created }}</strong> cargo(s) y se enviaron los mails de recordatorio.
          </span>
          <span v-else>
            No había cargos pendientes de generar para {{ _MESES[result.period_month] }} {{ result.period_year }}.
          </span>
        </div>

        <div class="card-actions">
          <button
            class="btn btn-primary"
            :disabled="loading"
            @click="handleGenerar"
          >
            <span v-if="loading" class="spinner" />
            <span v-else>Generar cargos y notificar</span>
          </button>
        </div>
      </div>
    </section>
  </AdminLayout>
</template>

<style scoped>
.suscripciones-admin {
  max-width: 720px;
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

.subtitle {
  color: #666;
  font-size: 0.95rem;
  margin: 0;
}

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

.card-description {
  color: #555;
  font-size: 0.9rem;
  line-height: 1.6;
  margin: 0;
}

.alert {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  line-height: 1.5;
}

.alert-error {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.alert-success {
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
}

.alert-icon {
  font-weight: 700;
  flex-shrink: 0;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
}

.btn {
  padding: 0.6rem 1.25rem;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: opacity 0.15s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #11a691;
  color: #fff;
}

.btn-primary:not(:disabled):hover {
  background: #0e8f7c;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
