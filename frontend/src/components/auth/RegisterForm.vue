<script setup lang="ts">
import { ref } from 'vue'
import PasswordInput from './PasswordInput.vue'

defineProps<{ loading?: boolean }>()
const emit = defineEmits(['submit'])

const formData = ref({
  email: '',
  password: '',
  confirmPassword: '',
  first_name: '',
  last_name: '',
  phone: '',
  birth_date: '',
  gender: 'masculino',
  doc_type_name: 'DNI',
  doc_number: ''
})

const error = ref('')

const handleSubmit = () => {
  if (formData.value.password !== formData.value.confirmPassword) {
    error.value = 'Las contraseñas no coinciden'
    return
  }
  error.value = ''
  const { confirmPassword, ...dataToSubmit } = formData.value
  emit('submit', dataToSubmit)
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="register-form">
    <div class="form-row">
      <div class="form-group">
        <label class="custom-label">Nombre</label>
        <input v-model="formData.first_name" type="text" class="input-field" required />
      </div>
      <div class="form-group">
        <label class="custom-label">Apellido</label>
        <input v-model="formData.last_name" type="text" class="input-field" required />
      </div>
    </div>

    <div class="form-group">
      <label class="custom-label">Email</label>
      <input v-model="formData.email" type="email" class="input-field" placeholder="tu@email.com" required />
    </div>

    <div class="form-row">
      <div class="form-group">
        <label class="custom-label">Tipo de Documento</label>
        <select v-model="formData.doc_type_name" class="input-field select-field">
          <option value="DNI">DNI</option>
          <option value="PASAPORTE">Pasaporte</option>
        </select>
      </div>
      <div class="form-group">
        <label class="custom-label">Numero</label>
        <input v-model="formData.doc_number" type="text" class="input-field" required />
      </div>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label class="custom-label">Nacimiento</label>
        <input v-model="formData.birth_date" type="date" class="input-field" required />
      </div>
      <div class="form-group">
        <label class="custom-label">Genero</label>
        <select v-model="formData.gender" class="input-field select-field">
          <option value="masculino">Masculino</option>
          <option value="femenino">Femenino</option>
          <option value="otro">Otro</option>
        </select>
      </div>
    </div>

    <div class="form-group">
      <label class="custom-label">Telefono</label>
      <input v-model="formData.phone" type="text" class="input-field" placeholder="1123456789" required />
    </div>

    <PasswordInput v-model="formData.password" label="Contraseña" :disabled="loading" />
    <PasswordInput v-model="formData.confirmPassword" label="Confirmar Contraseña" :disabled="loading" />

    <div v-if="error" class="error-message">{{ error }}</div>

    <button type="submit" class="btn-primary" :disabled="loading">
      <span>{{ loading ? 'Creando cuenta' : 'Registrarse' }}</span>
    </button>
  </form>
</template>

<style scoped>
.register-form { display: flex; flex-direction: column; gap: 14px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.custom-label { font-weight: 700; color: #00897b; font-size: 13px; margin-left: 4px; }
.input-field {
  padding: 12px 14px;
  background-color: #f8fbfb;
  border: 2px solid #e0f2f1;
  border-radius: 12px;
  font-size: 14px;
}
.select-field { height: 46px; cursor: pointer; }
.error-message {
  background-color: #fff5f5;
  color: #e53935;
  padding: 10px;
  border-radius: 10px;
  font-size: 13px;
  border: 1px solid #ffcdd2;
}
.btn-primary {
  padding: 16px;
  background: #11a691;
  color: white;
  border: none;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(17, 166, 145, 0.25);
  margin-top: 6px;
}
</style>