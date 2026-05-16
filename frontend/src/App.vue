<script setup lang="ts">
import { RouterView } from 'vue-router'
import SideMenu from '@/components/SideMenu.vue'
</script>

<template>
  <div class="app-layout">
    <SideMenu />

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