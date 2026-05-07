<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import AuthHeader from '@/components/auth/AuthHeader.vue'
import RegisterForm from '@/components/auth/RegisterForm.vue'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

const handleRegister = async (email: string, pass: string) => {
  loading.value = true
  try {
    await authStore.register(email, pass)
    router.push('/login')
  } catch (err) { /* Manejo de error */ }
  finally { loading.value = false }
}
</script>

<template>
  <div class="auth-page-wrapper">
    <div class="auth-card">
      <AuthHeader subtitle="Únete a nuestra comunidad" />
      <RegisterForm :loading="loading" @submit="handleRegister" />
      <div class="auth-footer">
        <div class="signup-prompt">
          <span>¿Ya tienes cuenta?</span>
          <router-link to="/login" class="link-accent">Inicia sesión</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #dff8f2 0%, #cfeee6 100%);
  padding: 20px;
}
.auth-card {
  background: white;
  padding: 40px;
  border-radius: 24px;
  box-shadow: 0 15px 35px rgba(13, 110, 95, 0.1);
  width: 100%;
  max-width: 420px;
}
.auth-footer { margin-top: 24px; text-align: center; }
.signup-prompt {
  font-size: 14px;
  color: #546e7a; /* Un gris azulado más oscuro para que sea legible */
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.link-accent {
  color: #11a691;
  text-decoration: none;
  font-weight: 700;
  /* Opcional: un ligero subrayado para que se note más que es un link */
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s;
}

.link-accent:hover {
  border-bottom-color: #11a691;
}
</style>