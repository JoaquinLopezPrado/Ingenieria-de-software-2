<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import ListLayout from '@/components/ListLayout.vue'
import ItemCard from '@/components/ItemCard.vue'

interface AsistenciaItem {
  clase_id: number
  activity_name: string
  clase_date: string
  horario: string
  estado: 'presente' | 'ausente' | null
  fechaFormateada: string
}

const historial = ref<AsistenciaItem[]>([])
const isLoading = ref(true)
const hasError = ref(false)

const fmtFecha = (raw: string): string => {
  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ]
  const parts = raw.split('-')
  const dia = parseInt(parts[2] as string, 10)
  const mesIndex = parseInt(parts[1] as string, 10) - 1
  return `${dia} ${meses[mesIndex]}`
}

const fetchHistorial = async () => {
  try {
    isLoading.value = true
    hasError.value = false

    const res = await api.get('/attendances/me')
    historial.value = res.data.map((item: any) => ({
      clase_id: item.clase_id,
      activity_name: item.activity_name,
      clase_date: item.clase_date,
      horario: item.horario,
      estado: item.estado ?? null,
      fechaFormateada: fmtFecha(item.clase_date),
    }))
  } catch {
    hasError.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchHistorial()
})
</script>

<template>
  <ListLayout pageTitle="Mis Asistencias">
    <div class="central-wrapper">

      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <span>Cargando tu historial de asistencias...</span>
      </div>

      <div v-else-if="hasError" class="error-state">
        <span>No se pudo cargar el historial.</span>
        <button type="button" class="btn-retry" @click="fetchHistorial">Reintentar</button>
      </div>

      <div v-else class="cards-stack">
        <div v-if="historial.length === 0" class="empty-state">
          <span>No tenés asistencias registradas todavía</span>
        </div>

        <template v-else>
          <ItemCard
            v-for="item in historial"
            :key="item.clase_id"
            :title="item.activity_name"
            :subtitle="item.horario"
            class="asistencia-card"
          >
            <template #right>
              <div class="asistencia-right">
                <span class="fecha-label">{{ item.fechaFormateada }}</span>
                <span
                  v-if="item.estado"
                  :class="['estado-badge', item.estado === 'presente' ? 'presente' : 'ausente']"
                >
                  {{ item.estado === 'presente' ? 'Presente' : 'Ausente' }}
                </span>
                <span v-else class="estado-badge sin-registro">Sin registro</span>
              </div>
            </template>
          </ItemCard>
        </template>
      </div>

    </div>
  </ListLayout>
</template>

<style scoped>
.central-wrapper {
  width: 100%;
  max-width: 680px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
}

.cards-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.asistencia-card {
  width: 100%;
}

:deep(.item-card) {
  min-height: 90px;
  display: flex;
  align-items: center;
}

.asistencia-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  min-width: 110px;
}

.fecha-label {
  color: #2c3e50;
  font-size: 15px;
  font-weight: 700;
}

.estado-badge {
  font-size: 10px;
  font-weight: 800;
  padding: 2px 10px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.estado-badge.presente {
  background-color: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}

.estado-badge.ausente {
  background-color: #ffebee;
  color: #c62828;
  border: 1px solid #ffcdd2;
}

.estado-badge.sin-registro {
  background-color: #f5f5f5;
  color: #9e9e9e;
  border: 1px solid #e0e0e0;
}

.empty-state {
  background: rgba(255, 255, 255, 0.4);
  border: 2px dashed #cfeee6;
  padding: 40px 20px;
  text-align: center;
  border-radius: 16px;
  color: #78909c;
  font-size: 14px;
  font-weight: 600;
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 80px 20px;
  color: #12695f;
  font-weight: 700;
  font-size: 16px;
}
.error-state { color: #c62828; }
.btn-retry {
  background: #c62828;
  color: white;
  border: none;
  border-radius: 20px;
  padding: 8px 24px;
  font-weight: 700;
  cursor: pointer;
}
.spinner {
  width: 36px;
  height: 36px;
  border: 4px solid #cfeee6;
  border-top-color: #11a691;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
