<script setup lang="ts">
/**
 * EditActividadView — HU: Modificar Actividad
 * --------------------------------------------
 * Escenarios cubiertos:
 *   1. Acceso desde el listado → form pre-cargado con nombre, descripción y estado
 *   2. Edición exitosa → guarda y retorna al listado
 *   3. Cancelar → descarta cambios y retorna al listado
 *   4. Nombre vacío → bloquea guardado con mensaje de error inline
 *   5. Desactivación con clientes afectados → modal de confirmación con conteo
 *   6. Desactivación sin clientes afectados → guarda directamente
 *   7. Cancelar desde el modal → retorna al listado (no al form)
 *
 * RN6, RN7 (cancelar clases futuras, acreditar saldo, enviar emails) → backend.
 */
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import {
  getActivityById,
  updateActivity,
  getDeactivationImpact,
  extractBackendError,
  type ActivityOption,
} from '@/services/sessionService'

const route  = useRoute()
const router = useRouter()
const id     = Number(route.params.id)

// ─── Estado ───────────────────────────────────────────────────────────────────

const original   = ref<ActivityOption | null>(null)
const isLoading  = ref(true)
const isSaving   = ref(false)
const loadError  = ref('')
const serverError = ref('')
const successMsg = ref('')

const form = ref({
  name:        '',
  description: '',
  is_active:   true,
})

const errors = ref<Record<string, string>>({})

// ─── Modal de confirmación (Esc. 5 y 7) ──────────────────────────────────────

const showModal       = ref(false)
const affectedClients = ref(0)
const isCheckingImpact = ref(false)

// ─── Carga inicial (Escenario 1) ──────────────────────────────────────────────

onMounted(async () => {
  try {
    const activity   = await getActivityById(id)
    original.value   = activity
    form.value = {
      name:        activity.name,
      description: activity.description ?? '',
      is_active:   activity.is_active,
    }
  } catch (e: unknown) {
    loadError.value = extractBackendError(e)
  } finally {
    isLoading.value = false
  }
})

// ─── Validación (Escenario 4) ─────────────────────────────────────────────────

function validate(): boolean {
  errors.value = {}
  if (!form.value.name.trim())
    errors.value.name = 'El nombre es un campo requerido.'
  return Object.keys(errors.value).length === 0
}

// ─── Submit principal ─────────────────────────────────────────────────────────

async function handleSubmit() {
  serverError.value = ''
  if (!validate()) return

  const wasActive    = original.value?.is_active ?? true
  const willInactive = wasActive && !form.value.is_active

  // Si el admin desactiva una actividad activa → verificar impacto (RN8)
  if (willInactive) {
    isCheckingImpact.value = true
    try {
      const impact = await getDeactivationImpact(id)
      affectedClients.value = impact.affected_clients

      if (affectedClients.value > 0) {
        // Escenario 5: hay clientes afectados → mostrar modal
        showModal.value = true
        return
      }
      // Escenario 6: sin clientes afectados → guardar directo
      await saveChanges()
    } catch {
      // Si el endpoint de impacto falla, guardar igual (degradación graceful)
      await saveChanges()
    } finally {
      isCheckingImpact.value = false
    }
    return
  }

  // Sin cambio de estado → guardar directo (Escenario 2)
  await saveChanges()
}

// ─── Guardar (Escenarios 2, 5, 6) ────────────────────────────────────────────

async function saveChanges() {
  isSaving.value = true
  showModal.value = false
  try {
    await updateActivity(id, {
      name:        form.value.name.trim(),
      description: form.value.description.trim(),
      is_active:   form.value.is_active,
    })
    successMsg.value = 'Actividad actualizada con éxito.'
    setTimeout(() => router.push({ name: 'lista-actividades' }), 1500)
  } catch (e: unknown) {
    serverError.value = extractBackendError(e)
  } finally {
    isSaving.value = false
  }
}

// ─── Cancelar desde el modal (Escenario 7) ───────────────────────────────────

function cancelFromModal() {
  showModal.value = false
  // La HU especifica que cancelar en el modal retorna al listado
  router.push({ name: 'lista-actividades' })
}

