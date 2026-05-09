<script setup lang="ts">
import { ref } from 'vue'
import SessionForm from '@/components/activities/SessionForm.vue'
import { createSession, type SessionData } from '@/services/sessionService'

const isSubmitting = ref(false)

const handleSaveSession = async (newSessionData: SessionData) => {
  isSubmitting.value = true
  try {
    const response = await createSession(newSessionData)
    // TypeScript a veces no sabe qué trae nuestra respuesta falsa, le avisamos que tiene 'message'
    alert((response as any).message)
  } catch (error) {
    console.error("Error al guardar la sesión:", error)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="schedule-container">
    <div class="schedule-content">
      <div class="header">
        <h1 class="page-title">Crear Nuevo Turno</h1>
        <p class="page-subtitle">Define dias, horarios, y capacidad para las nuevas clases.</p>
      </div>

      <SessionForm 
        :is-loading="isSubmitting"
        @submit-session="handleSaveSession" 
      />
    </div>
  </div>
</template>

<style scoped>
.schedule-container {
  padding: 3rem 2rem;
  min-height: 100vh;
  display: flex;
  justify-content: center;
}

.schedule-content {
  width: 100%;
  max-width: 800px;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.page-subtitle {
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 2rem;
  margin-top: 0;
}
</style>