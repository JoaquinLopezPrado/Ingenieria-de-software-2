
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const authStore = useAuthStore()

async function handleLogout() {
  await authStore.logout()
  router.push({ name: 'login' })
}

const showLogoutConfirm = ref(false)
const isLoggingOut = ref(false)
const collapsed = ref(false)

const adminEmail = computed(() => authStore.user?.email ?? authStore.user?.username ?? 'Sin correo')

const toggleSidebar = () => {
  collapsed.value = !collapsed.value
}

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

          <RouterLink to="/activities" class="nav-item" active-class="active"
            :title="collapsed ? 'Actividades' : ''">
            <span class="nav-icon">🏃</span>
            <span class="nav-text">Actividades</span>
          </RouterLink>

          <RouterLink to="/activities/turnos" class="nav-item" active-class="active"
            :title="collapsed ? 'Grilla de Turnos' : ''">
            <span class="nav-icon">📅</span>
            <span class="nav-text">Grilla de Turnos</span>
          </RouterLink>

          <a href="#" class="nav-item" :title="collapsed ? 'Inscripciones' : ''">
            <span class="nav-icon">📋</span>
            <span class="nav-text">Inscripciones</span>
          </a>
          <RouterLink to="/clientes" class="nav-item" active-class="active">
            <span class="nav-icon">◎</span> Alumnos
          </RouterLink>
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

        <!-- Botón colapsar -->
        <div class="nav-group nav-group--toggle">
          <button class="nav-item nav-toggle-btn" @click="toggleSidebar"
            :title="collapsed ? 'Expandir menú' : 'Colapsar menú'">
            <span class="nav-icon toggle-arrow" :class="{ 'is-collapsed': collapsed }">❮</span>
            <span class="nav-text">Colapsar menú</span>
          </button>
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

/* ── SIDEBAR ── */

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
  overflow-x: hidden;   /* clave para ocultar texto al colapsar */
  overflow-y: auto;
  transition: width 0.25s ease;
  z-index: 100;
}

/* ── Estado colapsado ── */

.admin-wrapper.sidebar-collapsed .sidebar {
  width: 64px;
}

.admin-wrapper.sidebar-collapsed .main-content {
  margin-left: 64px;
}

/* Los elementos con .nav-text desaparecen al colapsar */
.nav-text {
  overflow: hidden;
  white-space: nowrap;
  opacity: 1;
  max-width: 200px;
  transition: opacity 0.15s ease, max-width 0.25s ease;
}

.admin-wrapper.sidebar-collapsed .nav-text {
  opacity: 0;
  max-width: 0;
}

/* Labels de grupo también se ocultan */
.nav-label {
  overflow: hidden;
  white-space: nowrap;
  opacity: 1;
  max-height: 2rem;
  margin-bottom: 0.6rem;
  transition: opacity 0.15s ease, max-height 0.25s ease, margin 0.25s ease;
}

.admin-wrapper.sidebar-collapsed .nav-label {
  opacity: 0;
  max-height: 0;
  margin-bottom: 0;
}

/* ── Brand header ── */

.brand-header {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  padding: 1.75rem 1.25rem 1.5rem;
  transition: justify-content 0.25s;
  min-width: 0;
}

.admin-wrapper.sidebar-collapsed .brand-header {
  justify-content: center;
  padding: 1.75rem 0 1.5rem;
}

.logo-circle {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 50%;
  border: 2px solid #11998e;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.1rem;
  color: #11998e;
}

.logo-circle.small {
  width: 34px;
  height: 34px;
  font-size: 0.8rem;
  flex-shrink: 0;
}

.brand-name {
  min-width: 0;
}

.brand-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
}

.brand-subtitle {
  margin: 0;
  font-size: 0.68rem;
  color: #8fa8a2;
}

/* ── Navegación ── */

.sidebar-nav {
  flex-grow: 1;
  padding: 0 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-group {
  display: flex;
  flex-direction: column;
}

.nav-group--toggle {
  margin-top: auto;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.nav-label {
  font-size: 0.65rem;
  font-weight: 700;
  color: #6a8a80;
  letter-spacing: 1.1px;
  padding-left: 0.6rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  color: #c8d8d4;
  text-decoration: none;
  padding: 0.65rem 0.6rem;
  border-radius: 8px;
  font-size: 0.875rem;
  margin-bottom: 0.1rem;
  white-space: nowrap;
  transition: background-color 0.15s, color 0.15s, padding 0.25s, justify-content 0.1s;
  background: none;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: left;
}

.nav-item:hover {
  background-color: rgba(17, 153, 142, 0.18);
  color: white;
}

.nav-item.active {
  background-color: #11998e;
  color: white;
  font-weight: 600;
}

.admin-wrapper.sidebar-collapsed .nav-item {
  justify-content: center;
  padding: 0.65rem 0;
}

.nav-icon {
  font-size: 1rem;
  width: 1.1rem;
  text-align: center;
  flex-shrink: 0;
}

/* Flecha del toggle rota al colapsar */
.toggle-arrow {
  font-size: 0.85rem;
  font-weight: 700;
  transition: transform 0.25s ease;
}

.toggle-arrow.is-collapsed {
  transform: rotate(180deg);
}

/* ── User footer ── */

.user-footer {
  padding: 1rem 1.25rem;
  background-color: #0a251e;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
  transition: justify-content 0.25s, padding 0.25s;
}

.admin-wrapper.sidebar-collapsed .user-footer {
  justify-content: center;
  padding: 1rem 0;
}

.user-info {
  min-width: 0;
}

.user-name {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 600;
  color: #e2eeeb;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-role {
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
  padding: 1.25rem 2rem;
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
    transition: margin-left 0.25s ease;
  }
}

/* ── Responsive: colapso automático del sidebar ── */

@media (max-width: 960px) {
  /* Fuerza el sidebar a modo ícono sin importar el estado JS */
  .sidebar {
    width: 64px !important;
  }

  .nav-text {
    opacity: 0 !important;
    max-width: 0 !important;
  }

  .nav-label {
    opacity: 0 !important;
    max-height: 0 !important;
    margin-bottom: 0 !important;
  }

  .nav-item {
    justify-content: center !important;
    padding: 0.65rem 0 !important;
  }

  .brand-header {
    justify-content: center !important;
    padding: 1.75rem 0 1.5rem !important;
  }

  .user-footer {
    justify-content: center !important;
    padding: 1rem 0 !important;
  }

  /* El contenido ocupa el espacio restante sin desborde */
  .main-content {
    margin-left: 220px;
    padding: 1.5rem;
  }
}
</style>

