<script setup lang="ts">
import { inject, computed, type Ref } from 'vue'

const props = defineProps<{ value: string }>()

const { active, select } = inject<{
  active: Ref<string>
  select: (value: string) => void
}>('tab-bar')!

const isActive = computed(() => active.value === props.value)
</script>

<template>
  <button
    type="button"
    role="tab"
    :class="['activity-btn', { active: isActive }]"
    :aria-selected="isActive"
    @click="select(value)"
  >
    <slot />
  </button>
</template>

<style scoped>
.activity-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 20px;
  border-radius: 999px;
  border: none;
  background: transparent;
  color: #78909c;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.22s ease;
}

.activity-btn:hover {
  background: rgba(0, 137, 123, 0.08);
}

.activity-btn.active {
  background: #00897b;
  color: white;
  font-weight: 700;
  box-shadow: 0 6px 14px rgba(0, 137, 123, 0.25);
}

@media (max-width: 768px) {
  .activity-btn {
    flex: 1;
    justify-content: center;
    white-space: nowrap;
  }
}
</style>
