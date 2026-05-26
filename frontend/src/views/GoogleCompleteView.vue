<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import AuthHeader from '@/components/auth/AuthHeader.vue'
import { isAdminUser } from '@/utils/role'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const pendingToken = ref('')
const loading = ref(false)
const error = ref('')

const formData = ref({
  phone: '',
  birth_date: '',
  gender: 'masculino',
  doc_type_name: 'DNI',
  doc_number: '',
})

const prefilledEmail = ref('')
const prefilledName = ref('')

onMounted(() => {
  pendingToken.value = route.query.pending_token as string
  prefilledEmail.value = route.query.email as string ?? ''
  const firstName = route.query.first_name as string ?? ''
  const lastName = route.query.last_name as string ?? ''
  prefilledName.value = [firstName, lastName].filter(Boolean).join(' ')

  if (!pendingToken.value) {
    router.replace('/register')
  }
})

const extractApiError = (err: any): string => {
  const detail = err.response?.data?.detail
  if (!detail) return 'Error al completar el registro.'
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0]
    const msg: unknown = first?.ctx?.error ?? first?.msg
    if (typeof msg === 'string') return msg.replace(/^Value error,\s*/i, '')
  }
  return 'Error al completar el registro.'
}

const handleSubmit = async () => {
  error.value = ''
  loading.value = true
  try {
    await authStore.googleComplete(pendingToken.value, formData.value)
    router.replace(isAdminUser(authStore.user) ? '/admin' : '/list')
  } catch (err: any) {
    if (err.response?.status === 401) {
      router.replace('/register?error=google_token_expired')
      return
    }
    error.value = extractApiError(err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page-wrapper">
    <div class="auth-card">
      <AuthHeader subtitle="Completá tu registro" />

      <div class="google-info">
        <svg viewBox="0 0 24 24" width="20" height="20" xmlns="http://www.w3.org/2000/svg">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>
        <div class="google-info-text">
          <span class="google-name">{{ prefilledName }}</span>
          <span class="google-email">{{ prefilledEmail }}</span>
        </div>
      </div>

      <p class="helper-text">Solo necesitamos algunos datos más para completar tu cuenta.</p>

      <form @submit.prevent="handleSubmit" class="complete-form">
        <div class="form-row">
          <div class="form-group">
            <label class="custom-label">Tipo de Documento</label>
            <select v-model="formData.doc_type_name" class="input-field select-field" :disabled="loading">
              <option value="DNI">DNI</option>
              <option value="PASAPORTE">Pasaporte</option>
            </select>
          </div>
          <div class="form-group">
            <label class="custom-label">Número</label>
            <input v-model="formData.doc_number" type="text" class="input-field" required :disabled="loading" />
          </div>
        </div>

        <div class="form-group">
          <label class="custom-label">Teléfono</label>
          <input v-model="formData.phone" type="text" class="input-field" placeholder="1123456789" required :disabled="loading" />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="custom-label">Fecha de Nacimiento</label>
            <input v-model="formData.birth_date" type="date" class="input-field" required :disabled="loading" />
          </div>
          <div class="form-group">
            <label class="custom-label">Género</label>
            <select v-model="formData.gender" class="input-field select-field" :disabled="loading">
              <option value="masculino">Masculino</option>
              <option value="femenino">Femenino</option>
              <option value="otro">Otro</option>
            </select>
          </div>
        </div>

        <div v-if="error" class="error-message">{{ error }}</div>

        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? 'Creando cuenta...' : 'Completar registro' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.auth-page-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #dff8f2 0%, #cfeee6 50%, #e6f8f0 100%);
  padding: 16px;
}

.auth-card {
  background: white;
  padding: 24px;
  border-radius: 24px;
  box-shadow: 0 15px 35px rgba(13, 110, 95, 0.1);
  width: 100%;
}

.google-info {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8fbfb;
  border: 2px solid #e0f2f1;
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 12px;
}

.google-info-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.google-name {
  font-weight: 700;
  color: #2c3e50;
  font-size: 14px;
}

.google-email {
  color: #7f8c8d;
  font-size: 13px;
}

.helper-text {
  color: #7f8c8d;
  font-size: 13px;
  margin: 0 0 20px 4px;
}

.complete-form {
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
  transition: transform 0.2s, box-shadow 0.2s;
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

@media (min-width: 768px) {
  .auth-card {
    padding: 40px;
    max-width: 480px;
  }
}
</style>
