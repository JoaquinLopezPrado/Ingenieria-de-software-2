<script setup lang="ts">
import { ref } from 'vue'
import PasswordInput from './PasswordInput.vue'

defineProps<{
  loading?: boolean
}>()

const emit = defineEmits<{
  submit: [email: string, password: string, birthDate: string]
}>()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const birthDate = ref('') // Guardamos la fecha como string "YYYY-MM-DD"
const error = ref('')

// Función para calcular la edad
const calculateAge = (birthday: string) => {
  const today = new Date()
  const birthDateObj = new Date(birthday)
  let age = today.getFullYear() - birthDateObj.getFullYear()
  const monthDiff = today.getMonth() - birthDateObj.getMonth()
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDateObj.getDate())) {
    age--
  }
  return age
}

const handleSubmit = () => {
  if (!email.value || !password.value || !confirmPassword.value || !birthDate.value) {
    error.value = 'Por favor completa todos los campos'
    return
  }

  // Validación de mayoría de edad (18+)
  if (calculateAge(birthDate.value) < 18) {
    error.value = 'Debes ser mayor de 18 años para registrarte'
    return
  }

  if (password.value !== confirmPassword.value) {
    error.value = 'Las contraseñas no coinciden'
    return
  }

  error.value = ''
  emit('submit', email.value, password.value, birthDate.value)
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="register-form">
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

    <div class="form-group">
      <label for="birthDate" class="custom-label">Fecha de nacimiento</label>
      <input
        id="birthDate"
        v-model="birthDate"
        type="date"
        class="input-field custom-date"
        :disabled="loading"
      />
    </div>

    <PasswordInput v-model="password" label="Contraseña" :disabled="loading" />
    <PasswordInput v-model="confirmPassword" label="Confirmar Contraseña" :disabled="loading" />

    <div v-if="error" class="error-message">{{ error }}</div>

    <button type="submit" class="btn-primary" :disabled="loading">
      <span>{{ loading ? 'Creando cuenta...' : 'Registrarse' }}</span>
    </button>
  </form>
</template>

<style scoped>
/* Reutilizamos tus estilos previos */
.register-form { display: flex; flex-direction: column; gap: 18px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.custom-label { font-weight: 700; color: #00897b; font-size: 13px; margin-left: 4px; }

.input-field {
  padding: 14px 16px;
  background-color: #f8fbfb;
  border: 2px solid #e0f2f1;
  border-radius: 12px;
  font-size: 14px;
  width: 100%;
  box-sizing: border-box;
  font-family: inherit;
}

/* Estilo específico para que el input date se vea igual al resto */
.custom-date {
  color: #2c3e50;
  cursor: text;
}

/* Ajuste para que el icono del calendario combine con tu estética (en navegadores Chrome) */
::-webkit-calendar-picker-indicator {
  cursor: pointer;
  filter: invert(48%) sepia(13%) saturate(3207%) hue-rotate(130deg) brightness(95%) contrast(80%);
  /* Esto lo pone en un tono turquesa similar a tu --accent */
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
  box-shadow: 0 4px 15px rgba(17, 166, 145, 0.25);
  margin-top: 8px;
}
</style>