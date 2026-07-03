<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { getClienteById, deactivateCliente, reactivateCliente, type Cliente } from '@/services/clientesService'
import { extractBackendError } from '@/services/sessionService'
import { useAuthStore } from '@/stores/authStore'
import { useInscripcionStore } from '@/stores/inscripcionStore'
import { isAdminUser } from '@/utils/role'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const inscripcionStore = useInscripcionStore()

const clienteId = Number(route.params.clienteId)
const isAdmin = computed(() => isAdminUser(authStore.user))

const cliente = ref<Cliente | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

// ─── Dar de baja ─────────────────────────────────────────────────────────────

const confirmingDeactivate = ref(false)
const deactivateLoading = ref(false)
const deactivateError = ref<string | null>(null)

function askDeactivate() {
  deactivateError.value = null
  confirmingDeactivate.value = true
}

function cancelDeactivate() {
  confirmingDeactivate.value = false
}

async function confirmDeactivate() {
  deactivateLoading.value = true
  deactivateError.value = null
  try {
    await deactivateCliente(clienteId)
    if (cliente.value) cliente.value.is_active = false
    confirmingDeactivate.value = false
  } catch (err) {
    deactivateError.value = extractBackendError(err) ?? 'Ocurrió un error. Intentá de nuevo.'
  } finally {
    deactivateLoading.value = false
  }
}

// ─── Reactivar ───────────────────────────────────────────────────────────────

const reactivateLoading = ref(false)
const reactivateError = ref<string | null>(null)

async function confirmReactivate() {
  reactivateLoading.value = true
  reactivateError.value = null
  try {
    await reactivateCliente(clienteId)
    if (cliente.value) cliente.value.is_active = true
  } catch (err) {
    reactivateError.value = extractBackendError(err) ?? 'Ocurrió un error. Intentá de nuevo.'
  } finally {
    reactivateLoading.value = false
  }
}

onMounted(async () => {
  try {
    cliente.value = await getClienteById(clienteId)
  } catch (err) {
    error.value = extractBackendError(err) ?? 'No se pudo cargar la ficha del cliente.'
  } finally {
    loading.value = false
  }
})

function inscribirAClase() {
  if (!cliente.value) return
  const c = cliente.value
  inscripcionStore.setCliente({
    id: c.id,
    first_name: c.first_name,
    last_name: c.last_name,
    email: c.email,
    phone: c.phone,
    doc_number: c.doc_number,
    doc_type_name: c.doc_type_name as 'DNI' | 'PASAPORTE',
  })
  router.push({ name: 'inscripciones-clases' })
}
</script>

<template>
  <AdminLayout>
    <div class="ficha-page">
      <header class="page-header">
        <RouterLink :to="{ name: 'lista-alumnos' }" class="back-link">← Volver</RouterLink>
        <h1 class="page-title">Ficha del cliente</h1>
      </header>

      <div v-if="loading" class="state-box">
        <p class="state-text">Cargando...</p>
      </div>

      <div v-else-if="error" class="state-box error-box">
        <p class="state-text">{{ error }}</p>
      </div>

      <template v-else-if="cliente">
        <!-- ── Datos ── -->
        <div class="ficha-card">
          <div class="avatar">
            {{ cliente.first_name.charAt(0) }}{{ cliente.last_name.charAt(0) }}
          </div>

          <div class="ficha-info">
            <h2 class="cliente-name">{{ cliente.first_name }} {{ cliente.last_name }}</h2>

            <dl class="info-list">
              <div class="info-row">
                <dt class="info-label">Documento</dt>
                <dd class="info-value">{{ cliente.doc_type_name }} {{ cliente.doc_number }}</dd>
              </div>
              <div class="info-row">
                <dt class="info-label">Email</dt>
                <dd class="info-value">{{ cliente.email }}</dd>
              </div>
              <div class="info-row">
                <dt class="info-label">Teléfono</dt>
                <dd class="info-value">{{ cliente.phone }}</dd>
              </div>
            </dl>
          </div>
        </div>


        <!-- ── Acciones ── -->
        <div class="actions-card">
          <div class="actions-grid">
            <RouterLink
              :to="{ name: 'clientes-inscripciones-turnos', params: { clienteId } }"
              class="action-btn action-inscribir-turno"
            >
              Inscribir a Turno
            </RouterLink>

            <button
              type="button"
              class="action-btn action-inscribir-clase"
              @click="inscribirAClase"
            >
              Inscribir a Clase
            </button>

            <RouterLink
              :to="`/clientes/${clienteId}/inscripciones`"
              class="action-btn action-secondary"
            >
              Ver inscripciones activas
            </RouterLink>

            <RouterLink
              :to="`/clientes/${clienteId}/asistencias`"
              class="action-btn action-secondary"
            >
              Ver historial de asistencias
            </RouterLink>
          </div>

          <!-- Solo administrador -->
          <div v-if="isAdmin" class="danger-zone">
            <div v-if="cliente.is_active">
              <button
                v-if="!confirmingDeactivate"
                type="button"
                class="action-btn action-danger"
                @click="askDeactivate"
              >
                Dar de Baja
              </button>

              <div v-else class="confirm-box">
                <p class="confirm-text">
                  ¿Confirmás la baja de <strong>{{ cliente.first_name }} {{ cliente.last_name }}</strong>?
                  Se cancelarán todas sus suscripciones y clases futuras de forma inmediata.
                </p>
                <p v-if="deactivateError" class="confirm-error">{{ deactivateError }}</p>
                <div class="confirm-actions">
                  <button
                    type="button"
                    class="action-btn action-danger"
                    :disabled="deactivateLoading"
                    @click="confirmDeactivate"
                  >
                    {{ deactivateLoading ? 'Procesando...' : 'Sí, dar de baja' }}
                  </button>
                  <button
                    type="button"
                    class="action-btn action-secondary"
                    :disabled="deactivateLoading"
                    @click="cancelDeactivate"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            </div>

            <div v-else class="reactivate-zone">
              <p class="inactive-badge">Cliente desactivado</p>
              <p v-if="reactivateError" class="confirm-error">{{ reactivateError }}</p>
              <button
                type="button"
                class="action-btn action-reactivate"
                :disabled="reactivateLoading"
                @click="confirmReactivate"
              >
                {{ reactivateLoading ? 'Procesando...' : 'Reactivar cliente' }}
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </AdminLayout>
</template>

