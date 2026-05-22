<script setup lang="ts">
import { ref } from 'vue'
import PasswordInput from './PasswordInput.vue'

const props = defineProps<{
  loading?: boolean
  apiError?: string
}>()

const emit = defineEmits<{
  submit: [email: string, password: string]
  'google-login': []
}>()

const email = ref('')
const password = ref('')
const validationError = ref('')

const handleSubmit = () => {
  if (!email.value || !password.value) {
    validationError.value = 'Por favor completa todos los campos'
    return
  }
  validationError.value = ''
  emit('submit', email.value, password.value)
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="login-form">
    <div class="form-group">
      <label for="email" class="custom-label">Email</label>
      <input
        id="email"
        v-model="email"
        type="email"
        placeholder="tu@email.com"
        class="input-field"
        :disabled="loading"
      />
    </div>

    <PasswordInput
      v-model="password"
      label="Contraseña"
      :disabled="loading"
    />

    <div v-if="validationError || apiError" class="error-message">
      {{ validationError || apiError }}
    </div>

    <button type="submit" class="btn-primary" :disabled="loading">
      <span>{{ loading ? 'Iniciando sesión...' : 'Iniciar Sesión' }}</span>
    </button>

    <div class="oauth-divider">
      <span>o</span>
    </div>

    <button 
      type="button" 
      class="btn-google" 
      @click="emit('google-login')" 
      :disabled="loading"
    >
      <svg class="google-icon" viewBox="0 0 24 24" width="20" height="20" xmlns="http://www.w3.org/2000/svg">
        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
      </svg>
      <span>Continuar con Google</span>
    </button>
  </form>
</template>

<style scoped>
.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.custom-label {
  font-weight: 700;
  color: #00897b;
  font-size: 13px;
  margin-left: 4px;
}

.input-field {
  padding: 14px 16px;
  background-color: #f8fbfb;
  border: 2px solid #e0f2f1;
  border-radius: 12px;
  font-size: 14px;
  transition: all 0.2s ease;
}

.input-field:focus {
  outline: none;
  border-color: #11a691;
  background-color: #fff;
  box-shadow: 0 4px 12px rgba(17, 166, 145, 0.08);
}

.error-message {
  background-color: #fff5f5;
  color: #e53935;
  padding: 12px;
  border-radius: 10px;
  font-size: 13px;
  border: 1px solid #ffcdd2;
}

.btn-primary {
  padding: 16px 20px;
  background: #11a691;
  color: white;
  border: none;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 15px rgba(17, 166, 145, 0.25);
  margin-top: 10px;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(17, 166, 145, 0.35);
  filter: brightness(1.1);
}

.btn-primary:disabled {
  background-color: #b2dfdb;
  cursor: not-allowed;
  box-shadow: none;
}

.oauth-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #7f8c8d;
  font-size: 14px;
  margin: 10px 0;
  width: 100%;
}

.oauth-divider::before,
.oauth-divider::after {
  content: '';
  flex: 1;
  border-bottom: 2px solid #e0f2f1;
}

.oauth-divider span {
  padding: 0 12px;
  background-color: #ffffff; 
  color: #99afad;
  font-weight: 600;
}

.btn-google {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  padding: 16px 20px;
  background: #ffffff;
  color: #2c3e50;
  border: 2px solid #e0f2f1;
  border-radius: 30px; 
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.02);
}

.btn-google:hover:not(:disabled) {
  background-color: #f8fbfb;
  border-color: #11a691; 
  color: #11a691;
  box-shadow: 0 4px 12px rgba(17, 166, 145, 0.1);
}

.btn-google:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.google-icon {
  flex-shrink: 0;
}
</style>