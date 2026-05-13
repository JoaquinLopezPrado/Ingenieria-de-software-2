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

const isSubmitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const handleSaveSession = async (formData: SessionFormData) => {
  isSubmitting.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const result = await createSession(formData)
    successMessage.value = result.message   // "Turno programado con éxito"
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (error) {
    // extractBackendError lee error.response.data.errors del formato de FastAPI
    errorMessage.value = extractBackendError(error)
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
        <div>
          <h1 class="page-title">Programar nuevo turno</h1>
          <p class="page-subtitle">Definí actividad, días, horario y cupo máximo para la clase</p>
        </div>
      </div>

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
        :is-loading="isSubmitting"
        @submit-session="handleSaveSession"
      />

    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper {
  width: 100%;
}

.page-header {
  margin-bottom: 2rem;
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

/* ── Animación ── */

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s, transform 0.25s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
