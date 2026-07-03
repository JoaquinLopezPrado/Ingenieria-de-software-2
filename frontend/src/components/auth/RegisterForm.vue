<script setup lang="ts">
import { ref, watch } from 'vue'
import PasswordInput from './PasswordInput.vue'

const props = withDefaults(
  defineProps<{
    loading?: boolean
    apiError?: string
    showPasswordRequirements?: boolean
    showGoogleRegister?: boolean
    submitLabel?: string
  }>(),
  {
    loading: false,
    apiError: '',
    showPasswordRequirements: false,
    showGoogleRegister: true,
    submitLabel: 'Registrarse',
  },
)

const emit = defineEmits(['submit', 'google-register'])

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
  doc_number: '',
})

const fieldErrors = ref<Record<string, string>>({})

const clearError = (field: string) => {
  fieldErrors.value[field] = ''
}

const showReqs = ref(false)

watch(
  () => props.showPasswordRequirements,
  (val) => {
    if (val) showReqs.value = true
  },
)

watch(
  () => formData.value.password,
  () => {
    clearError('password')
    showReqs.value = false
  },
)

watch(
  () => formData.value.confirmPassword,
  () => clearError('confirmPassword'),
)

const handleSubmit = () => {
  const e: Record<string, string> = {}

  if (!formData.value.first_name.trim()) {
    e.first_name = 'El nombre es obligatorio.'
  }

  if (!formData.value.last_name.trim()) {
    e.last_name = 'El apellido es obligatorio.'
  }

  if (!formData.value.email.trim()) {
    e.email = 'El email es obligatorio.'
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.value.email)) {
    e.email = 'El email no tiene un formato válido.'
  }

  if (!formData.value.doc_number.trim()) {
    e.doc_number = 'El número de documento es obligatorio.'
  }

  if (!formData.value.birth_date) {
    e.birth_date = 'La fecha de nacimiento es obligatoria.'
  }

  if (!formData.value.phone.trim()) {
    e.phone = 'El teléfono es obligatorio.'
  } else if (!/^\d+$/.test(formData.value.phone.trim())) {
    e.phone = 'El teléfono debe contener solo números.'
  }

  if (!formData.value.password) {
    e.password = 'La contraseña es obligatoria.'
  }

  if (!formData.value.confirmPassword) {
    e.confirmPassword = 'Confirmá tu contraseña.'
  } else if (formData.value.password !== formData.value.confirmPassword) {
    e.confirmPassword = 'Las contraseñas no coinciden.'
  }

  fieldErrors.value = e

  if (Object.values(e).some((v) => v)) return

  const { confirmPassword, ...dataToSubmit } = formData.value
  emit('submit', dataToSubmit)
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="register-form" novalidate>
    <div class="form-row">
      <div class="form-group">
        <label
          class="custom-label"
          :class="{ 'label-error': fieldErrors.first_name }"
        >
          Nombre
        </label>

        <input
          v-model="formData.first_name"
          type="text"
          class="input-field"
          :class="{ 'input-error': fieldErrors.first_name }"
          @input="clearError('first_name')"
        />

        <span v-if="fieldErrors.first_name" class="field-error">
          {{ fieldErrors.first_name }}
        </span>
      </div>

      <div class="form-group">
        <label
          class="custom-label"
          :class="{ 'label-error': fieldErrors.last_name }"
        >
          Apellido
        </label>

        <input
          v-model="formData.last_name"
          type="text"
          class="input-field"
          :class="{ 'input-error': fieldErrors.last_name }"
          @input="clearError('last_name')"
        />

        <span v-if="fieldErrors.last_name" class="field-error">
          {{ fieldErrors.last_name }}
        </span>
      </div>
    </div>

    <div class="form-group">
      <label
        class="custom-label"
        :class="{ 'label-error': fieldErrors.email }"
      >
        Email
      </label>

      <input
        v-model="formData.email"
        type="email"
        class="input-field"
        :class="{ 'input-error': fieldErrors.email }"
        placeholder="tu@email.com"
        @input="clearError('email')"
      />

      <span v-if="fieldErrors.email" class="field-error">
        {{ fieldErrors.email }}
      </span>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label class="custom-label">
          Tipo de Documento
        </label>

        <select
          v-model="formData.doc_type_name"
          class="input-field select-field"
        >
          <option value="DNI">DNI</option>
          <option value="PASAPORTE">Pasaporte</option>
        </select>
      </div>

      <div class="form-group">
        <label
          class="custom-label"
          :class="{ 'label-error': fieldErrors.doc_number }"
        >
          Número
        </label>

        <input
          v-model="formData.doc_number"
          type="text"
          class="input-field"
          :class="{ 'input-error': fieldErrors.doc_number }"
          @input="clearError('doc_number')"
        />

        <span v-if="fieldErrors.doc_number" class="field-error">
          {{ fieldErrors.doc_number }}
        </span>
      </div>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label
          class="custom-label"
          :class="{ 'label-error': fieldErrors.birth_date }"
        >
          Nacimiento
        </label>

        <input
          v-model="formData.birth_date"
          type="date"
          class="input-field"
          :class="{ 'input-error': fieldErrors.birth_date }"
          @input="clearError('birth_date')"
        />

        <span v-if="fieldErrors.birth_date" class="field-error">
          {{ fieldErrors.birth_date }}
        </span>
      </div>

      <div class="form-group">
        <label class="custom-label">
          Género
        </label>

        <select
          v-model="formData.gender"
          class="input-field select-field"
        >
          <option value="masculino">Masculino</option>
          <option value="femenino">Femenino</option>
          <option value="otro">Otro</option>
        </select>
      </div>
    </div>

    <div class="form-group">
      <label
        class="custom-label"
        :class="{ 'label-error': fieldErrors.phone }"
      >
        Teléfono
      </label>

      <input
        v-model="formData.phone"
        type="text"
        inputmode="numeric"
        class="input-field"
        :class="{ 'input-error': fieldErrors.phone }"
        placeholder="1123456789"
        @input="clearError('phone')"
      />

      <span v-if="fieldErrors.phone" class="field-error">
        {{ fieldErrors.phone }}
      </span>
    </div>

    <PasswordInput
      v-model="formData.password"
      label="Contraseña"
      :error="fieldErrors.password"
      :disabled="loading"
    />

    <PasswordInput
      v-model="formData.confirmPassword"
      label="Confirmar Contraseña"
      :error="fieldErrors.confirmPassword"
      :disabled="loading"
    />

    <div v-if="apiError" class="error-message">
      {{ apiError }}
    </div>

    <button
      type="submit"
      class="btn-primary"
      :disabled="loading"
    >
      <span>{{ loading ? 'Creando cuenta' : submitLabel }}</span>
    </button>

    <ul v-if="showReqs" class="password-requirements">
      <li>Al menos 8 caracteres</li>
      <li>Al menos una letra mayúscula</li>
      <li>Al menos una letra minúscula</li>
      <li>Al menos un número</li>
      <li>Al menos un carácter especial</li>
    </ul>

    <template v-if="showGoogleRegister">
      <div class="oauth-divider">
        <span>o</span>
      </div>

      <button
        type="button"
        class="btn-google"
        @click="emit('google-register')"
        :disabled="loading"
      >
        <svg
          class="google-icon"
          viewBox="0 0 24 24"
          width="20"
          height="20"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>

        <span>Registrarse con Google</span>
      </button>
    </template>
  </form>
</template>

<style scoped>
.register-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
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
  padding: 12px 14px;
  background-color: #f8fbfb;
  border: 2px solid #e0f2f1;
  border-radius: 12px;
  font-size: 14px;
}

.select-field {
  height: 46px;
  cursor: pointer;
}

.input-field.input-error {
  border-color: #e53935;
  background-color: #fff8f8;
}

.custom-label.label-error {
  color: #e53935;
}

.field-error {
  font-size: 12px;
  color: #e53935;
  margin-left: 4px;
}

.password-requirements {
  margin: 0;
  padding: 10px 14px;
  background: #fff8e1;
  border: 1px solid #ffe082;
  border-radius: 10px;
  list-style: disc;
  list-style-position: inside;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: #795548;
}

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

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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