<script setup lang="ts">
import { provide, toRef } from 'vue'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()

provide('tab-bar', {
  active: toRef(props, 'modelValue'),
  select: (val: string) => emit('update:modelValue', val),
})
</script>

<template>
  <div class="activities-bar" role="tablist">
    <slot />
  </div>
</template>

<style scoped>
.activities-bar {
  display: flex;
  gap: 8px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(10px);
  padding: 6px;
  border-radius: 999px;
  width: fit-content;
  margin-bottom: 28px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.05);
}

@media (max-width: 768px) {
  .activities-bar {
    width: 100%;
    overflow-x: auto;
  }
}
</style>
