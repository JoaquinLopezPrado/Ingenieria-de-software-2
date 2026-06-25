<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { RouterLink } from 'vue-router'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const passwordChanged = computed(() => route.query.password_changed === 'true')

const showLogoutConfirm = ref(false)
const isLoggingOut = ref(false)

const employeeEmail = computed(() => authStore.user?.email ?? authStore.user?.username ?? 'Sin correo')

const openLogoutConfirm = () => { showLogoutConfirm.value = true }

const closeLogoutConfirm = () => {
  if (isLoggingOut.value) return
  showLogoutConfirm.value = false
}

const confirmLogout = async () => {
  isLoggingOut.value = true
  try {
    await authStore.logout()
    router.replace('/')
  } finally {
    showLogoutConfirm.value = false
    isLoggingOut.value = false
  }
}
</script>

<template>
  <div class="employee-wrapper">
    <aside class="sidebar">
      <div class="brand-header">
        <div class="brand-text">
          <h2 class="brand-title">SiempreGym</h2>
          <p class="brand-subtitle">Panel del empleado</p>
        </div>
      </div>

      <nav class="sidebar-nav">
        <RouterLink to="/admin/configuracion" class="nav-link">Seguridad</RouterLink>
      </nav>

      <div class="sidebar-spacer"></div>

      <div class="user-footer">
        <div class="user-meta">
          <p class="user-email">{{ employeeEmail }}</p>
        </div>

        <button type="button" class="btn-logout" @click="openLogoutConfirm">
          <svg class="logout-icon" viewBox="0 0 24 24" width="18" height="18" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 17v-3H9v-4h7V7l5 5-5 5M14 2a2 2 0 0 1 2 2v2h-2V4H5v16h9v-2h2v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9z" fill="currentColor"/>
          </svg>
          <span>Cerrar sesión</span>
        </button>
      </div>
    </aside>

    <main class="main-content">
      <div v-if="passwordChanged" class="banner banner-success">
        Tu contraseña fue actualizada correctamente.
      </div>
      <div class="construction-card">
        <div class="construction-icon">🚧</div>
        <h1 class="construction-title">Portal del empleado</h1>
        <p class="construction-text">Esta sección está en construcción.</p>
        <p class="construction-subtext">Próximamente vas a poder gestionar turnos, asistencias y más desde acá.</p>
      </div>
    </main>

    <div v-if="showLogoutConfirm" class="modal-overlay" @click.self="closeLogoutConfirm">
      <div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="logout-title">
        <h2 id="logout-title" class="modal-title">Confirmar cierre de sesión</h2>
        <p class="modal-text">¿Deseás continuar con la operación?</p>
        <div class="modal-actions">
          <button type="button" class="modal-cancel-btn" @click="closeLogoutConfirm" :disabled="isLoggingOut">No</button>
          <button type="button" class="modal-confirm-btn" @click="confirmLogout" :disabled="isLoggingOut">Sí, cerrar sesión</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.employee-wrapper {
  display: flex;
  min-height: 100vh;
  background-color: #f3f4f6;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
  background-color: #0d3027;
  color: white;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  left: 0;
  top: 0;
}

.brand-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 2rem 1.5rem;
}

.brand-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  white-space: nowrap;
}

.brand-subtitle {
  margin: 0;
  font-size: 0.72rem;
  color: #8fa8a2;
  white-space: nowrap;
}

.sidebar-nav {
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-link {
  display: block;
  padding: 10px 14px;
  border-radius: 10px;
  color: #c8dbd8;
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
  transition: background 0.2s, color 0.2s;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.sidebar-spacer {
  flex-grow: 1;
}

.user-footer {
  padding: 1.25rem 1.5rem;
  background-color: #0a251e;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.user-email {
  margin: 0;
  font-size: 0.78rem;
  color: #d1dadd;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-logout {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  background-color: #fff5f5;
  color: #e53935;
  border: 2px solid #ffcdd2;
  border-radius: 30px;
  padding: 12px 16px;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(229, 57, 53, 0.08);
  transition: all 0.2s ease;
  cursor: pointer;
}

.btn-logout:hover {
  background-color: #e53935;
  color: #ffffff;
  border-color: #e53935;
  box-shadow: 0 6px 15px rgba(229, 57, 53, 0.2);
}

.logout-icon {
  flex-shrink: 0;
}

.main-content {
  flex-grow: 1;
  margin-left: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
  box-sizing: border-box;
  gap: 1.25rem;
}

.banner {
  width: min(100%, 480px);
  border-radius: 12px;
  padding: 14px 18px;
  font-size: 14px;
  font-weight: 500;
}

.banner-success {
  background-color: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

.construction-card {
  background: white;
  border-radius: 24px;
  padding: 56px 48px;
  text-align: center;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.07);
  max-width: 480px;
  width: 100%;
}

.construction-icon {
  font-size: 3.5rem;
  margin-bottom: 1.25rem;
}

.construction-title {
  margin: 0 0 12px;
  font-size: 1.6rem;
  font-weight: 700;
  color: #0d3027;
}

.construction-text {
  margin: 0 0 8px;
  font-size: 1.05rem;
  color: #374151;
  font-weight: 600;
}

.construction-subtext {
  margin: 0;
  font-size: 0.9rem;
  color: #6b7280;
  line-height: 1.5;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 1200;
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

.modal-cancel-btn:disabled,
.modal-confirm-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
</style>
