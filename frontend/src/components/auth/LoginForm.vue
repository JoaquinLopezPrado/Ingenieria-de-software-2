<script setup lang="ts">
import { ref } from 'vue'
import PasswordInput from './PasswordInput.vue'

defineProps<{
  loading?: boolean
}>()

const emit = defineEmits<{
  submit: [email: string, password: string]
}>()

const email = ref('')
const password = ref('')
const error = ref('')

const handleSubmit = () => {
  if (!email.value || !password.value) {
    error.value = 'Por favor completa todos los campos'
    return
  }
  error.value = ''
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

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <button type="submit" class="btn-primary" :disabled="loading">
      <span>{{ loading ? 'Iniciando sesión...' : 'Iniciar Sesión ' }}</span>
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
  border-radius: 30px; /* Bordes muy redondeados como el de la foto */
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
</style>