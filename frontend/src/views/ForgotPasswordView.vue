<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import AuthHeader from '@/components/auth/AuthHeader.vue'
import ForgotPasswordForm from '@/components/auth/ForgotPasswordForm.vue'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const success = ref(false)

const handleForgotPassword = async (email: string) => {
  loading.value = true
  try {
    await authStore.forgotPassword(email)
    success.value = true
    // Redirigir a login después de 3 segundos
    setTimeout(() => {
      router.push('/')
    }, 3000)
  } catch (err: any) {
    // El error se maneja en ForgotPasswordForm
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="forgot-container">
    <div class="forgot-card">
      <AuthHeader subtitle="Recuperar Contraseña" />

      <div v-if="success" class="success-message">
        <p>✓ Se ha enviado un email con las instrucciones para recuperar tu contraseña.</p>
        <p class="small">Redirigiendo al login en unos segundos...</p>
      </div>

      <ForgotPasswordForm v-else :loading="loading" @submit="handleForgotPassword" />

      <div class="forgot-footer">
        <router-link to="/login" class="link-back">
          ← Volver al inicio de sesión
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.forgot-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.forgot-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 400px;
}

.success-message {
  background-color: #efe;
  color: #3c3;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #3c3;
}

.success-message p {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.success-message .small {
  font-size: 12px;
  opacity: 0.8;
  margin-bottom: 0;
}

.forgot-footer {
  margin-top: 20px;
  text-align: center;
}

.link-back {
  color: #667eea;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.3s;
}

.link-back:hover {
  color: #764ba2;
  text-decoration: underline;
}
</style>