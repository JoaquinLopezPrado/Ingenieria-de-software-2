<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { useInscripcionStore } from '@/stores/inscripcionStore'
import { getPreviewInscripcion, inscribirCliente } from '@/services/inscripcionService'
import { getFormOptions, extractBackendError } from '@/services/sessionService'
import { getClienteById } from '@/services/clientesService'
import type { PreviewInscripcionResponse } from '@/services/inscripcionService'
import type { ActivityOption } from '@/services/sessionService'
import type { Cliente as ClienteService } from '@/services/clientesService'

const router = useRouter()
const route = useRoute()
const store = useInscripcionStore()

const isClienteFlow = computed(() => !!route.params.clienteId)
const clienteId = computed(() => isClienteFlow.value ? Number(route.params.clienteId) : null)

// Flujo nuevo: cliente cargado por API. Flujo viejo: desde el store.
const clienteFromRoute = ref<ClienteService | null>(null)
const cliente = computed(() =>
  isClienteFlow.value ? clienteFromRoute.value! : store.clienteSeleccionado!
)
const turno = computed(() => store.turnoSeleccionado!)

const DAY_LABELS: Record<string, string> = {
  lunes: 'Lun', martes: 'Mar', miercoles: 'Mié',
  jueves: 'Jue', viernes: 'Vie', sabado: 'Sáb',
}

// ─── Mes de inicio ────────────────────────────────────────────────────────────

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
               'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

interface MesOption { label: string; month: number; year: number }

function buildMesOptions(): MesOption[] {
  const opts: MesOption[] = []
  const now = new Date()
  for (let i = 0; i < 5; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() + i, 1)
    opts.push({ label: `${MESES[d.getMonth()]} ${d.getFullYear()}`, month: d.getMonth() + 1, year: d.getFullYear() })
  }
  return opts
}

const mesOptions = buildMesOptions()
// null = auto (primer mes disponible); { month, year } = mes específico
const selectedMes = ref<MesOption | null>(null)

// ─── Estado ───────────────────────────────────────────────────────────────────

const allActivities = ref<ActivityOption[]>([])
const isLoadingPreview = ref(true)
const isConfirming = ref(false)
const preview = ref<PreviewInscripcionResponse | null>(null)
const previewError = ref<string | null>(null)
const confirmError = ref<string | null>(null)
const isSuccess = ref(false)

// ─── Computeds ────────────────────────────────────────────────────────────────

const activityName = computed(() => {
  return allActivities.value.find(a => a.id === turno.value.activity_id)?.name
    ?? `Actividad ${turno.value.activity_id}`
})

const totalClases = computed(() =>
  (preview.value?.clases_con_cupo.length ?? 0) +
  (preview.value?.clases_sin_cupo.length ?? 0) +
  (preview.value?.clases_ya_abonadas.length ?? 0)
)

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getInitials(first: string, last: string): string {
  return `${first[0]}${last[0]}`.toUpperCase()
}

function formatMoney(amount: number): string {
  return `$${amount.toLocaleString('es-AR')}`
}

// ─── Ciclo de vida ────────────────────────────────────────────────────────────

async function fetchPreview() {
  const userId = isClienteFlow.value ? Number(route.params.clienteId) : store.clienteSeleccionado!.id
  isLoadingPreview.value = true
  previewError.value = null
  try {
    preview.value = await getPreviewInscripcion(
      turno.value.id, userId, turno.value.class_price,
      selectedMes.value?.month, selectedMes.value?.year,
    )
  } catch (err) {
    preview.value = null
    previewError.value = extractBackendError(err) || 'No se pudo calcular el monto de la inscripción'
  } finally {
    isLoadingPreview.value = false
  }
}

onMounted(async () => {
  try {
    const [formOptions] = await Promise.all([
      getFormOptions(),
      fetchPreview(),
    ])
    allActivities.value = formOptions.activities
  } catch {
    // fetchPreview ya maneja su propio error
  }

  // Carga del banner del cliente (no bloquea el preview)
  if (isClienteFlow.value) {
    getClienteById(Number(route.params.clienteId))
      .then(c => { clienteFromRoute.value = c })
      .catch(() => {})
  }
})

