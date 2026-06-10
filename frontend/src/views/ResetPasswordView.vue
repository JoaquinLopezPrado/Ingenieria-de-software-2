<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import AuthHeader from '@/components/auth/AuthHeader.vue'
import ResetPasswordForm from '@/components/auth/ResetPasswordForm.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const success = ref(false)
const tokenError = ref('')
const submitError = ref('')
const token = ref('')

onMounted(() => {
  token.value = String(route.query.token ?? '')
  if (!token.value) {
    tokenError.value = 'El enlace de recuperación es inválido o ha expirado.'
  }
})

const handleSubmit = async (newPassword: string) => {
  submitError.value = ''
  loading.value = true
  try {
    await authStore.resetPassword(token.value, newPassword)
    success.value = true
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    submitError.value = detail ?? 'El enlace de recuperación es inválido o ha expirado.'
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="page-wrapper">
    <div class="auth-card">
      <AuthHeader subtitle="Restablecer Contraseña" />

      <div v-if="tokenError" class="error-banner">
        <p>{{ tokenError }}</p>
        <router-link to="/forgot-password" class="link-accent">Solicitar un nuevo enlace</router-link>
      </div>

      <template v-else-if="success">
        <div class="success-banner">
          <p>¡Tu contraseña fue actualizada exitosamente!</p>
          <button class="btn-primary" @click="goToLogin">Ir al inicio de sesión</button>
        </div>
      </template>

      <template v-else>
        <p class="hint">Ingresá tu nueva contraseña.</p>
        <div v-if="submitError" class="error-inline">{{ submitError }}</div>
        <ResetPasswordForm :loading="loading" @submit="handleSubmit" />
      </template>
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
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.success-banner p {
  margin: 0;
}

.error-banner {
  background-color: #fdecea;
  color: #c62828;
  padding: 24px;
  border-radius: 16px;
  text-align: center;
  line-height: 1.6;
}

.error-banner p {
  margin: 0 0 12px 0;
}

.error-inline {
  background-color: #fdecea;
  color: #c62828;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 14px;
}

.link-accent {
  display: inline-block;
  color: #11a691;
  font-weight: 700;
  text-decoration: none;
}

.btn-primary {
  padding: 14px;
  background: #11a691;
  color: white;
  border: none;
  border-radius: 30px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  filter: brightness(1.1);
}
</style>