<style scoped>
.ficha-page {
  max-width: 680px;
  margin: 0 auto;
}

/* ── Header ── */

.page-header {
  margin-bottom: 2rem;
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

.page-title {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 700;
  color: #111827;
}

/* ── Estados ── */

.state-box {
  background: white;
  border-radius: 16px;
  padding: 2.5rem;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.error-box {
  border: 1px solid #fecaca;
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

/* ── Ficha ── */

.ficha-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  display: flex;
  align-items: flex-start;
  gap: 1.5rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border: 1px solid #f3f4f6;
  margin-bottom: 1.25rem;
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #d1fae5;
  color: #065f46;
  font-size: 1.3rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  text-transform: uppercase;
}

.ficha-info {
  flex: 1;
  min-width: 0;
}

.cliente-name {
  margin: 0 0 1rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
}

.info-row {
  display: flex;
  gap: 1rem;
  align-items: baseline;
}

.info-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  width: 90px;
  flex-shrink: 0;
}

.info-value {
  font-size: 0.95rem;
  color: #374151;
  margin: 0;
}

/* ── Acciones ── */

.actions-card {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border: 1px solid #f3f4f6;
}

.actions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  padding: 0.7rem 1rem;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 600;
  text-decoration: none;
  text-align: center;
  cursor: pointer;
  border: 1.5px solid transparent;
  transition: background-color 0.15s, border-color 0.15s, color 0.15s;
  white-space: nowrap;
}

.action-inscribir-turno {
  background-color: #eff6ff;
  color: #1d4ed8;
  border-color: #bfdbfe;
}

.action-inscribir-turno:hover {
  background-color: #dbeafe;
  border-color: #93c5fd;
}

.action-inscribir-clase {
  background-color: #faf5ff;
  color: #7c3aed;
  border-color: #ddd6fe;
}

.action-inscribir-clase:hover {
  background-color: #ede9fe;
  border-color: #c4b5fd;
}

.action-secondary {
  background-color: #f9fafb;
  color: #374151;
  border-color: #e5e7eb;
}

.action-secondary:not([disabled]):hover {
  background-color: #f3f4f6;
  border-color: #d1d5db;
}

.action-secondary[disabled] {
  opacity: 0.45;
  cursor: not-allowed;
}

/* ── Zona de peligro ── */

.danger-zone {
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid #fee2e2;
}

.action-danger {
  background-color: #fff5f5;
  color: #dc2626;
  border-color: #fecaca;
}

.action-danger:not([disabled]):hover {
  background-color: #fef2f2;
  border-color: #fca5a5;
}

.action-danger[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Confirmar baja ── */

.confirm-box {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.confirm-text {
  margin: 0;
  font-size: 0.88rem;
  color: #374151;
  line-height: 1.5;
}

.confirm-error {
  margin: 0;
  font-size: 0.85rem;
  color: #dc2626;
}

.confirm-actions {
  display: flex;
  gap: 0.6rem;
}

/* ── Reactivar ── */

.reactivate-zone {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.inactive-badge {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 600;
  color: #6b7280;
}

.action-reactivate {
  background-color: #f0fdf4;
  color: #15803d;
  border-color: #bbf7d0;
}

.action-reactivate:not([disabled]):hover {
  background-color: #dcfce7;
  border-color: #86efac;
}

.action-reactivate[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 520px) {
  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
