<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { useInscripcionStore } from '@/stores/inscripcionStore'
import { agregarListaEspera } from '@/services/inscripcionService'
import { getFormOptions, extractBackendError } from '@/services/sessionService'
import { getClienteById } from '@/services/clientesService'
import type { ActivityOption } from '@/services/sessionService'
import type { Cliente as ClienteService } from '@/services/clientesService'

const router = useRouter()
const route = useRoute()
const store = useInscripcionStore()

const isClienteFlow = computed(() => !!route.params.clienteId)
const clienteId = computed(() => isClienteFlow.value ? Number(route.params.clienteId) : null)

const clienteFromRoute = ref<ClienteService | null>(null)
const cliente = computed(() =>
  isClienteFlow.value ? clienteFromRoute.value! : store.clienteSeleccionado!
)
const turno = computed(() => store.turnoSeleccionado!)

const DAY_LABELS: Record<string, string> = {
  lunes: 'Lun', martes: 'Mar', miercoles: 'Mié',
  jueves: 'Jue', viernes: 'Vie', sabado: 'Sáb',
}

const allActivities = ref<ActivityOption[]>([])
const activityName = computed(() =>
  allActivities.value.find(a => a.id === turno.value.activity_id)?.name
  ?? `Actividad ${turno.value.activity_id}`
)

// ─── Estado ───────────────────────────────────────────────────────────────────

const isConfirming = ref(false)
const confirmError = ref<string | null>(null)
const isSuccess = ref(false)

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getInitials(first: string, last: string): string {
  return `${first[0]}${last[0]}`.toUpperCase()
}

onMounted(async () => {
  const formOptions = await getFormOptions().catch(() => ({ activities: [] as ActivityOption[] }))
  allActivities.value = formOptions.activities

  // Carga del banner del cliente (no bloquea el formulario)
  if (isClienteFlow.value) {
    getClienteById(Number(route.params.clienteId))
      .then(c => { clienteFromRoute.value = c })
      .catch(() => {})
  }
})

// ─── Acciones ─────────────────────────────────────────────────────────────────

async function handleConfirmar() {
  if (isConfirming.value) return
  confirmError.value = null
  isConfirming.value = true
  try {
    const userId = isClienteFlow.value ? clienteId.value! : store.clienteSeleccionado!.id
    await agregarListaEspera(turno.value.id, userId)
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
          <h1 class="page-title">Lista de espera</h1>
          <p class="page-subtitle">Registrá al cliente en la lista de espera del turno sin cupo</p>
        </div>
        <button v-if="!isSuccess" type="button" class="btn-secondary" @click="handleVolver">
          ← Volver al listado
        </button>
      </div>

      <!-- ─── ÉXITO ──────────────────────────────────────────────── -->
      <div v-if="isSuccess" class="success-card" role="alert">
        <div class="success-icon" aria-hidden="true">✓</div>
        <h2 class="success-title">Cliente registrado en la lista de espera con éxito</h2>
        <p class="success-desc">
          {{ cliente?.first_name }} {{ cliente?.last_name }} quedó anotado/a en la lista de espera del turno.
          Será notificado si se libera un lugar.
        </p>
        <button type="button" class="btn-primary" @click="handleVolver">
          Volver al listado de turnos
        </button>
      </div>

      <!-- ─── FLUJO NORMAL ───────────────────────────────────────── -->
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
          <div class="card-title-row">
            <h2 class="card-title">Turno seleccionado</h2>
            <span class="badge-sin-cupo">Sin cupo</span>
          </div>
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
          </div>
        </div>

        <!-- Card de confirmación -->
        <div class="info-card">
          <h2 class="card-title">Confirmar registro</h2>

          <div class="waitlist-note">
            <span class="waitlist-note-icon" aria-hidden="true">ℹ</span>
            <span>
              El cliente se agregará al <strong>final de la lista de espera</strong> respetando el orden de llegada.
              El registro <strong>no requiere pago</strong>.
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
              class="btn-confirmar"
              :disabled="isConfirming"
              @click="handleConfirmar"
            >
              <span v-if="isConfirming" class="spinner" aria-hidden="true"></span>
              {{ isConfirming ? 'Registrando...' : 'Confirmar registro en lista de espera' }}
            </button>
          </div>
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

.card-title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 700;
  color: #0d3027;
  margin: 0 0 1.25rem 0;
}

.card-title-row .card-title {
  margin: 0;
}

.badge-sin-cupo {
  display: inline-block;
  padding: 0.2rem 0.65rem;
  background: #fff7ed;
  color: #c2410c;
  border: 1px solid #fed7aa;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
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

/* ─── Nota informativa ───────────────────────────────────── */

.waitlist-note {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.85rem 1rem;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 10px;
  font-size: 0.85rem;
  color: #0c4a6e;
  line-height: 1.5;
  margin-bottom: 1.25rem;
}

.waitlist-note-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: #0284c7;
  color: white;
  border-radius: 50%;
  font-size: 0.72rem;
  font-weight: 800;
  flex-shrink: 0;
  margin-top: 1px;
}

/* ─── Error banner ───────────────────────────────────────── */

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

/* ─── Acciones ───────────────────────────────────────────── */

.confirm-actions {
  display: flex;
  justify-content: flex-end;
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
