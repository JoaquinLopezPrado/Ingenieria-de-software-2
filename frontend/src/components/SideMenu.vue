<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { storeToRefs } from 'pinia'

const authStore = useAuthStore()
const { isAuthenticated } = storeToRefs(authStore)
const router = useRouter()
const isMenuOpen = ref(false)

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
}

const closeMenu = () => {
  isMenuOpen.value = false
}

const navigateTo = (path: string) => {
  closeMenu()
  router.push(path)
}

const handleLogout = async () => {
  closeMenu()
  await authStore.logout()
  router.push('/')
}
</script>

<template>
  <div>
    <button 
      v-if="isAuthenticated"
      type="button" 
      class="menu-toggle" 
      @click="toggleMenu"
      :class="{ 'is-active': isMenuOpen }"
      aria-label="Abrir menú"
    >
      <div class="burger-container">
        <span class="bar"></span>
        <span class="bar"></span>
        <span class="bar"></span>
      </div>
    </button>

    <div 
      v-if="isMenuOpen && isAuthenticated" 
      class="menu-backdrop" 
      @click="closeMenu"
    ></div>

    <nav 
      v-if="isAuthenticated"
      class="side-menu" 
      :class="{ 'is-open': isMenuOpen }"
    >
      <div class="menu-header">
        <h3>SiempreGym</h3>
      </div>
      
      <ul class="menu-links">
        <li>
          <button type="button" @click="closeMenu">Vincular mi cuenta con Google</button>
        </li>
        <li>
          <button type="button" @click="navigateTo('/asistencias')">Mis asistencias</button>
        </li>
        <li>
          <button type="button" @click="navigateTo('/pagos')">Mis pagos</button>
        </li>
        <li class="logout-item">
          <button type="button" @click="handleLogout" class="btn-logout">
            <svg class="logout-icon" viewBox="0 0 24 24" width="20" height="20" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 17v-3H9v-4h7V7l5 5-5 5M14 2a2 2 0 0 1 2 2v2h-2V4H5v16h9v-2h2v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9z" fill="currentColor"/>
            </svg>
            <span>Cerrar sesión</span>
          </button>
        </li>
      </ul>
    </nav>
  </div>
</template>

<style scoped>
.menu-toggle {
  position: fixed;
  top: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: #ffffff;
  border: 2px solid #e0f2f1;
  border-radius: 50%;
  cursor: pointer;
  z-index: 1001;
  padding: 0;
  box-shadow: 0 4px 12px rgba(17, 166, 145, 0.12);
  transition: all 0.2s ease;
}

.menu-toggle:hover {
  border-color: #11a691;
  background-color: #f8fbfb;
}

.burger-container {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 20px;
  height: 14px;
}

.bar {
  width: 100%;
  height: 2px;
  background-color: #11a691;
  border-radius: 2px;
  transition: all 0.3s ease;
}

.menu-toggle.is-active .bar:nth-child(1) {
  transform: translateY(6px) rotate(45deg);
}

.menu-toggle.is-active .bar:nth-child(2) {
  opacity: 0;
}

.menu-toggle.is-active .bar:nth-child(3) {
  transform: translateY(-6px) rotate(-45deg);
}

.menu-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(18, 105, 95, 0.4);
  backdrop-filter: blur(4px);
  z-index: 999;
}

.side-menu {
  position: fixed;
  top: 0;
  left: 0;
  width: 280px;
  height: 100vh;
  background-color: #ffffff;
  z-index: 1000;
  box-shadow: 10px 0 30px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  transform: translateX(-100%);
  transition: transform 0.3s ease;
}

.side-menu.is-open {
  transform: translateX(0);
}

.menu-header {
  padding: 24px;
  border-bottom: 1px solid #e0f2f1;
}

.menu-header h3 {
  margin: 0;
  color: #12695f;
  font-size: 20px;
  font-weight: 800;
}

.menu-links {
  list-style: none;
  padding: 16px;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 100%;
}

.menu-links button {
  width: 100%;
  text-align: left;
  padding: 14px 16px;
  background: transparent;
  border: none;
  border-radius: 12px;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.menu-links button:hover {
  background-color: #f8fbfb;
  color: #11a691;
}

.logout-item {
  margin-top: auto;
  margin-bottom: 32px;
  padding: 0 8px;
}

.btn-logout {
  display: flex !important;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  background-color: #fff5f5 !important;
  color: #e53935 !important;
  border: 2px solid #ffcdd2 !important;
  border-radius: 30px !important;
  padding: 14px 20px !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 12px rgba(229, 57, 53, 0.08);
  transition: all 0.2s ease !important;
}

.btn-logout:hover {
  background-color: #e53935 !important;
  color: #ffffff !important;
  border-color: #e53935 !important;
  box-shadow: 0 6px 15px rgba(229, 57, 53, 0.2);
}

.logout-icon {
  flex-shrink: 0;
}

@media (min-width: 768px) {
  .menu-toggle {
    top: 24px;
    right: 24px;
    width: 50px;
    height: 50px;
  }
  
  .side-menu {
    width: 320px;
  }
}
</style>