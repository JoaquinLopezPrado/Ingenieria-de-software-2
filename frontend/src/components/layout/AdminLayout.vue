
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const authStore = useAuthStore()

const showLogoutConfirm = ref(false)
const isLoggingOut = ref(false)

const adminEmail = computed(() => authStore.user?.email ?? authStore.user?.username ?? 'Sin correo')

const openLogoutConfirm = () => {
  showLogoutConfirm.value = true
}

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
  <div class="admin-wrapper">
    <aside class="sidebar">
      <div class="brand-header">
        <div class="brand-text">
          <h2 class="brand-title">SiempreGym</h2>
          <p class="brand-subtitle">Panel de administración</p>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-group">
          <p class="nav-label">PRINCIPAL</p>
          <RouterLink to="/admin" class="nav-item" active-class="active" exact>
            <span class="nav-icon">⊞</span> Inicio
          </RouterLink>
          <a href="#" class="nav-item">
            <span class="nav-icon">☰</span> Inscripciones
          </a>
          <a href="#" class="nav-item">
            <span class="nav-icon">◎</span> Alumnos
          </a>
          <RouterLink to="/activities" class="nav-item" active-class="active">
            <span class="nav-icon">◈</span> Actividades
          </RouterLink>
        </div>

        <div class="nav-group">
          <p class="nav-label">ADMINISTRACIÓN</p>
          <RouterLink to="/report" class="nav-item" active-class="active">
            <span class="nav-icon">▦</span> Reportes
          </RouterLink>
          <RouterLink to="/activities/turnos" class="nav-item" active-class="active">
            <span class="nav-icon">◷</span> Grilla de Turnos
          </RouterLink>
          <a href="#" class="nav-item">
            <span class="nav-icon">✓</span> Asistencia
          </a>
          <RouterLink to="/admin/configuracion" class="nav-item" active-class="active">
            <span class="nav-icon">⚙</span> Configuración
          </RouterLink>
        </div>
      </nav>

      <div class="user-footer">
        <div class="brand-text user-meta">
          <p class="user-email">{{ adminEmail }}</p>
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
      <slot></slot>
    </main>

    <div v-if="showLogoutConfirm" class="modal-overlay" @click.self="closeLogoutConfirm">
      <div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="logout-title">
        <h2 id="logout-title" class="modal-title">Confirmar cierre de sesión</h2>
        <p class="modal-text">¿Deseás continuar con la operación?</p>

        <div class="modal-actions">
          <button type="button" class="modal-cancel-btn" @click="closeLogoutConfirm" :disabled="isLoggingOut">
            No
          </button>
          <button type="button" class="modal-confirm-btn" @click="confirmLogout" :disabled="isLoggingOut">
            Sí, cerrar sesión
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-wrapper {
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
  overflow-y: auto;
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
  flex-grow: 1;
  padding: 0.5rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  overflow-y: auto;
}

.nav-label {
  font-size: 0.68rem;
  font-weight: 700;
  color: #8fa8a2;
  letter-spacing: 1.2px;
  margin: 0 0 0.6rem 0;
  padding-left: 0.75rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  color: #d1dadd;
  text-decoration: none;
  padding: 0.7rem 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
  margin-bottom: 0.15rem;
  transition: background-color 0.15s, color 0.15s;
}

.nav-item:hover {
  background-color: rgba(17, 153, 142, 0.15);
  color: white;
}

.nav-item.active {
  background-color: #11998e;
  color: white;
  font-weight: 600;
}

.nav-icon {
  font-size: 0.95rem;
  width: 1.2rem;
  text-align: center;
  flex-shrink: 0;
}

.user-footer {
  padding: 1.25rem 1.5rem;
  background-color: #0a251e;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.user-meta {
  min-width: 0;
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
  padding: 2rem 2.5rem;
  min-width: 0;
  min-height: 100vh;
  box-sizing: border-box;
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

@media (max-width: 768px) {
  .sidebar {
    width: 220px;
  }

  .main-content {
    margin-left: 220px;
    padding: 1.5rem;
  }
}
</style>

