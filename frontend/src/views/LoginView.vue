<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import AuthHeader from '@/components/auth/AuthHeader.vue'
import LoginForm from '@/components/auth/LoginForm.vue'
import { isAdminUser } from '@/utils/role'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const loading = ref(false)
const apiError = ref('')
const registroExitoso = ref(route.query.registered === 'true')
const googleErrorMessages: Record<string, string> = {
  google_not_registered: 'No encontramos una cuenta registrada con ese correo de Google. Registrate primero.',
  google_email_conflict: 'Este correo ya está registrado. Por favor, iniciá sesión con tu contraseña y vinculá Google desde tu perfil.',
  google_already_linked: 'Esa cuenta de Google ya está vinculada a un usuario existente. Intentá iniciar sesión.',
  google_error: 'Ocurrió un error al iniciar sesión con Google. Intentá de nuevo.',
}
const googleError = ref(googleErrorMessages[route.query.error as string] ?? '')

// 2FA step
const needs2FA = ref(false)
const preAuthToken = ref('')
const totpCode = ref('')
const totpError = ref('')
const totpLoading = ref(false)

const redirectAfterLogin = () => {
  const redirectParam = Array.isArray(route.query.redirect)
    ? route.query.redirect[0]
    : route.query.redirect
  if (typeof redirectParam === 'string' && redirectParam.startsWith('/')) {
    router.replace(redirectParam === '/home' ? '/list' : redirectParam)
    return
  }
  router.replace(isAdminUser(authStore.user) ? '/admin' : '/list')
}

const handleLogin = async (email: string, pass: string) => {
  loading.value = true
  apiError.value = ''
  try {
<<<<<<< HEAD
    const result = await authStore.login({ email, password: pass })
    if (result.requires_2fa) {
      preAuthToken.value = result.pre_auth_token!
      needs2FA.value = true
      return
    }
    redirectAfterLogin()
=======
    await authStore.login({ email, password: pass })

    const role = authStore.user?.role ?? ''
    const isAdmin = role === 'admin' || role === 'Admin' || role === 'Administrador'

    router.push(isAdmin ? { name: 'admin-home' } : { name: 'cliente-home' })
>>>>>>> c8d7b14 (feat: agregar enrutamiento de Inicio basado en roles (admin/cliente) y corregir la redireccion de sesion)
  } catch (err: any) {
    const errors = err?.response?.data?.errors
    apiError.value = (errors && Object.values(errors)[0]) || 'El email o la contraseña ingresados son incorrectos.'
  } finally {
    loading.value = false
  }
}

const handleVerify2FA = async () => {
  totpLoading.value = true
  totpError.value = ''
  try {
    await authStore.loginWith2FA(preAuthToken.value, totpCode.value)
    redirectAfterLogin()
  } catch {
    totpError.value = 'El código ingresado no es válido. Intentá de nuevo.'
    totpCode.value = ''
  } finally {
    totpLoading.value = false
  }
}

const handleGoogleLogin = () => {
  const apiBase = import.meta.env.VITE_API_URL.replace(/\/$/, '')
  window.location.href = `${apiBase}/auth/google?mode=login`
}
</script>

<template>
  <div class="auth-page-wrapper">
    <div class="auth-card">
      <AuthHeader subtitle="Bienvenido de nuevo" />

      <!-- Paso 2: verificación TOTP -->
      <template v-if="needs2FA">
        <p class="totp-intro">Ingresá el código de 6 dígitos de tu app de autenticación.</p>
        <div v-if="totpError" class="error-message">{{ totpError }}</div>
        <form @submit.prevent="handleVerify2FA" class="totp-form">
          <input
            v-model="totpCode"
            type="text"
            inputmode="numeric"
            maxlength="6"
            placeholder="000000"
            class="totp-input"
            autofocus
          />
          <button type="submit" class="totp-btn" :disabled="totpLoading || totpCode.length !== 6">
            {{ totpLoading ? 'Verificando...' : 'Verificar' }}
          </button>
        </form>
      </template>

      <!-- Paso 1: email y contraseña -->
      <template v-else>
        <div v-if="registroExitoso" class="success-message">
          Registro exitoso. Podés iniciar sesión.
        </div>
        <div v-if="googleError" class="error-message">
          {{ googleError }}
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
      </template>
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

.error-message {
  background-color: #fff5f5;
  color: #c0392b;
  padding: 12px;
  border-radius: 10px;
  font-size: 13px;
  border: 1px solid #fecaca;
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

.totp-intro {
  font-size: 14px;
  color: #4b5563;
  margin: 0 0 16px;
  line-height: 1.5;
}

.totp-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.totp-input {
  width: 100%;
  padding: 14px;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0.3em;
  text-align: center;
  border: 1.5px solid #d1d5db;
  border-radius: 12px;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.totp-input:focus {
  border-color: #00897b;
}

.totp-btn {
  width: 100%;
  padding: 13px;
  border-radius: 12px;
  border: none;
  background: #00897b;
  color: white;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s;
}

.totp-btn:hover:not(:disabled) { background: #00695c; }
.totp-btn:disabled { opacity: 0.55; cursor: not-allowed; }
</style>