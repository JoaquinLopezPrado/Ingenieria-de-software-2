<script setup lang="ts">
import { ref } from 'vue'
import ListLayout from '@/components/common/ListLayout.vue'
import ItemCard from '@/components/common/ItemCard.vue'

const asistencias = ref([
  { id: 1, fecha: '15/05/2026', clase: 'Crossfit', hora: '19:00', profesor: 'Lucas' },
  { id: 2, fecha: '13/05/2026', clase: 'Funcional', hora: '18:00', profesor: 'Mariana' },
  { id: 3, fecha: '11/05/2026', clase: 'Crossfit', hora: '19:00', profesor: 'Lucas' }
])
</script>

<template>
  <ListLayout pageTitle="Mis Asistencias">
    <ItemCard 
      v-for="item in asistencias" 
      :key="item.id"
      :title="item.clase"
      :subtitle="'Prof: ' + item.profesor"
    >
      <template #right>
        <span class="fecha-label">{{ item.fecha }}</span>
        <span class="hora-label">{{ item.hora }} hs</span>
      </template>
    </ItemCard>
  </ListLayout>
</template>

<style scoped>
.fecha-label {
  color: #11a691;
  font-weight: 700;
  font-size: 14px;
}

.hora-label {
  color: #546e7a;
  font-size: 13px;
}
</style>