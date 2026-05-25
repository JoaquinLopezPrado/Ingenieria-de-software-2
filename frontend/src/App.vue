<script setup lang="ts">
import { computed } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import SideMenu from '@/components/SideMenu.vue'
import { isAdminUser } from '@/utils/role'

const authStore = useAuthStore()
const showGlobalSideMenu = computed(() => {
  if (!authStore.isAuthenticated || !authStore.user) {
    return false
  }

  return !isAdminUser(authStore.user)
})
</script>

<template>
  <div class="app-layout">
    <SideMenu v-if="showGlobalSideMenu" />

    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  position: relative;
  min-height: 100vh;
}

.main-content {
  width: 100%;
}
</style>