watch(selectedMes, () => {
  confirmError.value = null
  fetchPreview()
})

// ─── Acciones ─────────────────────────────────────────────────────────────────

async function handleConfirmar() {
  if (isConfirming.value || !preview.value) return
  confirmError.value = null
  isConfirming.value = true
  try {
    const userId = isClienteFlow.value ? clienteId.value! : store.clienteSeleccionado!.id
    await inscribirCliente(turno.value.id, userId, selectedMes.value?.month, selectedMes.value?.year)
    store.setTurno(null)
    isSuccess.value = true
  } catch (err) {
    confirmError.value = extractBackendError(err)
  } finally {
    isConfirming.value = false
  }
}

function handleVolver() {
  if (isClienteFlow.value) {
    router.push({ name: 'clientes-inscripciones-turnos', params: { clienteId: clienteId.value! } })
  } else {
    router.push({ name: 'inscripciones-turnos' })
  }
}

function handleCambiarCliente() {
  if (isClienteFlow.value) {
    router.push({ name: 'ficha-cliente', params: { clienteId: clienteId.value! } })
  } else {
    store.reset()
    router.push({ name: 'inscripciones-buscar-cliente' })
  }
}
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <!-- ─── Header ──────────────────────────────────────────────── -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Inscribir cliente</h1>
          <p class="page-subtitle">Revisá el resumen y confirmá el pago presencial</p>
        </div>
        <button v-if="!isSuccess" type="button" class="btn-secondary" @click="handleVolver">
          ← Volver al listado
        </button>
      </div>

      <!-- ─── ÉXITO ────────────────────────────────────────────────── -->
      <div v-if="isSuccess" class="success-card" role="alert">
        <div class="success-icon" aria-hidden="true">✓</div>
        <h2 class="success-title">Inscripción realizada con éxito</h2>
        <p class="success-desc">
          {{ cliente?.first_name }} {{ cliente?.last_name }} quedó inscripto/a en el turno correctamente.
        </p>
        <button type="button" class="btn-primary" @click="handleVolver">
          Volver al listado de turnos
        </button>
      </div>

      <!-- ─── FLUJO NORMAL ──────────────────────────────────────────── -->
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
          <button type="button" class="btn-cambiar" @click="handleCambiarCliente">
            {{ isClienteFlow ? '← Volver a la ficha' : '← Cambiar cliente' }}
          </button>
        </div>

        <!-- Card del turno -->
        <div class="info-card">
          <h2 class="card-title">Turno seleccionado</h2>
          <div class="turno-grid">
            <div class="turno-field">
              <span class="field-label">Actividad</span>
              <span class="field-value field-value--highlight">{{ activityName }}</span>
            </div>
            <div class="turno-field">
              <span class="field-label">Descripción</span>
              <span class="field-value">{{ turno.description || '—' }}</span>
            </div>
            <div class="turno-field">
              <span class="field-label">Días</span>
              <div class="days-list">
                <span
                  v-for="day in turno.days"
                  :key="day"
                  class="day-chip"
                >{{ DAY_LABELS[day] ?? day }}</span>
              </div>
            </div>
            <div class="turno-field">
              <span class="field-label">Horario</span>
              <span class="field-value">{{ turno.start_time }} – {{ turno.end_time }}</span>
            </div>
            <div class="turno-field">
              <span class="field-label">Precio por clase</span>
              <span class="field-value">{{ formatMoney(turno.class_price) }}</span>
            </div>
          </div>
        </div>

        <!-- Selector de mes de inicio (solo flujo admin) -->
        <div v-if="isClienteFlow" class="mes-selector-card">
          <label class="mes-label" for="mes-inicio">Mes de inicio</label>
          <select
            id="mes-inicio"
            class="mes-select"
            :value="selectedMes ? `${selectedMes.month}-${selectedMes.year}` : ''"
            @change="selectedMes = mesOptions.find(o => `${o.month}-${o.year}` === ($event.target as HTMLSelectElement).value) ?? null"
          >
            <option value="">Próximo disponible</option>
            <option
              v-for="m in mesOptions"
              :key="`${m.month}-${m.year}`"
              :value="`${m.month}-${m.year}`"
            >{{ m.label }}</option>
          </select>
        </div>

        <!-- Card de resumen / preview -->
        <div class="info-card">
          <h2 class="card-title">Resumen de inscripción</h2>

          <!-- Loading -->
          <div v-if="isLoadingPreview" class="preview-loading" aria-live="polite">
            <span class="spinner" aria-hidden="true"></span>
            Calculando el monto...
          </div>

          <!-- Error en preview -->
          <div v-else-if="previewError" class="error-banner" role="alert">
            <span class="error-icon" aria-hidden="true">!</span>
            {{ previewError }}
          </div>

          <!-- Contenido del preview -->
          <template v-else-if="preview">
            <p class="clases-total-note">
              El turno tiene {{ totalClases }} {{ totalClases === 1 ? 'clase' : 'clases' }} en el período en curso.
            </p>

            <!-- Desglose -->
            <div class="breakdown">
              <div class="breakdown-row">
                <span class="breakdown-label">
                  {{ preview.clases_con_cupo.length }}
                  {{ preview.clases_con_cupo.length === 1 ? 'clase incluida' : 'clases incluidas' }}
                </span>
                <span class="breakdown-amount">
                  {{ formatMoney(preview.clases_con_cupo.length * preview.precio_por_clase) }}
                </span>
              </div>

              <div v-if="preview.clases_sin_cupo.length > 0" class="breakdown-row breakdown-row--discount">
                <span class="breakdown-label">
                  {{ preview.clases_sin_cupo.length }}
                  {{ preview.clases_sin_cupo.length === 1 ? 'clase sin cupo' : 'clases sin cupo' }}
                  <span class="breakdown-note">(sin lugar disponible)</span>
                </span>
                <span class="breakdown-amount breakdown-amount--negative">
                  − {{ formatMoney(preview.clases_sin_cupo.length * preview.precio_por_clase) }}
                </span>
              </div>

              <div v-if="preview.clases_ya_abonadas.length > 0" class="breakdown-row breakdown-row--discount">
                <span class="breakdown-label">
                  {{ preview.clases_ya_abonadas.length }}
                  {{ preview.clases_ya_abonadas.length === 1 ? 'clase ya abonada' : 'clases ya abonadas' }}
                  <span class="breakdown-note">(reserva individual previa)</span>
                </span>
                <span class="breakdown-amount breakdown-amount--negative">
                  − {{ formatMoney(preview.clases_ya_abonadas.length * preview.precio_por_clase) }}
                </span>
              </div>

              <div class="breakdown-divider"></div>

              <div class="breakdown-row breakdown-row--total">
                <span class="breakdown-label">Total a cobrar en efectivo</span>
                <span class="breakdown-total">{{ formatMoney(preview.total) }}</span>
              </div>
            </div>

            <!-- Nota de pago -->
            <div class="payment-note">
              <span class="payment-note-icon" aria-hidden="true">💵</span>
              El pago se registra como presencial en efectivo. Confirmá solo después de haber recibido el importe.
            </div>

            <!-- Error de confirmación (ej: ya inscripto) -->
            <div v-if="confirmError" class="error-banner" role="alert">
              <span class="error-icon" aria-hidden="true">!</span>
              {{ confirmError }}
            </div>

            <!-- Botón confirmar -->
            <div class="confirm-actions">
              <button
                type="button"
                class="btn-confirmar"
                :disabled="isConfirming"
                @click="handleConfirmar"
              >
                <span v-if="isConfirming" class="spinner spinner--dark" aria-hidden="true"></span>
                {{ isConfirming ? 'Confirmando...' : 'Confirmar inscripción' }}
              </button>
            </div>
          </template>
        </div>

      </template>
    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper {
  width: 100%;
  max-width: 680px;
}

