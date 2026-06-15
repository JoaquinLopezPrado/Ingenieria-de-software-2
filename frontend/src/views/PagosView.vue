<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ListLayout from '@/components/ListLayout.vue'
import ItemCard from '@/components/ItemCard.vue'
import { enrollmentService } from '@/services/enrollmentService'

type EnrollmentStatus = 'pending' | 'confirmed' | 'cancelled' | 'deposit_paid' | 'deposit_forfeited' | 'refunded'

interface RawSubscription {
  enrollment_id: number
  status: EnrollmentStatus
  amount: string
  original_amount: string
  discount_full_classes: string
  expires_at: string | null
  created_at: string
  turno_id: number
  turno_description: string
  start_time: string
  end_time: string
  instructor: string
  activity_name: string
  days: string[]
  last_payment_date: string | null
}

interface RawSingle {
  enrollment_id: number
  status: EnrollmentStatus
  amount: string
  expires_at: string | null
  created_at: string
  turno_id: number
  clase_id: number
  clase_date: string
  start_time: string
  end_time: string
  turno_description: string
  instructor: string
  activity_name: string
}

const PAID_STATUSES: EnrollmentStatus[] = ['confirmed', 'deposit_paid', 'deposit_forfeited', 'refunded']

const suscripciones = ref<RawSubscription[]>([])
const clasesIndividuales = ref<RawSingle[]>([])
const isLoading = ref(true)
const hasError = ref(false)

const formatPeso = (amount: string | number): string => {
  const n = typeof amount === 'string' ? parseFloat(amount) : amount
  return '$' + Math.round(n).toLocaleString('es-AR')
}

const formatFecha = (raw: string): string => {
  const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
  const parts = raw.split('-')
  if (parts.length !== 3) return raw
  const dia = parseInt(parts[2] ?? '0', 10)
  const mes = meses[parseInt(parts[1] ?? '0', 10) - 1] ?? ''
  return `${dia} ${mes}`
}

const periodoLabel = (item: RawSubscription): string => {
  const ref = item.last_payment_date ?? item.created_at.slice(0, 10)
  const parts = ref.split('-')
  if (parts.length < 2) return ''
  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ]
  const mes = meses[parseInt(parts[1] ?? '0', 10) - 1] ?? ''
  return `${mes} ${parts[0]}`
}

const fetchPagos = async () => {
  try {
    isLoading.value = true
    hasError.value = false
    const [resSub, resSingle] = await Promise.all([
      enrollmentService.getMySubscription(),
      enrollmentService.getMySingle(),
    ])
    suscripciones.value = (resSub.data as RawSubscription[]).filter(e =>
      PAID_STATUSES.includes(e.status),
    )
    clasesIndividuales.value = (resSingle.data as RawSingle[]).filter(e =>
      PAID_STATUSES.includes(e.status),
    )
  } catch {
    hasError.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchPagos)

const STATUS_LABEL: Record<EnrollmentStatus, string> = {
  confirmed: 'Pagado',
  deposit_paid: 'Seña abonada',
  deposit_forfeited: 'Seña vencida',
  refunded: 'Reembolsado',
  pending: '',
  cancelled: '',
}

const STATUS_CLASS: Record<EnrollmentStatus, string> = {
  confirmed: 'badge-pagado',
  deposit_paid: 'badge-senia',
  deposit_forfeited: 'badge-vencida',
  refunded: 'badge-reembolsado',
  pending: '',
  cancelled: '',
}

const totalPagado = computed(() => {
  const sumSub = suscripciones.value
    .filter(e => e.status === 'confirmed')
    .reduce((acc, e) => acc + parseFloat(e.amount), 0)
  const sumSingle = clasesIndividuales.value
    .filter(e => e.status === 'confirmed' || e.status === 'deposit_paid')
    .reduce((acc, e) => acc + parseFloat(e.amount) * (e.status === 'deposit_paid' ? 0.3 : 1), 0)
  return sumSub + sumSingle
})
</script>

<template>
  <ListLayout pageTitle="Mis Pagos">
    <div class="central-wrapper">

      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <span>Cargando tus pagos...</span>
      </div>

      <div v-else-if="hasError" class="error-state">
        <span>No se pudieron recuperar tus pagos.</span>
        <button type="button" class="btn-retry" @click="fetchPagos">Reintentar</button>
      </div>

      <template v-else>
        <div v-if="suscripciones.length > 0 || clasesIndividuales.length > 0" class="resumen-banner">
          <span class="resumen-label">Total abonado</span>
          <span class="resumen-monto">{{ formatPeso(totalPagado) }}</span>
        </div>

        <div class="columns-grid">

          <section class="pago-section">
            <div class="section-header">
              <h3>Turnos Fijos</h3>
            </div>
            <div class="cards-stack">
              <div v-if="suscripciones.length === 0" class="empty-column">
                <span>No hay pagos de turnos registrados</span>
              </div>
              <template v-else>
                <ItemCard
                  v-for="sub in suscripciones"
                  :key="sub.enrollment_id"
                  :title="sub.activity_name"
                  :subtitle="sub.turno_description"
                  class="pago-card"
                >
                  <template #right>
                    <div class="pago-right">
                      <span :class="['status-badge', STATUS_CLASS[sub.status]]">
                        {{ STATUS_LABEL[sub.status] }}
                      </span>
                      <span class="precio-label">{{ formatPeso(sub.amount) }}</span>
                      <div class="dias-badge-container">
                        <span v-for="dia in sub.days" :key="dia" class="dia-badge">
                          {{ dia.slice(0, 3) }}
                        </span>
                      </div>
                      <span class="horario-label">{{ sub.start_time }} - {{ sub.end_time }}</span>
                      <span class="periodo-label">{{ periodoLabel(sub) }}</span>
                    </div>
                  </template>
                </ItemCard>
              </template>
            </div>
          </section>

          <section class="pago-section">
            <div class="section-header">
              <h3>Clases Individuales</h3>
            </div>
            <div class="cards-stack">
              <div v-if="clasesIndividuales.length === 0" class="empty-column">
                <span>No hay pagos de clases registrados</span>
              </div>
              <template v-else>
                <ItemCard
                  v-for="clase in clasesIndividuales"
                  :key="clase.enrollment_id"
                  :title="clase.activity_name"
                  subtitle="Clase Individual"
                  class="pago-card"
                >
                  <template #right>
                    <div class="pago-right">
                      <span :class="['status-badge', STATUS_CLASS[clase.status]]">
                        {{ STATUS_LABEL[clase.status] }}
                      </span>
                      <span class="precio-label">{{ formatPeso(clase.amount) }}</span>
                      <span class="fecha-badge">{{ formatFecha(clase.clase_date) }}</span>
                      <span class="horario-label">{{ clase.start_time }} hs</span>
                    </div>
                  </template>
                </ItemCard>
              </template>
            </div>
          </section>

        </div>
      </template>

    </div>
  </ListLayout>
</template>

<style scoped>
.central-wrapper {
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
}

.resumen-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #e8f5e9 0%, #f1fdf9 100%);
  border: 1.5px solid #c8e6c9;
  border-radius: 14px;
  padding: 14px 20px;
  margin-bottom: 24px;
}

