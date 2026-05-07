<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <RouterView />
</template>

<style>
/* Estilos globales mínimos para asegurar que el contenido ocupe todo */
#app {
  width: 100%;
  margin: 0;
  padding: 0;
  max-width: none; /* Quitamos el límite de 1280px */
}
</style>