// ─── Cancelar desde el form (Escenario 3) ────────────────────────────────────

function cancelEdit() {
  router.push({ name: 'lista-actividades' })
}
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <!-- ── Encabezado ── -->
      <div class="page-header">
        <div class="header-left">
          <button class="btn-back" @click="cancelEdit">← Volver</button>
          <div>
            <h1 class="page-title">Editar actividad</h1>
            <p class="page-subtitle">Modificá los datos de la actividad y guardá los cambios</p>
          </div>
        </div>
      </div>

      <!-- ── Cargando ── -->
      <div v-if="isLoading" class="skeleton-wrapper">
        <div class="skeleton-row" style="width: 220px; height: 32px;"></div>
        <div class="skeleton-row" style="height: 320px; margin-top: 0.5rem;"></div>
      </div>

      <!-- ── Error de carga ── -->
      <div v-else-if="loadError" class="state-panel state-error">
        <div class="state-icon">⚠</div>
        <h2 class="state-title">No se pudo cargar la actividad</h2>
        <p class="state-desc">{{ loadError }}</p>
        <button class="btn-secondary" @click="router.go(0)">Reintentar</button>
      </div>

      <!-- ── Formulario ── -->
      <template v-else>

        <!-- Banner éxito -->
        <Transition name="fade">
          <div v-if="successMsg" class="alert alert-success">
            <span class="alert-icon success-icon">✓</span>
            <span>{{ successMsg }}</span>
          </div>
        </Transition>

        <!-- Banner error servidor -->
        <Transition name="fade">
          <div v-if="serverError" class="alert alert-error">
            <span class="alert-icon error-icon">!</span>
            <span>{{ serverError }}</span>
            <button class="alert-close" @click="serverError = ''">×</button>
          </div>
        </Transition>

        <div class="form-card">
          <form @submit.prevent="handleSubmit" novalidate>

            <!-- ── Nombre (Escenario 4) ── -->
            <div class="input-group">
              <label for="nombre">Nombre</label>
              <input
                id="nombre"
                type="text"
                v-model="form.name"
                maxlength="120"
                placeholder="Nombre de la actividad"
                :class="{ 'input-error': errors.name }"
              />
              <span v-if="errors.name" class="field-error">{{ errors.name }}</span>
            </div>

            <!-- ── Descripción ── -->
            <div class="input-group">
              <label for="descripcion">Descripción</label>
              <textarea
                id="descripcion"
                v-model="form.description"
                maxlength="500"
                rows="4"
                placeholder="Descripción de la actividad (opcional)"
              ></textarea>
            </div>

            <!-- ── Estado ── -->
            <div class="input-group">
              <label>Estado</label>
              <div class="estado-options">
                <label class="radio-label">
                  <input type="radio" v-model="form.is_active" :value="true" />
                  <span class="radio-chip chip-active">Activa</span>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="form.is_active" :value="false" />
                  <span class="radio-chip chip-inactive">Inactiva</span>
                </label>
              </div>
              <p v-if="original?.is_active && !form.is_active" class="deactivation-warning">
                ⚠ Al desactivar esta actividad, los turnos futuros asociados serán cancelados y los clientes notificados.
              </p>
            </div>

            <!-- ── Acciones (Escenarios 2, 3) ── -->
            <div class="form-actions">
              <button
                type="button"
                class="btn-cancel"
                :disabled="isSaving || isCheckingImpact"
                @click="cancelEdit"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="btn-submit"
                :disabled="isSaving || isCheckingImpact"
              >
                {{ isSaving || isCheckingImpact ? 'Guardando...' : 'Aceptar' }}
              </button>
            </div>

          </form>
        </div>

      </template>

      <!-- ── Modal de confirmación (Escenarios 5 y 7) ── -->
      <Teleport to="body">
        <Transition name="fade">
          <div v-if="showModal" class="modal-overlay" @click.self="cancelFromModal">
            <div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="modal-title">

              <div class="modal-icon">⚠️</div>
              <h2 id="modal-title" class="modal-title">Confirmar desactivación</h2>

              <p class="modal-text">
                Esta acción cancelará todos los turnos futuros de esta actividad.
                <strong>{{ affectedClients }} cliente{{ affectedClients !== 1 ? 's' : '' }}</strong>
                {{ affectedClients !== 1 ? 'serán compensados' : 'será compensado' }} con una clase a favor y
                {{ affectedClients !== 1 ? 'recibirán' : 'recibirá' }} un correo de notificación.
              </p>
              <p class="modal-subtext">No se realizarán devoluciones de dinero.</p>

              <div class="modal-actions">
                <button
                  class="btn-modal-cancel"
                  @click="cancelFromModal"
                  :disabled="isSaving"
                >
                  Cancelar
                </button>
                <button
                  class="btn-modal-confirm"
                  @click="saveChanges"
                  :disabled="isSaving"
                >
                  {{ isSaving ? 'Guardando...' : 'Confirmar' }}
                </button>
              </div>

            </div>
          </div>
        </Transition>
      </Teleport>

    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper { width: 100%; }

