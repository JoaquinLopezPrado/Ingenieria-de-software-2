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

const handleLogout = async () => {
  closeMenu()
  await authStore.logout()
  router.push('/login')
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
      <span class="bar"></span>
      <span class="bar"></span>
      <span class="bar"></span>
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
          <button type="button" @click="closeMenu">Mis clases</button>
        </li>
        <li>
          <button type="button" @click="closeMenu">Mis pagos</button>
        </li>
        <li class="logout-item">
          <button type="button" @click="handleLogout">Cerrar sesión</button>
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
  flex-direction: column;
  justify-content: space-between;
  width: 30px;
  height: 21px;
  background: transparent;
  border: none;
  cursor: pointer;
  z-index: 1001;
  padding: 0;
}

.bar {
  width: 100%;
  height: 3px;
  background-color: #11a691;
  border-radius: 2px;
  transition: all 0.3s ease;
}

.menu-toggle.is-active .bar:nth-child(1) {
  transform: translateY(9px) rotate(45deg);
}

.menu-toggle.is-active .bar:nth-child(2) {
  opacity: 0;
}

.menu-toggle.is-active .bar:nth-child(3) {
  transform: translateY(-9px) rotate(-45deg);
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
}

.logout-item button {
  color: #e53935;
}

.logout-item button:hover {
  background-color: #fff5f5;
  color: #e53935;
}

@media (min-width: 768px) {
  .menu-toggle {
    top: 24px;
    right: 24px;
  }
  
  .side-menu {
    width: 320px;
  }
}
</style>
