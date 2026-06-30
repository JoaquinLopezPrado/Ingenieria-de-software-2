<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { useInscripcionStore } from '@/stores/inscripcionStore'
import { extractBackendError } from '@/services/sessionService'
import { inscribirClienteClase } from '@/services/inscripcionService'

const router = useRouter()
const store = useInscripcionStore()

const clase = computed(() => store.claseSeleccionada)
const cliente = computed(() => store.clienteSeleccionado)

// ─── Tipo de pago ─────────────────────────────────────────────────────────────

type TipoPago = 'total' | 'sena'
const tipoPago = ref<TipoPago>('total')

const montoDisplay = computed(() => {
  if (!clase.value) return 0
  return tipoPago.value === 'sena'
    ? Math.round(clase.value.class_price * 0.3)
    : clase.value.class_price
})

const cupoDisponible = computed(() =>
  clase.value ? clase.value.capacity - clase.value.enrolled : 0
)

// ─── Estado ───────────────────────────────────────────────────────────────────

const isConfirming = ref(false)
const confirmError = ref<string | null>(null)
const isSuccess = ref(false)

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(dateStr: string): string {
  const [y, m, d] = dateStr.split('-').map(Number)
  return new Date(y!, m! - 1, d!).toLocaleDateString('es-AR', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function formatMoney(n: number): string {
  return `$${n.toLocaleString('es-AR')}`
}

function getInitials(first: string, last: string): string {
  return `${first[0]}${last[0]}`.toUpperCase()
}

// ─── Acciones ─────────────────────────────────────────────────────────────────

async function handleConfirmar() {
  if (!clase.value || !cliente.value || isConfirming.value) return
  confirmError.value = null
  isConfirming.value = true
  try {
    await inscribirClienteClase(clase.value.id, cliente.value.id)
    store.markClaseEnrolled(clase.value.id)
    isSuccess.value = true
  } catch (err) {
    confirmError.value = extractBackendError(err)
  } finally {
    isConfirming.value = false
  }
}

function handleVolver() {
  router.push({ name: 'inscripciones-clases' })
}
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <!-- ─── Header ──────────────────────────────────────────────── -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Inscribir a clase</h1>
          <p class="page-subtitle">Confirmá la inscripción del cliente a la clase seleccionada</p>
        </div>
        <button v-if="!isSuccess" type="button" class="btn-secondary" @click="handleVolver">
          ← Volver al calendario
        </button>
      </div>

      <!-- ─── Sin datos de clase (navegación directa) ─────────────── -->
      <div v-if="!clase" class="state-card state-empty">
        <div class="state-icon">📅</div>
        <h2 class="state-title">Clase no encontrada</h2>
        <p class="state-desc">
          Accedé a esta pantalla desde el calendario seleccionando una clase disponible.
        </p>
        <button type="button" class="btn-secondary" @click="handleVolver">
          Ir al calendario
        </button>
      </div>

      <template v-else>

        <!-- ─── ÉXITO ──────────────────────────────────────────────── -->
        <div v-if="isSuccess" class="success-card" role="alert">
          <div class="success-icon" aria-hidden="true">✓</div>
          <h2 class="success-title">Inscripción realizada con éxito</h2>
          <p class="success-desc">
            {{ cliente?.first_name }} {{ cliente?.last_name }} quedó inscripto/a en la clase del
            {{ formatDate(clase.date) }}.
          </p>
          <button type="button" class="btn-primary" @click="handleVolver">
            Volver al calendario
          </button>
        </div>

        <!-- ─── FLUJO NORMAL ──────────────────────────────────────── -->
        <template v-else>

          <!-- Banner del cliente -->
          <div v-if="cliente" class="cliente-banner">
            <div class="banner-avatar" aria-hidden="true">
              {{ getInitials(cliente.first_name, cliente.last_name) }}
            </div>
            <div class="banner-info">
              <span class="banner-name">{{ cliente.first_name }} {{ cliente.last_name }}</span>
              <span class="banner-doc">{{ cliente.doc_type_name }} {{ cliente.doc_number }}</span>
            </div>
          </div>

          <!-- Resumen de la clase -->
          <div class="info-card">
            <h2 class="card-title">Clase seleccionada</h2>
            <div class="turno-grid">
              <div class="turno-field">
                <span class="field-label">Actividad</span>
                <span class="field-value field-value--highlight">{{ clase.activity_name }}</span>
              </div>
              <div class="turno-field">
                <span class="field-label">Fecha</span>
                <span class="field-value">{{ formatDate(clase.date) }}</span>
              </div>
              <div class="turno-field">
                <span class="field-label">Horario</span>
                <span class="field-value">{{ clase.start_time }} – {{ clase.end_time }}</span>
              </div>
              <div class="turno-field">
                <span class="field-label">Cupo disponible</span>
                <span class="field-value">
                  {{ cupoDisponible }} lugar{{ cupoDisponible !== 1 ? 'es' : '' }}
                  <span class="cupo-total">(de {{ clase.capacity }})</span>
                </span>
              </div>
              <div class="turno-field">
                <span class="field-label">Precio por clase</span>
                <span class="field-value">{{ formatMoney(clase.class_price) }}</span>
              </div>
            </div>
          </div>

          <!-- Tipo de pago -->
          <div class="info-card">
            <h2 class="card-title">Tipo de pago</h2>

            <div class="pago-options">
              <label :class="['pago-option', { 'pago-option--active': tipoPago === 'total' }]">
                <input type="radio" v-model="tipoPago" value="total" class="pago-radio" />
                <div class="pago-content">
                  <span class="pago-label">Pagar total (100 %)</span>
                  <span class="pago-amount">{{ formatMoney(clase.class_price) }}</span>
                </div>
              </label>

              <label :class="['pago-option', { 'pago-option--active': tipoPago === 'sena' }]">
                <input type="radio" v-model="tipoPago" value="sena" class="pago-radio" />
                <div class="pago-content">
                  <span class="pago-label">Pagar seña (30 %)</span>
                  <span class="pago-amount">{{ formatMoney(Math.round(clase.class_price * 0.3)) }}</span>
                </div>
              </label>
            </div>

            <div class="monto-total">
              <span class="monto-label">Monto a cobrar</span>
              <span class="monto-value">{{ formatMoney(montoDisplay) }}</span>
            </div>

            <div class="pago-pending-note">
              <span class="pending-icon" aria-hidden="true">ℹ</span>
              <span>
                El tipo de pago es informativo. El backend aún no distingue seña/total
                — ver <em>pendientes-backend.md § 13.2</em>.
              </span>
            </div>

            <!-- Error de confirmación -->
            <div v-if="confirmError" class="error-banner" role="alert">
              <span class="error-icon" aria-hidden="true">!</span>
              {{ confirmError }}
            </div>

            <div class="confirm-actions">
              <button
                type="button"
                class="btn-cancelar"
                :disabled="isConfirming"
                @click="handleVolver"
              >
                Cancelar
              </button>
              <button
                type="button"
                class="btn-confirmar"
                :disabled="isConfirming"
                @click="handleConfirmar"
              >
                <span v-if="isConfirming" class="spinner" aria-hidden="true"></span>
                {{ isConfirming ? 'Inscribiendo...' : 'Confirmar inscripción' }}
              </button>
            </div>
          </div>

        </template>
      </template>
    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper {
  width: 100%;
  max-width: 680px;
}

/* ─── Header ──────────────────────────────────────────────── */

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.75rem;
  gap: 1rem;
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

.btn-secondary {
  padding: 0.6rem 1.2rem;
  background: white;
  color: #374151;
  border: 1.5px solid #d1d5db;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: border-color 0.15s;
}

.btn-secondary:hover {
  border-color: #9ca3af;
}

/* ─── Estado vacío ── */

.state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 3.5rem 2rem;
  border-radius: 12px;
  text-align: center;
}

.state-empty {
  background: #f9fafb;
  border: 2px dashed #d1d5db;
}

.state-icon { font-size: 2.5rem; }
.state-title {
  font-size: 1rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}
.state-desc { font-size: 0.9rem; color: #6b7280; margin: 0; max-width: 360px; }

/* ─── Éxito ── */

.success-card {
  background: white;
  border-radius: 16px;
  padding: 3rem 2rem;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1.5px solid #a7f3d0;
  animation: slide-in 0.25s ease;
}

.success-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #11998e, #0d9b8a);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 auto 1.25rem;
}

.success-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #065f46;
  margin: 0 0 0.6rem 0;
}

