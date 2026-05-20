<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import AuthHeader from '@/components/auth/AuthHeader.vue'
import RegisterForm from '@/components/auth/RegisterForm.vue'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

const handleRegister = async (userData: any) => {
  loading.value = true
  try {
    await authStore.register(userData)
    router.push('/')
  } catch (err: any) {
    const message = err.response?.data?.errors?.general || 'Error en el registro'
    alert(message)
  } finally {
    loading.value = false
  }
}

const handleGoogleRegister = async () => {
  loading.value = true
  try {
    console.log('Iniciando flujo de OAuth con Google para registro...')
  } catch (err: any) {
    alert('Hubo un problema al registrarse con Google')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page-wrapper">
    <div class="auth-card">
      <AuthHeader subtitle="Únete a nuestra comunidad" />
      
      <RegisterForm 
        :loading="loading" 
        @submit="handleRegister" 
        @google-register="handleGoogleRegister" 
      />
      
      <div class="auth-footer">
        <div class="signup-prompt">
          <span>¿Ya tienes cuenta?</span>
          <router-link to="/" class="link-accent">Inicia sesión</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ESTILOS BASE: Celulares (<768px) */
.auth-page-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #dff8f2 0%, #cfeee6 100%);
  padding: 16px;
}

.auth-card {
  background: white;
  padding: 24px;
  border-radius: 24px;
  box-shadow: 0 15px 35px rgba(13, 110, 95, 0.1);
  width: 100%;
}

.auth-footer {
  margin-top: 20px;
  text-align: center;
}

.signup-prompt {
  font-size: 14px;
  color: #546e7a;
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

/* RESPONSIVE: Escritorios y Tablets (>=768px) */
@media (min-width: 768px) {
  .auth-page-wrapper {
    padding: 20px;
  }

  .auth-card {
    padding: 40px;
    max-width: 480px;
  }

  .auth-footer {
    margin-top: 24px;
  }

  .signup-prompt {
    flex-direction: row;
    justify-content: center;
    gap: 6px;
  }
}
</style>