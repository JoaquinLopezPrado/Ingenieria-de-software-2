<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ loading: boolean }>()
const emit = defineEmits<{ (e: 'submit', email: string): void }>()

const email = ref('')
const emailError = ref('')

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const handleSubmit = () => {
  emailError.value = ''
  if (!EMAIL_REGEX.test(email.value)) {
    emailError.value = 'El formato del correo electrónico no es válido.'
    return
  }
  emit('submit', email.value)
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="form-container">
    <div class="form-group">
      <label class="custom-label">Tu Email</label>
      <input
        v-model="email"
        type="text"
        placeholder="email@ejemplo.com"
        class="input-field"
        :class="{ 'input-error': emailError }"
        autocomplete="email"
      />
      <span v-if="emailError" class="field-error">{{ emailError }}</span>
    </div>

    <div class="actions">
      <button type="submit" class="btn-primary" :disabled="props.loading">
        {{ props.loading ? 'Enviando...' : 'Enviar enlace' }}
      </button>
      <router-link to="/login" class="link-back">Cancelar</router-link>
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
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 10px;
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

.link-back {
  text-align: center;
  color: #7f8c8d;
  font-size: 14px;
  text-decoration: none;
}
</style>