.success-desc {
  color: #6b7280;
  font-size: 0.9rem;
  line-height: 1.6;
  margin: 0 0 2rem 0;
}

@keyframes slide-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ─── Banner del cliente ── */

.cliente-banner {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  background: white;
  border-radius: 12px;
  padding: 0.9rem 1.2rem;
  margin-bottom: 1.25rem;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.banner-avatar {
  width: 38px;
  height: 38px;
  background: linear-gradient(135deg, #11998e, #0d9b8a);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 700;
  flex-shrink: 0;
}

.banner-info {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}

.banner-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: #111827;
}

.banner-doc {
  font-size: 0.78rem;
  color: #6b7280;
}

/* ─── Cards ── */

.info-card {
  background: white;
  border-radius: 16px;
  padding: 1.75rem 2rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
  margin-bottom: 1.25rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 700;
  color: #0d3027;
  margin: 0 0 1.25rem 0;
}

/* ─── Turno grid ── */

.turno-grid {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.turno-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.field-label {
  font-size: 0.82rem;
  color: #6b7280;
  font-weight: 600;
  flex-shrink: 0;
}

.field-value {
  font-size: 0.88rem;
  color: #1f2937;
  font-weight: 500;
  text-align: right;
}

.field-value--highlight {
  font-weight: 700;
  color: #0d3027;
}

.cupo-total {
  font-size: 0.8rem;
  color: #9ca3af;
  font-weight: 400;
}

/* ─── Tipo de pago ── */

.pago-options {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-bottom: 1.25rem;
}

.pago-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  border: 1.5px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: border-color 0.15s, background-color 0.15s;
}

.pago-option:hover {
  border-color: #11998e;
  background: #f0fdf9;
}

.pago-option--active {
  border-color: #11998e;
  background: #f0fdf9;
}

.pago-radio {
  accent-color: #11998e;
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.pago-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pago-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
}

.pago-amount {
  font-size: 0.95rem;
  font-weight: 700;
  color: #0d3027;
}

/* ─── Monto total ── */

.monto-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1rem;
  background: #f0fdf9;
  border: 1.5px solid #a7f3d0;
  border-radius: 10px;
  margin-bottom: 1rem;
}

