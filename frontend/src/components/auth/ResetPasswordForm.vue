<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ loading: boolean }>()
const emit = defineEmits<{ (e: 'submit', newPassword: string): void }>()

const newPassword = ref('')
const confirmPassword = ref('')
const passwordError = ref('')
const confirmError = ref('')

const PASSWORD_REGEX_UPPER = /[A-Z]/
const PASSWORD_REGEX_LOWER = /[a-z]/
const PASSWORD_REGEX_DIGIT = /[0-9]/
const PASSWORD_REGEX_SPECIAL = /[^A-Za-z0-9]/

const handleSubmit = () => {
  passwordError.value = ''
  confirmError.value = ''

  if (newPassword.value.length < 8) {
    passwordError.value = 'La contraseña debe tener al menos 8 caracteres.'
    return
  }
  if (!PASSWORD_REGEX_UPPER.test(newPassword.value)) {
    passwordError.value = 'La contraseña debe contener al menos una letra mayúscula.'
    return
  }
  if (!PASSWORD_REGEX_LOWER.test(newPassword.value)) {
    passwordError.value = 'La contraseña debe contener al menos una letra minúscula.'
    return
  }
  if (!PASSWORD_REGEX_DIGIT.test(newPassword.value)) {
    passwordError.value = 'La contraseña debe contener al menos un número.'
    return
  }
  if (!PASSWORD_REGEX_SPECIAL.test(newPassword.value)) {
    passwordError.value = 'La contraseña debe contener al menos un carácter especial.'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    confirmError.value = 'Las contraseñas no coinciden.'
    return
  }

  emit('submit', newPassword.value)
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="form-container">
    <div class="form-group">
      <label class="custom-label">Nueva contraseña</label>
      <input
        v-model="newPassword"
        type="password"
        placeholder="Mínimo 8 caracteres"
        class="input-field"
        :class="{ 'input-error': passwordError }"
        autocomplete="new-password"
      />
      <span v-if="passwordError" class="field-error">{{ passwordError }}</span>
    </div>

    <div class="form-group">
      <label class="custom-label">Confirmar contraseña</label>
      <input
        v-model="confirmPassword"
        type="password"
        placeholder="Repetí la contraseña"
        class="input-field"
        :class="{ 'input-error': confirmError }"
        autocomplete="new-password"
      />
      <span v-if="confirmError" class="field-error">{{ confirmError }}</span>
    </div>

    <div class="actions">
      <button type="submit" class="btn-primary" :disabled="props.loading">
        {{ props.loading ? 'Guardando...' : 'Restablecer contraseña' }}
      </button>
    </div>
  </form>
</template>

<style scoped>
.form-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
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
  width: 100%;
  box-sizing: border-box;
}

.input-field:focus {
  outline: none;
  border-color: #11a691;
  background-color: #fff;
}

.input-error {
  border-color: #e53935 !important;
}

.field-error {
  color: #e53935;
  font-size: 12px;
  margin-left: 4px;
}

.actions {
  margin-top: 10px;
}

.btn-primary {
  width: 100%;
  padding: 16px;
  background: #11a691;
  color: white;
  border: none;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: translateY(-2px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
