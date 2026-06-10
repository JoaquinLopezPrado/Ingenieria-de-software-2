<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import AuthHeader from '@/components/auth/AuthHeader.vue'
import ForgotPasswordForm from '@/components/auth/ForgotPasswordForm.vue'

const authStore = useAuthStore()

const loading = ref(false)
const success = ref(false)

const handleSubmit = async (email: string) => {
  loading.value = true
  try {
    await authStore.forgotPassword(email)
  } finally {
    success.value = true
    loading.value = false
  }
}
</script>

<template>
  <div class="page-wrapper">
    <div class="auth-card">
      <AuthHeader subtitle="Recuperar Contraseña" />

      <div v-if="success" class="success-banner">
        <p>Si el correo está registrado, recibirás las instrucciones en breve.</p>
        <router-link to="/login" class="link-accent">← Volver al inicio de sesión</router-link>
      </div>

      <template v-else>
        <p class="hint">
          Ingresá tu correo electrónico y te enviaremos un enlace para restablecer tu contraseña.
        </p>
        <ForgotPasswordForm :loading="loading" @submit="handleSubmit" />
      </template>

      <div v-if="!success" class="footer-note">
        <router-link to="/login" class="link-secondary">← Volver al inicio de sesión</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  width: 100vw;
  position: fixed;
  top: 0;
  left: 0;
  background: linear-gradient(135deg, #dff8f2 0%, #cfeee6 100%);
  z-index: 999;
}

.auth-card {
  background: white;
  padding: 40px;
  border-radius: 24px;
  box-shadow: 0 15px 35px rgba(13, 110, 95, 0.1);
  width: 90%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hint {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

.success-banner {
  background-color: #e8f4f1;
  color: #00897b;
  padding: 24px;
  border-radius: 16px;
  text-align: center;
  line-height: 1.6;
}

.success-banner p {
  margin: 0 0 12px 0;
}

.link-accent {
  display: inline-block;
  color: #11a691;
  font-weight: 700;
  text-decoration: none;
}

.footer-note {
  padding-top: 8px;
  border-top: 1px solid #eef2f1;
  text-align: center;
}

.link-secondary {
  color: #7f8c8d;
  font-size: 14px;
  text-decoration: none;
}
</style>
