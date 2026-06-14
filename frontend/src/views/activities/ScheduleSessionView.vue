<script setup lang="ts">
/**
 * ScheduleSessionView — Vista de programación de turno (ACT-06.01)
 * ----------------------------------------------------------------
 * Orquesta el flujo completo: formulario → servicio → feedback al admin.
 *
 * Errores cubiertos por el backend (ver turno_service.py):
 *   - 404: La actividad no existe ("Actividad no encontrada.")
 *   - 409: Turno duplicado ("Ya existe un turno con esa descripción...") → Escenario 4
 *   - 422: Validación de campos (hora fin <= inicio, días repetidos, etc.)  → Escenario 2
 *   - 401: No autenticado ("No autenticado.")
 *   - 403: Sin permiso de admin ("Acceso denegado.")
 *
 * El formato de error del backend es siempre:
 *   { errors: { general: "mensaje" } }  ó  { errors: { campo: "mensaje" } }
 * Ver app/api/exception_handlers.py
 */
import { ref } from 'vue'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import SessionForm from '@/components/activities/SessionForm.vue'
import { createSession, extractBackendError, type SessionFormData } from '@/services/sessionService'
import { useRouter } from 'vue-router'

const isSubmitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const router = useRouter()

const sessionFormRef = ref<InstanceType<typeof SessionForm> | null>(null)
const showLeaveModal = ref(false)

function handleBack() {
  if (sessionFormRef.value?.isDirty) {
    showLeaveModal.value = true
  } else {
    router.push({ name: 'turnos-grilla' })
  }
}

function confirmLeave() {
  showLeaveModal.value = false
  router.push({ name: 'turnos-grilla' })
}

// null = sin error de auth | 'session' = 401 | 'forbidden' = 403
const authError = ref<null | 'session' | 'forbidden'>(null)

/**
 * Emitido por SessionForm cuando getFormOptions() devuelve 401 o 403.
 * En ambos casos ocultamos el formulario y mostramos el panel correspondiente.
 */
const handleAuthError = (status: number) => {
  authError.value = status === 403 ? 'forbidden' : 'session'
}