/* ─── Header ─────────────────────────────────────────────── */

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

/* ─── Selector de mes ────────────────────────────────── */

.mes-selector-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 0.85rem 1.2rem;
  margin-bottom: 1.25rem;
}

.mes-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
}

.mes-select {
  flex: 1;
  padding: 0.45rem 0.75rem;
  border: 1.5px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.88rem;
  color: #111827;
  background: #f9fafb;
  cursor: pointer;
  outline: none;
  text-transform: capitalize;
}

.mes-select:focus {
  border-color: #11a691;
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

/* ─── Éxito ─────────────────────────────────────────────── */

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
  font-size: 1.2rem;
  font-weight: 700;
  color: #065f46;
  margin: 0 0 0.6rem 0;
}

.success-desc {
  color: #6b7280;
  font-size: 0.9rem;
  margin: 0 0 2rem 0;
}

@keyframes slide-in {
  from { opacity: 0; transform: translateY(8px) }
  to   { opacity: 1; transform: translateY(0) }
}

/* ─── Banner del cliente ─────────────────────────────────── */

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
  flex: 1;
}

.banner-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.banner-doc {
  font-size: 0.78rem;
  color: #6b7280;
}

.btn-cambiar {
  font-size: 0.8rem;
  color: #18b4a3;
  background: none;
  border: none;
  cursor: pointer;
  white-space: nowrap;
  font-weight: 600;
  padding: 0;
  flex-shrink: 0;
  transition: color 0.15s;
}