.monto-label {
  font-size: 0.88rem;
  font-weight: 700;
  color: #065f46;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.monto-value {
  font-size: 1.15rem;
  font-weight: 800;
  color: #064e3b;
}

/* ─── Nota pendiente ── */

.pago-pending-note {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.65rem 0.85rem;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  font-size: 0.8rem;
  color: #92400e;
  line-height: 1.5;
  margin-bottom: 1.25rem;
}

.pending-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  background: #d97706;
  color: white;
  border-radius: 50%;
  font-size: 0.65rem;
  font-weight: 800;
  flex-shrink: 0;
  margin-top: 1px;
}

/* ─── Error banner ── */

.error-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  margin-bottom: 1.25rem;
  padding: 0.85rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  color: #991b1b;
  font-size: 0.88rem;
  font-weight: 500;
}

.error-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: #dc2626;
  color: white;
  border-radius: 50%;
  font-size: 0.7rem;
  font-weight: 800;
  flex-shrink: 0;
  margin-top: 1px;
}

/* ─── Acciones ── */

.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-cancelar {
  padding: 0.8rem 1.5rem;
  background: #f3f4f6;
  color: #374151;
  border: none;
  border-radius: 999px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-cancelar:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-cancelar:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-confirmar,
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem 2rem;
  background-color: #0d3027;
  color: white;
  font-size: 0.95rem;
  font-weight: 700;
  border: none;
  border-radius: 999px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-confirmar:hover:not(:disabled),
.btn-primary:hover {
  background-color: #18b4a3;
}

.btn-confirmar:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

/* ─── Spinner ── */

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 520px) {
  .page-header {
    flex-direction: column;
  }

  .turno-field {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.2rem;
  }

  .field-value {
    text-align: left;
  }

  .confirm-actions {
    flex-direction: column;
  }

  .btn-confirmar,
  .btn-cancelar {
    width: 100%;
    justify-content: center;
  }
}
</style>
