<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { authService } from '@/services/authService'

const twoFactorEnabled = ref(false)
const hasLocalPassword = ref(false)

// Setup flow
const showSetupModal = ref(false)
const setupQr = ref('')
const setupSecret = ref('')
const setupCode = ref('')
const setupError = ref('')
const setupLoading = ref(false)

// Disable flow
const showDisableModal = ref(false)
const disableCode = ref('')
const disableError = ref('')
const disableLoading = ref(false)

// Change password flow
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordError = ref('')
const passwordSuccess = ref(false)
const passwordLoading = ref(false)

onMounted(async () => {
  const { data } = await authService.getMe()
  twoFactorEnabled.value = data.is_2fa_enabled
  hasLocalPassword.value = data.has_local_password
})

const handleToggle = async () => {
  if (!twoFactorEnabled.value) {
    // Quiere habilitar → abrir flujo de setup
    twoFactorEnabled.value = true
    try {
      const { data } = await authService.setup2FA()
      setupQr.value = data.qr
      setupSecret.value = data.secret
      setupCode.value = ''
      setupError.value = ''
      showSetupModal.value = true
    } catch {
      twoFactorEnabled.value = false
    }
  } else {
    // Quiere deshabilitar → pedir código primero
    twoFactorEnabled.value = false
    disableCode.value = ''
    disableError.value = ''
    showDisableModal.value = true
  }
}

const confirmSetup = async () => {
  setupLoading.value = true
  setupError.value = ''
  try {
    await authService.confirm2FA(setupSecret.value, setupCode.value)
    showSetupModal.value = false
    twoFactorEnabled.value = true
  } catch (err: any) {
    setupError.value = err?.response?.data?.detail || 'Código inválido. Intentá de nuevo.'
    setupCode.value = ''
  } finally {
    setupLoading.value = false
  }
}

const cancelSetup = () => {
  showSetupModal.value = false
  twoFactorEnabled.value = false
}

const confirmDisable = async () => {
  disableLoading.value = true
  disableError.value = ''
  try {
    await authService.disable2FA(disableCode.value)
    showDisableModal.value = false
    twoFactorEnabled.value = false
  } catch (err: any) {
    disableError.value = err?.response?.data?.detail || 'Código inválido. Intentá de nuevo.'
    disableCode.value = ''
  } finally {
    disableLoading.value = false
  }
}

