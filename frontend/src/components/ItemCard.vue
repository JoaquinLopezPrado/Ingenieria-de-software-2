<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
}>()
</script>

<template>
  <div class="item-card">
    <div class="card-left">
      <span class="card-title">{{ title }}</span>
      <span v-if="subtitle" class="card-subtitle">{{ subtitle }}</span>
      <slot name="left-detail"></slot>
    </div>
    <div class="card-right">
      <slot name="right"></slot>
    </div>
  </div>
</template>

<style scoped>
.item-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;
  padding: 16px;
  border-radius: 16px;
  border: 2px solid #e0f2f1;
  box-shadow: 0 4px 12px rgba(17, 166, 145, 0.04);
}

.card-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-title {
  color: #2c3e50;
  font-size: 16px;
  font-weight: 700;
}

.card-subtitle {
  color: #7f8c8d;
  font-size: 13px;
}

.card-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}
</style>