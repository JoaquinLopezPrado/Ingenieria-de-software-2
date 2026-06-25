<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import SideMenu from '@/components/SideMenu.vue'
import { authService } from '@/services/authService'

const router = useRouter()

const hasLocalPassword = ref(false)
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordError = ref('')
const passwordSuccess = ref(false)
const passwordLoading = ref(false)

onMounted(async () => {
  const { data } = await authService.getMe()
  hasLocalPassword.value = data.has_local_password
})

const handleChangePassword = async () => {
  passwordError.value = ''
  passwordSuccess.value = false
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = 'Las contraseñas nuevas no coinciden.'
    return
  }
  passwordLoading.value = true
  try {
    await authService.changePassword(currentPassword.value, newPassword.value)
    passwordSuccess.value = true
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    const errors = err?.response?.data?.errors
    if (errors?.new_password) {
      passwordError.value = errors.new_password
    } else {
      passwordError.value = detail || 'Ocurrió un error al cambiar la contraseña.'
    }
  } finally {
    passwordLoading.value = false
  }
}
</script>

<template>
  <SideMenu />
  <div class="page-wrapper">
    <div class="security-card">
      <p class="eyebrow">Mi cuenta</p>
      <h1>Cambiar contraseña</h1>
      <p class="intro">Actualizá tu contraseña de acceso.</p>

      <div v-if="!hasLocalPassword" class="no-password-notice">
        Tu cuenta inició sesión con Google y no tiene contraseña local. No podés cambiar la contraseña desde aquí.
      </div>

      <form v-else class="password-form" @submit.prevent="handleChangePassword">
        <div class="field-group">
          <label class="field-label">Contraseña actual</label>
          <input
            v-model="currentPassword"
            type="password"
            class="field-input"
            placeholder="••••••••"
            autocomplete="current-password"
            required
          />
        </div>
        <div class="field-group">
          <label class="field-label">Nueva contraseña</label>
          <input
            v-model="newPassword"
            type="password"
            class="field-input"
            placeholder="••••••••"
            autocomplete="new-password"
            required
          />
        </div>
        <div class="field-group">
          <label class="field-label">Confirmar nueva contraseña</label>
          <input
            v-model="confirmPassword"
            type="password"
            class="field-input"
            placeholder="••••••••"
            autocomplete="new-password"
            required
          />
        </div>
        <p v-if="passwordError" class="form-error">{{ passwordError }}</p>
        <p v-if="passwordSuccess" class="form-success">Contraseña actualizada correctamente.</p>
        <button
          type="submit"
          class="btn-primary"
          :disabled="passwordLoading"
        >
          {{ passwordLoading ? 'Guardando...' : 'Cambiar contraseña' }}
        </button>
      </form>

      <button class="btn-back" @click="router.back()">Volver</button>
    </div>
  </div>
</template>

<style scoped>
.page-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 5rem 1.5rem 2rem;
  box-sizing: border-box;
}

.security-card {
  width: min(100%, 480px);
  padding: 2.25rem;
  border-radius: 28px;
  background: linear-gradient(135deg, #ffffff 0%, #f1f7f6 100%);
  box-shadow: 0 18px 40px rgba(13, 48, 39, 0.12);
  border: 1px solid rgba(17, 153, 142, 0.12);
}

.eyebrow {
  margin: 0 0 0.75rem;
  color: #0d9b8a;
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  color: #0f172a;
  font-size: clamp(1.6rem, 4vw, 2.2rem);
  line-height: 1.1;
}

.intro {
  margin: 1rem 0 0;
  color: #4b5563;
  font-size: 1rem;
  line-height: 1.6;
}

.no-password-notice {
  margin-top: 1.25rem;
  padding: 0.9rem 1rem;
  border-radius: 12px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  color: #92400e;
  font-size: 0.9rem;
  line-height: 1.5;
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1.25rem;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.field-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: #334155;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.field-input {
  width: 100%;
  padding: 11px 14px;
  font-size: 0.95rem;
  border: 1.5px solid #d1d5db;
  border-radius: 12px;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s;
  background: #fff;
}

.field-input:focus { border-color: #00897b; }

.form-error {
  margin: 0;
  font-size: 0.85rem;
  color: #dc2626;
}

.form-success {
  margin: 0;
  font-size: 0.85rem;
  color: #059669;
  font-weight: 600;
}

.btn-primary {
  width: 100%;
  padding: 13px;
  margin-top: 0.25rem;
  border-radius: 10px;
  border: none;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  background: #00897b;
  color: #fff;
  transition: background 0.2s, opacity 0.2s;
}

.btn-primary:hover:not(:disabled) { background: #00695c; }
.btn-primary:disabled { opacity: 0.55; cursor: not-allowed; }

.btn-back {
  width: 100%;
  margin-top: 0.75rem;
  padding: 11px;
  border-radius: 10px;
  border: none;
  font-size: 0.92rem;
  font-weight: 600;
  cursor: pointer;
  background: #f1f5f9;
  color: #334155;
  transition: background 0.2s;
}

.btn-back:hover { background: #e2e8f0; }
</style>
