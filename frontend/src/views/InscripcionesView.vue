<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import ListLayout from '@/components/ListLayout.vue'
import ItemCard from '@/components/ItemCard.vue'

interface InscripcionUnificada {
  id: number
  tipo: 'Turno Fijo' | 'Clase Individual'
  actividad: string
  subtitulo: string
  horario: string
  detalles: string
  badgeFecha?: string
  dias?: string[]
}

const inscripciones = ref<InscripcionUnificada[]>([])
const isLoading = ref(true)
const hasError = ref(false)

const formatearFecha = (fechaRaw: string): string => {
  if (!fechaRaw) return ''
  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ]
  const partes = fechaRaw.split('-')
  if (partes.length !== 3) return fechaRaw
  const dia = parseInt(partes[2], 10)
  const mesIndex = parseInt(partes[1], 10) - 1
  return `${dia} ${meses[mesIndex]}`
}

const fetchInscripcionesActivas = async () => {
  try {
    isLoading.value = true
    hasError.value = false

    // CAMBIO CLAVE: Cambiar '/my/monthly' por '/my/subscription'
    const [resSubscription, resSingle] = await Promise.all([
      api.get('/subscriptions/me'),
      api.get('/single-enrollments/me')
    ])
    
    // Cambiamos resMonthly por resSubscription
    const turnosMapeados = resSubscription.data
      .filter((item: any) => item.is_active ?? true)
      .map((item: any) => ({
        id: item.id,
        tipo: 'Turno Fijo' as const,
        actividad: item.actividad || item.activity_name || 'Actividad',
        subtitulo: item.descripcion || item.turno_description || 'Turno fijo',
        horario: item.horario || `${item.start_time?.slice(0, 5)} - ${item.end_time?.slice(0, 5)}`,
        detalles: item.periodo || `Mes ${item.month}/${item.year} · Prof. ${item.instructor || 'Profesor'}`,
        dias: item.dias || []
      }))

    const clasesMapeadas = resSingle.data
      .filter((item: any) => item.is_active ?? true)
      .map((item: any) => ({
        id: item.id,
        tipo: 'Clase Individual' as const,
        actividad: item.actividad || item.activity_name || 'Clase Suelta',
        subtitulo: `Prof. ${item.instructor || 'Profesor'}`,
        horario: `${item.horario || item.start_time?.slice(0, 5) || '00:00'} hs`,
        badgeFecha: formatearFecha(item.date || item.fecha || item.clase?.date),
        detalles: 'Reserva única'
      }))

    inscripciones.value = [...turnosMapeados, ...clasesMapeadas]

  } catch (error) {
    console.error('Error cargando inscripciones activas:', error)
    hasError.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchInscripcionesActivas()
})
</script>

<template>
  <ListLayout pageTitle="Mis Inscripciones">
    <div class="central-wrapper">
      
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <span>Cargando tus inscripciones vigentes...</span>
      </div>

      <div v-else-if="hasError" class="error-state">
        <span>No se pudieron recuperar tus inscripciones.</span>
        <button type="button" class="btn-retry" @click="fetchInscripcionesActivas">Reintentar</button>
      </div>

      <div v-else class="cards-stack">
        <div v-if="inscripciones.length === 0" class="empty-column-sub">
          <span>No tenés ninguna inscripción activa en este momento</span>
        </div>

        <template v-else>
          <ItemCard
            v-for="item in inscripciones"
            :key="`${item.tipo}-${item.id}`"
            :title="item.actividad"
            :subtitle="item.subtitulo"
            class="inscripcion-card"
          >
            <template #right>
              <div class="inscripcion-right">
                <span :class="['type-badge', item.tipo === 'Turno Fijo' ? 'badge-turno' : 'badge-clase']">
                  {{ item.tipo }}
                </span>

                <div v-if="item.dias && item.dias.length > 0" class="dias-badge-container">
                  <span v-for="dia in item.dias" :key="dia" class="dia-badge">
                    {{ dia.slice(0, 3) }}
                  </span>
                </div>

                <span v-if="item.badgeFecha" class="fecha-badge">{{ item.badgeFecha }}</span>
                <span class="horario-label">{{ item.horario }}</span>
                <span class="periodo-label">{{ item.detalles }}</span>
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
  gap: 14px;
  width: 100%;
}

.inscripcion-card {
  width: 100%;
}

:deep(.item-card) {
  min-height: 110px;
  display: flex;
  align-items: center;
}

.inscripcion-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 5px;
  height: 100%;
  min-width: 140px;
}

.type-badge {
  font-size: 10px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 8px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.type-badge.badge-turno {
  background-color: #e0f2f1;
  color: #12695f;
  border: 1px solid #b2dfdb;
}

.type-badge.badge-clase {
  background-color: #e3f2fd;
  color: #0d47a1;
  border: 1px solid #bbdefb;
}

.dias-badge-container {
  display: flex;
  gap: 4px;
}

.dia-badge {
  background-color: #f5f5f5;
  color: #616161;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 4px;
  text-transform: uppercase;
}

.horario-label {
  color: #2c3e50;
  font-weight: 700;
  font-size: 14px;
}

.periodo-label {
  color: #7f8c8d;
  font-size: 11px;
}

.fecha-badge {
  background: linear-gradient(135deg, #11a691 0%, #0d8277 100%);
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 10px;
}

.empty-column-sub {
  background: rgba(255, 255, 255, 0.4);
  border: 2px dashed #cfeee6;
  padding: 40px 20px;
  text-align: center;
  border-radius: 16px;
  color: #78909c;
  font-size: 14px;
  font-weight: 600;
}

/* Feedback de Red */
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
.error-state {
  color: #c62828;
}
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

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>