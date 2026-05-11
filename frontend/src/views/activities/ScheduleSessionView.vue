<script setup lang="ts">
/**
 * ScheduleSessionView
 * -------------------
 * Vista de administración para programar un nuevo turno (ACT-06.01).
 *
 * Flujo:
 *   1. SessionForm valida los datos en el cliente y emite "submit-session".
 *   2. Esta vista llama a createSession() del servicio.
 *   3. Si el servidor responde con éxito, muestra un banner verde.
 *   4. Si el servidor retorna un error (turno duplicado, superposición, etc.),
 *      muestra el mensaje de error del backend en un banner rojo.
 *
 * ┌─ CONEXIÓN CON BACKEND ─────────────────────────────────────────┐
 * │  Hoy createSession() es un mock. Ver sessionService.ts y       │
 * │  /docs/integracion-backend.md para migrar al endpoint real.    │
 * └────────────────────────────────────────────────────────────────┘
 */
import { ref } from 'vue'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import SessionForm from '@/components/activities/SessionForm.vue'
import { createSession, type SessionData } from '@/services/sessionService'

const isSubmitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const handleSaveSession = async (sessionData: SessionData) => {
  isSubmitting.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const response = await createSession(sessionData)
    successMessage.value = (response as any).message
    // Desplazar al tope para que el banner de éxito sea visible
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (error: any) {
    // Los errores del backend (duplicado, superposición) llegan como excepciones.
    // El mensaje de error viene en error.message o en error.response.data.detail
    // según cómo esté configurado el cliente HTTP. Ver integracion-backend.md.
    errorMessage.value = error?.message ?? 'Ocurrió un error al programar el turno. Intentá de nuevo.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <!-- ── Encabezado de página ── -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Programar nuevo turno</h1>
          <p class="page-subtitle">Definí actividad, días, horario y cupo máximo para la clase</p>
        </div>
      </div>

      <!-- ── Banner de éxito ── -->
      <transition name="fade">
        <div v-if="successMessage" class="alert alert-success" role="alert">
          <span class="alert-icon">✓</span>
          <span>{{ successMessage }}</span>
          <button class="alert-close" @click="successMessage = ''" aria-label="Cerrar">×</button>
        </div>
      </transition>

      <!-- ── Banner de error del servidor (Escenarios 4 y 5) ── -->
      <transition name="fade">
        <div v-if="errorMessage" class="alert alert-error" role="alert">
          <span class="alert-icon">!</span>
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
/* El wrapper ocupa todo el ancho disponible del main-content */
.page-wrapper {
  width: 100%;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
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
  font-size: 1rem;
  font-weight: 700;
  flex-shrink: 0;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.alert-success .alert-icon {
  background-color: #16a34a;
  color: white;
  font-size: 0.8rem;
}

.alert-error .alert-icon {
  background-color: #dc2626;
  color: white;
  font-size: 0.85rem;
}

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

.alert-close:hover {
  opacity: 1;
}

/* ── Animación de entrada/salida de alertas ── */
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
