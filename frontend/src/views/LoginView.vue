<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import AuthHeader from '@/components/auth/AuthHeader.vue'
import LoginForm from '@/components/auth/LoginForm.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const loading = ref(false)
const apiError = ref('')
const registroExitoso = ref(route.query.registered === 'true')

const handleLogin = async (email: string, pass: string) => {
  loading.value = true
  apiError.value = ''
  try {
    await authStore.login({ email, password: pass })
    router.replace('/home')
  } catch (err: any) {
    const errors = err?.response?.data?.errors
    apiError.value = (errors && Object.values(errors)[0]) || 'El email o la contraseña ingresados son incorrectos.'
  } finally {
    loading.value = false
  }
}

const handleGoogleLogin = async () => {
  loading.value = true
  try {
    console.log('Iniciando flujo de OAuth con Google...')
  } catch (err: any) {
    alert('Hubo un problema al iniciar sesión con Google')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page-wrapper">
    <div class="auth-card">
      <AuthHeader subtitle="Bienvenido de nuevo" />
      
      <div v-if="registroExitoso" class="success-message">
        Registro exitoso. Podés iniciar sesión.
      </div>

      <LoginForm
        :loading="loading"
        :api-error="apiError"
        @submit="handleLogin"
        @google-login="handleGoogleLogin"
      />
      
      <div class="auth-footer">
        <router-link to="/forgot-password" class="link-secondary">
          ¿Olvidaste tu contraseña?
        </router-link>
        <div class="divider"></div>
        <div class="signup-prompt">
          <span>¿No tienes cuenta?</span>
          <router-link to="/register" class="link-accent">Crea una aquí</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.success-message {
  background-color: #f0fdf4;
  color: #16a34a;
  padding: 12px;
  border-radius: 10px;
  font-size: 13px;
  border: 1px solid #bbf7d0;
  margin-bottom: 4px;
}
/* ESTILOS BASE: Celulares (<768px) */
.auth-page-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #dff8f2 0%, #cfeee6 50%, #e6f8f0 100%);
  padding: 16px;
}

.auth-card {
  background: white;
  padding: 40px;
  border-radius: 24px; 
  box-shadow: 0 15px 35px rgba(13, 110, 95, 0.1);
  width: 100%;
}

.auth-footer {
  margin-top: 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.divider {
  height: 1px;
  background-color: #e0f2f1;
  width: 100%;
}

.link-secondary {
  color: #7f8c8d;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.link-secondary:hover {
  color: #00897b;
}

.signup-prompt {
  font-size: 14px;
  color: #2c3e50;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.link-accent {
  color: #11a691;
  text-decoration: none;
  font-weight: 700;
}

.link-accent:hover {
  text-decoration: underline;
}

/* RESPONSIVE: Escritorios y Tablets (>=768px) */
@media (min-width: 768px) {
  .auth-page-wrapper {
    padding: 20px;
  }

  .auth-card {
    padding: 40px;
    max-width: 420px;
  }

  .auth-footer {
    margin-top: 32px;
  }

  .signup-prompt {
    flex-direction: row;
    justify-content: center;
    gap: 8px;
  }
}
</style>