<script setup lang="ts">
import { ref } from 'vue'
import ListLayout from '@/components/common/ListLayout.vue'
import ItemCard from '@/components/common/ItemCard.vue'

const pagos = ref([
  { id: 1, mes: 'Mayo 2026', monto: '$18000', estado: 'Pagado', fecha: '05/05/2026' },
  { id: 2, mes: 'Abril 2026', monto: '$18000', estado: 'Pagado', fecha: '04/04/2026' },
  { id: 3, mes: 'Marzo 2026', monto: '$15000', estado: 'Vencido', fecha: '-' }
])
</script>

<template>
  <ListLayout pageTitle="Mis Pagos">
    <ItemCard 
      v-for="pago in pagos" 
      :key="pago.id"
      :title="pago.mes"
      :subtitle="pago.monto"
    >
      <template #right>
        <span :class="['status-badge', pago.estado.toLowerCase()]">
          {{ pago.estado }}
        </span>
        <span v-if="pago.fecha !== '-'" class="pago-fecha">Abonado el {{ pago.fecha }}</span>
      </template>
    </ItemCard>
  </ListLayout>
</template>

<style scoped>
.status-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
}

.status-badge.pagado {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.status-badge.vencido {
  background-color: #ffebee;
  color: #c62828;
}

.pago-fecha {
  color: #7f8c8d;
  font-size: 12px;
}
</style>