/* ── Encabezado ── */

.page-header { display: flex; align-items: flex-start; margin-bottom: 1.75rem; }
.header-left { display: flex; align-items: flex-start; gap: 1rem; }

.btn-back {
  margin-top: 4px;
  background: none;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0.4rem 0.9rem;
  font-size: 0.82rem;
  color: #6b7280;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.15s, color 0.15s;
}
.btn-back:hover { background-color: #f3f4f6; color: #374151; }

.page-title    { font-size: 1.5rem; font-weight: 700; color: #1f2937; margin: 0 0 0.2rem 0; }
.page-subtitle { color: #6b7280; font-size: 0.88rem; margin: 0; }

/* ── Skeleton ── */

.skeleton-wrapper { display: flex; flex-direction: column; gap: 0.75rem; }

.skeleton-row {
  border-radius: 8px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Estado de error de carga ── */

.state-panel {
  display: flex; flex-direction: column; align-items: center;
  gap: 0.75rem; padding: 4rem 2rem; border-radius: 12px; text-align: center;
}
.state-error   { background: #fff5f5; border: 1px solid #fecaca; }
.state-icon    { font-size: 2.5rem; line-height: 1; }
.state-title   { font-size: 1.05rem; font-weight: 700; margin: 0; color: #991b1b; }
.state-desc    { font-size: 0.9rem; color: #7f1d1d; margin: 0; max-width: 420px; }

/* ── Alertas ── */

.alert {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.9rem 1.25rem; border-radius: 10px;
  font-size: 0.9rem; font-weight: 500; margin-bottom: 1.25rem;
}
.alert-success { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
.alert-error   { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }

.alert-icon {
  width: 1.4rem; height: 1.4rem; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.78rem; font-weight: 700; flex-shrink: 0;
}
.success-icon { background: #16a34a; color: white; }
.error-icon   { background: #dc2626; color: white; }

.alert-close {
  margin-left: auto; background: none; border: none; font-size: 1.4rem;
  cursor: pointer; color: inherit; opacity: 0.5; transition: opacity 0.15s;
}
.alert-close:hover { opacity: 1; }

/* ── Formulario ── */

.form-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 2rem 2.5rem;
  max-width: 680px;
}

.input-group { margin-bottom: 1.5rem; }

label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 0.45rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

input[type="text"],
textarea {
  width: 100%;
  padding: 0.7rem 0.9rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #fafafa;
  font-size: 0.95rem;
  color: #1f2937;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s, background-color 0.2s;
  font-family: inherit;
  resize: vertical;
}

input:focus, textarea:focus {
  border-color: #11998e;
  background-color: #fff;
  box-shadow: 0 0 0 3px rgba(17, 153, 142, 0.15);
}

.input-error {
  border-color: #ef4444 !important;
  background-color: #fff5f5 !important;
}

.field-error {
  display: block; margin-top: 0.35rem;
  font-size: 0.78rem; color: #dc2626; font-weight: 500;
}

/* ── Estado (radio) ── */

.estado-options {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.radio-label {
  cursor: pointer;
  text-transform: none;
  letter-spacing: 0;
  font-size: 1rem;
  font-weight: normal;
}

.radio-label input[type="radio"] { display: none; }

.radio-chip {
  display: inline-block;
  padding: 0.45rem 1.2rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 600;
  border: 2px solid transparent;
  transition: all 0.15s;
  user-select: none;
}

.chip-active  { background: #f0fdf4; color: #15803d; border-color: #bbf7d0; }
.chip-inactive { background: #f3f4f6; color: #6b7280; border-color: #e5e7eb; }

.radio-label input[type="radio"]:checked + .chip-active  {
  background: #16a34a; color: white; border-color: #16a34a;
}
.radio-label input[type="radio"]:checked + .chip-inactive {
  background: #6b7280; color: white; border-color: #6b7280;
}

.deactivation-warning {
  margin: 0.6rem 0 0;
  font-size: 0.82rem;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  font-weight: 500;
}

/* ── Acciones ── */

.form-actions {
  display: flex; justify-content: flex-end; gap: 0.75rem;
  padding-top: 1.5rem; margin-top: 0.5rem;
  border-top: 1px solid #f3f4f6;
}

.btn-cancel {
  background: #f3f4f6; color: #374151; font-size: 0.9rem; font-weight: 600;
  padding: 0.7rem 1.5rem; border-radius: 8px; border: 1px solid #d1d5db;
  cursor: pointer; transition: background-color 0.15s;
}
.btn-cancel:hover:not(:disabled) { background: #e5e7eb; }
.btn-cancel:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-submit {
  background: #11998e; color: white; font-weight: 600; font-size: 0.95rem;
  padding: 0.7rem 2rem; border-radius: 8px; border: none; cursor: pointer;
  min-width: 120px; transition: background-color 0.2s;
}
.btn-submit:hover:not(:disabled) { background: #0c8a70; }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-secondary {
  background: #f3f4f6; color: #374151; font-size: 0.88rem; font-weight: 600;
  padding: 0.6rem 1.4rem; border-radius: 8px; border: 1px solid #d1d5db;
  cursor: pointer; transition: background-color 0.15s;
}
.btn-secondary:hover { background: #e5e7eb; }

/* ── Modal ── */

.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex; align-items: center; justify-content: center;
  padding: 1.5rem; z-index: 1000;
}

.modal-box {
  background: white; border-radius: 16px;
  padding: 2rem 2rem 1.75rem;
  max-width: 420px; width: 100%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
  text-align: center;
}

.modal-icon  { font-size: 2.5rem; margin-bottom: 0.75rem; line-height: 1; }

.modal-title {
  font-size: 1.1rem; font-weight: 700; color: #1f2937;
  margin: 0 0 1rem;
}

.modal-text {
  font-size: 0.9rem; color: #374151; line-height: 1.6;
  margin: 0 0 0.5rem;
}

.modal-subtext {
  font-size: 0.8rem; color: #9ca3af; margin: 0 0 1.5rem;
}

.modal-actions {
  display: flex; gap: 0.75rem; justify-content: center;
}

.btn-modal-cancel {
  background: #f3f4f6; color: #374151; font-size: 0.9rem; font-weight: 600;
  padding: 0.65rem 1.5rem; border-radius: 8px; border: 1px solid #d1d5db;
  cursor: pointer; transition: background-color 0.15s; flex: 1;
}
.btn-modal-cancel:hover:not(:disabled) { background: #e5e7eb; }

.btn-modal-confirm {
  background: #dc2626; color: white; font-size: 0.9rem; font-weight: 600;
  padding: 0.65rem 1.5rem; border-radius: 8px; border: none;
  cursor: pointer; transition: background-color 0.15s; flex: 1;
}
.btn-modal-confirm:hover:not(:disabled) { background: #b91c1c; }

.btn-modal-cancel:disabled,
.btn-modal-confirm:disabled { opacity: 0.6; cursor: not-allowed; }

/* ── Transiciones ── */

.fade-enter-active, .fade-leave-active { transition: opacity 0.25s, transform 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-6px); }

@media (max-width: 480px) {
  .form-card { padding: 1.5rem 1.25rem; }
  .form-actions { flex-direction: column-reverse; }
  .btn-submit, .btn-cancel { width: 100%; }
  .modal-actions { flex-direction: column; }
}
</style>