const handleSaveSession = async (formData: SessionFormData) => {
  isSubmitting.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const result = await createSession(formData)
    successMessage.value = result.message   // "Turno programado con éxito"
    setTimeout(() => {
      router.push({ name: 'turnos-grilla' })
    }, 1500)
  } catch (error) {
    const status = (error as { response?: { status?: number } })?.response?.status
    if (status === 401) {
      authError.value = 'session'
    } else if (status === 403) {
      authError.value = 'forbidden'
    } else {
      errorMessage.value = extractBackendError(error)
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <!-- ── Encabezado ── -->
      <div class="page-header">
        <div class="header-left">
          <button class="btn-back" @click="handleBack" title="Volver a la grilla">
            ← Volver
          </button>
          <div>
            <h1 class="page-title">Programar nuevo turno</h1>
            <p class="page-subtitle">Definí actividad, días, horario y cupo máximo para la clase</p>
          </div>
        </div>
      </div>

      <!-- ── Panel: sesión expirada (401) ── -->
      <div v-if="authError === 'session'" class="auth-panel">
        <div class="auth-icon">🔒</div>
        <h2 class="auth-title">Tu sesión expiró</h2>
        <p class="auth-desc">
          No podemos verificar tu identidad. Iniciá sesión nuevamente para continuar.
        </p>
        <button class="btn-login" @click="router.push({ name: 'login' })">
          Iniciar sesión
        </button>
      </div>

      <!-- ── Panel: sin permisos (403) ── -->
      <div v-else-if="authError === 'forbidden'" class="auth-panel auth-panel--forbidden">
        <div class="auth-icon">⛔</div>
        <h2 class="auth-title">Acceso denegado</h2>
        <p class="auth-desc">
          Solo los administradores pueden programar turnos. Contactá a tu administrador si creés que esto es un error.
        </p>
        <button class="btn-secondary" @click="router.push({ name: 'home' })">
          Volver al inicio
        </button>
      </div>

      <!-- ── Contenido normal (sin error de auth) ── -->
      <template v-else>

        <!-- ── Banner de éxito (Escenario 1) ── -->
        <transition name="fade">
          <div v-if="successMessage" class="alert alert-success" role="alert">
            <span class="alert-icon success-icon">✓</span>
            <span>{{ successMessage }}</span>
            <button class="alert-close" @click="successMessage = ''" aria-label="Cerrar">×</button>
          </div>
        </transition>

        <!-- ── Banner de error del servidor (Escenarios 4, 5 y otros) ── -->
        <transition name="fade">
          <div v-if="errorMessage" class="alert alert-error" role="alert">
            <span class="alert-icon error-icon">!</span>
            <span>{{ errorMessage }}</span>
            <button class="alert-close" @click="errorMessage = ''" aria-label="Cerrar">×</button>
          </div>
        </transition>

        <!-- ── Formulario ── -->
        <SessionForm
          ref="sessionFormRef"
          :is-loading="isSubmitting"
          @submit-session="handleSaveSession"
          @auth-error="handleAuthError"
        />

      </template>

    </div>
    <!-- ── Modal de confirmación al salir ── -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="showLeaveModal" class="modal-overlay" @click.self="showLeaveModal = false">
          <div class="modal" role="dialog" aria-modal="true" aria-labelledby="leave-modal-title">
            <div class="modal-header">
              <h2 id="leave-modal-title" class="modal-title">¿Salir sin guardar?</h2>
            </div>
            <div class="modal-body">
              <p class="modal-text">
                Tenés campos cargados en el formulario. Si salís ahora, los datos se perderán.
              </p>
            </div>
            <div class="modal-footer">
              <button class="btn-stay" @click="showLeaveModal = false">Seguir editando</button>
              <button class="btn-leave" @click="confirmLeave">Salir sin guardar</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </AdminLayout>
</template>

<style scoped>
.page-wrapper {
  width: 100%;
}

.page-header {
  margin-bottom: 2rem;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

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

.btn-back:hover {
  background-color: #f3f4f6;
  color: #374151;
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

/* ── Alertas ── */

.alert {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.9rem 1.25rem;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
}

.alert-success {
  background-color: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.alert-error {
  background-color: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.alert-icon {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
}

.success-icon { background-color: #16a34a; color: white; }
.error-icon   { background-color: #dc2626; color: white; }

.alert-close {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 1.4rem;
  line-height: 1;
  cursor: pointer;
  color: inherit;
  opacity: 0.5;
  padding: 0 0.2rem;
  flex-shrink: 0;
  transition: opacity 0.15s;
}

.alert-close:hover { opacity: 1; }

/* ── Paneles de error de autenticación ── */

.auth-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.85rem;
  padding: 4rem 2rem;
  border-radius: 12px;
  text-align: center;
  background-color: #fff5f5;
  border: 1px solid #fecaca;
}

.auth-panel--forbidden {
  background-color: #fff7ed;
  border-color: #fed7aa;
}

.auth-icon {
  font-size: 2.8rem;
  line-height: 1;
}

.auth-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #991b1b;
  margin: 0;
}

.auth-panel--forbidden .auth-title {
  color: #9a3412;
}

.auth-desc {
  font-size: 0.9rem;
  color: #7f1d1d;
  margin: 0;
  max-width: 400px;
  line-height: 1.55;
}

.auth-panel--forbidden .auth-desc {
  color: #7c2d12;
}

.btn-login {
  margin-top: 0.5rem;
  background-color: #11998e;
  color: white;
  font-size: 0.9rem;
  font-weight: 600;
  padding: 0.65rem 1.75rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-login:hover {
  background-color: #0c8a70;
}

.btn-secondary {
  margin-top: 0.5rem;
  background-color: #f3f4f6;
  color: #374151;
  font-size: 0.9rem;
  font-weight: 600;
  padding: 0.65rem 1.75rem;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-secondary:hover {
  background-color: #e5e7eb;
}

/* ── Animación alertas ── */

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s, transform 0.25s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ── Modal de confirmación ── */

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.modal {
  background: white;
  border-radius: 14px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.modal-header {
  padding: 1.25rem 1.5rem 0;
}

.modal-title {
  font-size: 1rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.modal-body {
  padding: 0.75rem 1.5rem 1.25rem;
}

.modal-text {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.55;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #f3f4f6;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-stay {
  background-color: #f3f4f6;
  color: #374151;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.55rem 1.2rem;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-stay:hover { background-color: #e5e7eb; }

.btn-leave {
  background-color: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.55rem 1.2rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-leave:hover { background-color: #fee2e2; }

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-active .modal,
.modal-fade-leave-active .modal {
  transition: transform 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .modal,
.modal-fade-leave-to .modal {
  transform: scale(0.95) translateY(-8px);
}
</style>