const cancelDisable = () => {
  showDisableModal.value = false
  twoFactorEnabled.value = true
}

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
  <AdminLayout>
    <section class="admin-security">
      <div class="security-card">
        <p class="eyebrow">Contraseña</p>
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
            class="btn-primary btn-full"
            :disabled="passwordLoading"
          >
            {{ passwordLoading ? 'Guardando...' : 'Cambiar contraseña' }}
          </button>
        </form>
      </div>

      <div class="security-card">
        <p class="eyebrow">Seguridad</p>
        <h1>Configuracion de 2FA</h1>
        <p class="intro">
          Habilita o deshabilita el segundo factor para el panel de administracion.
        </p>

        <div class="toggle-panel">
          <div class="toggle-copy">
            <span class="toggle-title">Estado del 2FA</span>
            <span class="toggle-description">
              {{ twoFactorEnabled
                ? 'El acceso de administrador pedirá un segundo factor cuando inicie sesión.'
                : 'El acceso de administrador funcionará solo con email y contraseña.' }}
            </span>
          </div>

          <label class="toggle-row">
            <input
              type="checkbox"
              class="toggle-input"
              :checked="twoFactorEnabled"
              aria-label="Habilitar o deshabilitar 2FA"
              @change="handleToggle"
            />
            <span class="toggle-track" :class="twoFactorEnabled ? 'is-on' : 'is-off'">
              <span class="toggle-thumb"></span>
            </span>
            <span class="toggle-state" :class="twoFactorEnabled ? 'active' : 'inactive'">
              {{ twoFactorEnabled ? 'Habilitado' : 'Deshabilitado' }}
            </span>
          </label>
        </div>
      </div>
    </section>

    <!-- Modal: activar 2FA -->
    <div v-if="showSetupModal" class="modal-backdrop">
      <div class="modal">
        <h2>Activar autenticación en dos pasos</h2>
        <p class="modal-intro">Escaneá este código QR con tu app de autenticación (MS Authenticator, Google Authenticator, etc.).</p>

        <img :src="setupQr" alt="QR code 2FA" class="qr-img" />

        <p class="manual-key-label">O ingresá la clave manual:</p>
        <code class="manual-key">{{ setupSecret }}</code>

        <p class="modal-intro" style="margin-top: 20px;">Luego ingresá el código de 6 dígitos para confirmar:</p>
        <input
          v-model="setupCode"
          type="text"
          inputmode="numeric"
          maxlength="6"
          placeholder="000000"
          class="totp-input"
          autofocus
        />
        <p v-if="setupError" class="modal-error">{{ setupError }}</p>

        <div class="modal-actions">
          <button class="btn-secondary" @click="cancelSetup">Cancelar</button>
          <button
            class="btn-primary"
            :disabled="setupLoading || setupCode.length !== 6"
            @click="confirmSetup"
          >
            {{ setupLoading ? 'Verificando...' : 'Activar 2FA' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: desactivar 2FA -->
    <div v-if="showDisableModal" class="modal-backdrop">
      <div class="modal">
        <h2>Desactivar autenticación en dos pasos</h2>
        <p class="modal-intro">Ingresá el código de tu app de autenticación para confirmar.</p>

        <input
          v-model="disableCode"
          type="text"
          inputmode="numeric"
          maxlength="6"
          placeholder="000000"
          class="totp-input"
          autofocus
        />
        <p v-if="disableError" class="modal-error">{{ disableError }}</p>

        <div class="modal-actions">
          <button class="btn-secondary" @click="cancelDisable">Cancelar</button>
          <button
            class="btn-danger"
            :disabled="disableLoading || disableCode.length !== 6"
            @click="confirmDisable"
          >
            {{ disableLoading ? 'Verificando...' : 'Desactivar 2FA' }}
          </button>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<style scoped>
.admin-security {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 2rem;
  box-sizing: border-box;
}

.security-card {
  width: min(100%, 540px);
  padding: 2.25rem;
  border-radius: 28px;
  background: linear-gradient(135deg, #ffffff 0%, #f1f7f6 100%);
  box-shadow: 0 18px 40px rgba(13, 48, 39, 0.12);
  border: 1px solid rgba(17, 153, 142, 0.12);
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

.btn-full {
  width: 100%;
  padding: 13px;
  margin-top: 0.25rem;
  font-size: 0.95rem;
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
  font-size: clamp(1.8rem, 4vw, 2.5rem);
  line-height: 1.1;
}

.intro {
  margin: 1rem 0 0;
  color: #4b5563;
  font-size: 1rem;
  line-height: 1.6;
}

.toggle-panel {
  margin-top: 1.75rem;
  padding: 1.25rem 1.25rem 1.1rem;
  border-radius: 18px;
  border: 1px solid rgba(17, 153, 142, 0.14);
  background: rgba(255, 255, 255, 0.72);
}

.toggle-copy {
  display: grid;
  gap: 0.35rem;
  margin-bottom: 1rem;
}

.toggle-title {
  font-size: 0.82rem;
  font-weight: 700;
  color: #334155;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.toggle-description {
  color: #64748b;
  font-size: 0.92rem;
  line-height: 1.5;
}

.toggle-row {
  display: inline-flex;
  align-items: center;
  gap: 0.85rem;
  cursor: pointer;
  user-select: none;
}

.toggle-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.toggle-track {
  width: 48px;
  height: 26px;
  border-radius: 999px;
  background-color: #d1d5db;
  padding: 3px;
  box-sizing: border-box;
  transition: background-color 0.2s ease;
}

.toggle-track.is-on { background-color: #11998e; }
.toggle-track.is-off { background-color: #cbd5e1; }

.toggle-thumb {
  display: block;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transform: translateX(0);
  transition: transform 0.2s ease;
}

.toggle-track.is-on .toggle-thumb { transform: translateX(22px); }

.toggle-state { font-size: 0.95rem; font-weight: 700; }
.toggle-state.active { color: #0c8a70; }
.toggle-state.inactive { color: #64748b; }

/* MODAL */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 1rem;
}

.modal {
  background: #fff;
  border-radius: 24px;
  padding: 2rem;
  width: min(100%, 440px);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  gap: 0;
}

.modal h2 {
  margin: 0 0 0.75rem;
  font-size: 1.25rem;
  color: #0f172a;
}

.modal-intro {
  margin: 0 0 1rem;
  font-size: 0.92rem;
  color: #4b5563;
  line-height: 1.5;
}

.qr-img {
  width: 200px;
  height: 200px;
  align-self: center;
  border-radius: 12px;
  margin-bottom: 1rem;
}

.manual-key-label {
  margin: 0 0 0.4rem;
  font-size: 0.82rem;
  color: #64748b;
}

.manual-key {
  display: block;
  background: #f1f5f9;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  letter-spacing: 0.08em;
  word-break: break-all;
  margin-bottom: 0.5rem;
}

.totp-input {
  width: 100%;
  padding: 12px;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.3em;
  text-align: center;
  border: 1.5px solid #d1d5db;
  border-radius: 12px;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s;
  margin-top: 0.5rem;
}

.totp-input:focus { border-color: #00897b; }

.modal-error {
  margin: 0.5rem 0 0;
  font-size: 13px;
  color: #dc2626;
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 1.25rem;
}

.btn-primary, .btn-secondary, .btn-danger {
  flex: 1;
  padding: 12px;
  border-radius: 10px;
  border: none;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
}

.btn-primary { background: #00897b; color: #fff; }
.btn-primary:hover:not(:disabled) { background: #00695c; }

.btn-secondary { background: #f1f5f9; color: #334155; }
.btn-secondary:hover { background: #e2e8f0; }

.btn-danger { background: #dc2626; color: #fff; }
.btn-danger:hover:not(:disabled) { background: #b91c1c; }

.btn-primary:disabled, .btn-danger:disabled { opacity: 0.55; cursor: not-allowed; }

@media (max-width: 640px) {
  .security-card { padding: 1.5rem; border-radius: 22px; }
  .toggle-panel { padding: 1rem; }
  .toggle-row { align-items: flex-start; }
}
</style>