.resumen-label {
  color: #2e7d32;
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.resumen-monto {
  color: #11a691;
  font-size: 22px;
  font-weight: 800;
}

.columns-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
  width: 100%;
}

.pago-section {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.section-header {
  margin-bottom: 14px;
  border-bottom: 2px solid #cfeee6;
  padding-bottom: 6px;
}

.section-header h3 {
  color: #12695f;
  font-size: 18px;
  font-weight: 800;
  margin: 0;
}

.cards-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.pago-card {
  width: 100%;
}

:deep(.item-card) {
  min-height: 106px;
  display: flex;
  align-items: center;
}

.pago-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 5px;
  height: 100%;
  min-width: 130px;
}

.status-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.badge-pagado {
  background-color: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}

.badge-senia {
  background-color: #fff3e0;
  color: #E65100;
  border: 1px solid #ffe0b2;
}

.badge-vencida {
  background-color: #eceff1;
  color: #546e7a;
  border: 1px solid #b0bec5;
}

.badge-reembolsado {
  background-color: #e3f2fd;
  color: #1565c0;
  border: 1px solid #bbdefb;
}

.precio-label {
  color: #11a691;
  font-weight: 800;
  font-size: 16px;
}

.dias-badge-container {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.dia-badge {
  background-color: #e0f2f1;
  color: #12695f;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 6px;
  text-transform: uppercase;
}

.horario-label {
  color: #2c3e50;
  font-weight: 700;
  font-size: 13px;
}

.periodo-label {
  color: #7f8c8d;
  font-size: 11px;
}

.fecha-badge {
  background: linear-gradient(135deg, #11a691 0%, #0d8277 100%);
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 10px;
}

.empty-column {
  background: rgba(255, 255, 255, 0.4);
  border: 2px dashed #cfeee6;
  padding: 32px;
  text-align: center;
  border-radius: 16px;
  color: #546e7a;
  font-size: 14px;
  font-weight: 600;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 80px 20px;
  color: #12695f;
  font-weight: 700;
  font-size: 16px;
}

.error-state {
  color: #c62828;
}

.btn-retry {
  background: #c62828;
  color: white;
  border: none;
  border-radius: 20px;
  padding: 8px 24px;
  font-weight: 700;
  cursor: pointer;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 4px solid #cfeee6;
  border-top-color: #11a691;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (min-width: 768px) {
  .central-wrapper {
    max-width: 960px;
  }

  .columns-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 32px;
  }
}

@media (max-width: 768px) {
  .pago-right {
    gap: 4px;
  }
}
</style>
