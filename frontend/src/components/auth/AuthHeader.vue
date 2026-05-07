<script setup lang="ts">
defineProps<{
  subtitle: string
}>()
</script>

<template>
  <div class="app-header">
    <h1 class="app-title">SIEMPREGYM</h1>
    <p class="app-subtitle">{{ subtitle }}</p>
  </div>
</template>

<style scoped>
.app-header {
  text-align: center;
  margin-bottom: 32px;
}

.app-title {
  font-size: 26px; /* Un poco más grande ahora que no está el logo */
  font-weight: 800;
  color: #00897b;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0;
}

.app-subtitle {
  color: #7f8c8d;
  font-size: 15px;
  margin-top: 6px;
}
</style>