<template>
  <div class="logout-page" :class="{ leaving: isLeaving }">
    <div class="logout-card">
      <h1 class="brand">SIEMPREGYM</h1>
      <p class="subtitle">¿Querés cerrar tu sesión?</p>

      <div class="actions">
        <button class="primary-btn" @click="openConfirmModal" :disabled="loading">
          {{ loading ? 'Cerrando sesión...' : 'Cerrar sesión' }}
        </button>

        <button class="secondary-btn" @click="handleCancel" :disabled="loading">
          Cancelar
        </button>
      </div>

      <p v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </p>
    </div>

    <div v-if="showConfirmModal" class="modal-overlay">
      <div class="modal-box">
        <h2 class="modal-title">Confirmar cierre de sesión</h2>
        <p class="modal-text">¿Deseás continuar con la operación?</p>

        <div class="modal-actions">
          <button class="modal-cancel-btn" @click="closeConfirmModal" :disabled="loading">
            No
          </button>

          <button class="modal-confirm-btn" @click="confirmLogout" :disabled="loading">
            Sí, cerrar sesión
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const authStore = useAuthStore()

const isLeaving = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const showConfirmModal = ref(false)

function openConfirmModal() {
  showConfirmModal.value = true
}

function closeConfirmModal() {
  showConfirmModal.value = false
}

async function confirmLogout() {
  errorMessage.value = ''
  loading.value = true
  isLeaving.value = true
  showConfirmModal.value = false

  setTimeout(async () => {
    try {
      await authStore.logout()
      router.push('/')
    } catch (error) {
      console.error('ERROR en confirmLogout:', error)
      errorMessage.value = 'No se pudo cerrar sesión. Intentá nuevamente.'
      isLeaving.value = false
    } finally {
      loading.value = false
    }
  }, 180)
}

function handleCancel() {
  isLeaving.value = true

  setTimeout(() => {
    router.push('/')
  }, 180)
}
</script>

<style scoped>
.logout-page {
  min-height: 100vh;
  background: #d9eeea;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  padding-top: 84px;
  transition: opacity 0.18s ease, transform 0.18s ease;
  opacity: 1;
}

.logout-page.leaving {
  opacity: 0;
  transform: scale(0.995);
}

.logout-card {
  width: 100%;
  max-width: 420px;
  background: #ffffff;
  border-radius: 28px;
  padding: 40px 32px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.brand {
  margin: 0 0 12px;
  font-size: 2rem;
  font-weight: 800;
  color: #0d9b8a;
  letter-spacing: 1px;
}

.subtitle {
  margin: 0 0 32px;
  font-size: 1rem;
  color: #6b7280;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.primary-btn {
  border: none;
  border-radius: 999px;
  padding: 14px 20px;
  background: #18b4a3;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 8px 18px rgba(24, 180, 163, 0.25);
}

.primary-btn:hover {
  background: #109889;
}

.primary-btn:disabled,
.secondary-btn:disabled,
.modal-cancel-btn:disabled,
.modal-confirm-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.secondary-btn {
  border: 1px solid #cfd8dc;
  border-radius: 999px;
  padding: 14px 20px;
  background: white;
  color: #4b5563;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.secondary-btn:hover {
  background: #f8fafc;
}

.error-message {
  margin-top: 16px;
  color: #dc2626;
  font-size: 0.95rem;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 999;
}

.modal-box {
  width: 100%;
  max-width: 380px;
  background: white;
  border-radius: 24px;
  padding: 28px 24px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
  text-align: center;
}

.modal-title {
  margin: 0 0 10px;
  color: #0d9b8a;
  font-size: 1.3rem;
  font-weight: 700;
}

.modal-text {
  margin: 0 0 22px;
  color: #6b7280;
  font-size: 0.98rem;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.modal-cancel-btn,
.modal-confirm-btn {
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
}

.modal-cancel-btn {
  background: #f3f4f6;
  color: #374151;
}

.modal-confirm-btn {
  background: #18b4a3;
  color: white;
}

.modal-confirm-btn:hover {
  background: #109889;
}
</style>