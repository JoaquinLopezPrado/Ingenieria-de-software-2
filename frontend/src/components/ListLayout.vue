<script setup lang="ts">
defineProps<{
  pageTitle: string
}>()
</script>

<template>
  <div class="page-wrapper">
    <div class="header-section">
      <h2>{{ pageTitle }}</h2>
    </div>

    <div class="list-container">
      <slot></slot>
    </div>
  </div>
</template>

<style scoped>
.page-wrapper {
  padding: 80px 16px 24px 16px;
  min-height: 100vh;
  background-color: #dff8f2;
}

.header-section {
  margin-bottom: 24px;
  text-align: center;
}

.header-section h2 {
  color: #12695f;
  font-size: 24px;
  font-weight: 800;
  margin: 0;
}

.list-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

@media (min-width: 768px) {
  .page-wrapper {
    padding: 100px 24px 40px 24px;
  }

  .header-section {
    margin-bottom: 32px;
  }

  .header-section h2 {
    font-size: 32px;
  }
}
</style>