.btn-cambiar:hover {
  color: #0d9b8a;
}

/* ─── Cards ─────────────────────────────────────────────── */

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

/* ─── Turno grid ─────────────────────────────────────────── */

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

.days-list {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.day-chip {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  background: #f0fdf4;
  color: #166534;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid #bbf7d0;
}

/* ─── Loading ────────────────────────────────────────────── */

.preview-loading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #6b7280;
  font-size: 0.9rem;
  padding: 1.5rem 0;
}

/* ─── Desglose ───────────────────────────────────────────── */

.clases-total-note {
  font-size: 0.82rem;
  color: #6b7280;
  margin: 0 0 1.25rem 0;
}

.breakdown {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.breakdown-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
  padding: 0.5rem 0;
}

.breakdown-row--discount {
  opacity: 0.75;
}

.breakdown-row--total {
  padding-top: 0.75rem;
}

.breakdown-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 0.25rem 0;
}

.breakdown-label {
  font-size: 0.88rem;
  color: #374151;
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.breakdown-note {
  font-size: 0.76rem;
  color: #9ca3af;
}

.breakdown-amount {
  font-size: 0.9rem;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
}

.breakdown-amount--negative {
  color: #dc2626;
}

.breakdown-total {
  font-size: 1.15rem;
  font-weight: 800;
  color: #0d3027;
}

.breakdown-row--total .breakdown-label {
  font-size: 0.92rem;
  font-weight: 700;
  color: #111827;
}

/* ─── Nota de pago ───────────────────────────────────────── */

.payment-note {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  margin-top: 1.5rem;
  padding: 0.85rem 1rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
  font-size: 0.85rem;
  color: #166534;
  line-height: 1.5;
}

.payment-note-icon {
  flex-shrink: 0;
  font-size: 1rem;
  margin-top: 1px;
}

/* ─── Error banner ───────────────────────────────────────── */

.error-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  margin-top: 1.25rem;
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

/* ─── Acciones ───────────────────────────────────────────── */

.confirm-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.5rem;
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

/* ─── Spinner ────────────────────────────────────────────── */

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

.spinner--dark {
  border-color: rgba(255, 255, 255, 0.35);
  border-top-color: white;
}

@keyframes spin {
  to { transform: rotate(360deg) }
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

  .days-list {
    justify-content: flex-start;
  }

  .confirm-actions {
    justify-content: stretch;
  }

  .btn-confirmar {
    width: 100%;
    justify-content: center;
  }
}
</style>
