<script setup lang="ts">
import { ref, watch } from 'vue'

type CreateActivityPayload = {
  name: string
  description: string
}

const props = defineProps<{
  visible: boolean
  loading?: boolean
}>()

const emit = defineEmits<{
  close: []
  submit: [payload: CreateActivityPayload]
}>()

const form = ref<CreateActivityPayload>({
  name: '',
  description: '',
})

const error = ref('')

const resetForm = () => {
  form.value = { name: '', description: '' }
  error.value = ''
}

watch(
  () => props.visible,
  (isVisible) => {
    if (isVisible) resetForm()
  }
)

const handleSubmit = () => {
  const name = form.value.name.trim()
  const description = form.value.description.trim()

  if (!name || !description) {
    error.value = 'Completa nombre y descripción'
    return
  }

  if (name.length > 100) {
    error.value = 'El nombre no puede superar 100 caracteres'
    return
  }

  if (description.length > 500) {
    error.value = 'La descripción no puede superar 500 caracteres'
    return
  }

  error.value = ''
  emit('submit', { name, description })
}

const closeModal = () => {
  emit('close')
}
</script>

<template>
  <div v-if="visible" class="modal-backdrop" @click.self="closeModal">
    <div class="modal-card" role="dialog" aria-modal="true" aria-label="Crear actividad">
      <div class="modal-header">
        <h2>Nueva actividad</h2>
        <button type="button" class="icon-close" @click="closeModal" :disabled="loading">×</button>
      </div>

      <form @submit.prevent="handleSubmit" class="modal-form">
        <div class="form-group">
          <label class="custom-label" for="activity-name">Nombre</label>
          <input
            id="activity-name"
            v-model="form.name"
            type="text"
            class="input-field"
            placeholder="Ej: Funcional"
            :disabled="loading"
          />
        </div>

        <div class="form-group">
          <label class="custom-label" for="activity-description">Descripción</label>
          <textarea
            id="activity-description"
            v-model="form.description"
            class="input-field input-textarea"
            placeholder="Ej: Actividad funcional enfocada en fuerza y cardio"
            :disabled="loading"
            rows="4"
          ></textarea>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div class="actions">
          <button type="button" class="btn-secondary" @click="closeModal" :disabled="loading">
            Cancelar
          </button>
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? 'Creando...' : 'Crear actividad' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(23, 35, 34, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
  padding: 16px;
}

.modal-card {
  width: 100%;
  max-width: 480px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 18px 42px rgba(13, 110, 95, 0.2);
  padding: 24px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.modal-header h2 {
  margin: 0;
  color: #12695f;
  font-size: 22px;
  font-weight: 800;
}

.icon-close {
  border: none;
  background: transparent;
  font-size: 26px;
  line-height: 1;
  cursor: pointer;
  color: #4f6663;
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
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
  transition: all 0.2s ease;
}

.input-textarea {
  resize: vertical;
  min-height: 100px;
  font-family: inherit;
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
  padding: 10px;
  border-radius: 10px;
  font-size: 13px;
  border: 1px solid #ffcdd2;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}

.btn-secondary {
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid #cde8e3;
  background: #ffffff;
  color: #2f4d49;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary {
  padding: 12px 16px;
  background: #11a691;
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(17, 166, 145, 0.25);
}

.btn-primary:disabled,
.btn-secondary:disabled,
.icon-close:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
</style>