<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import ListLayout from '@/components/ListLayout.vue'
import ItemCard from '@/components/ItemCard.vue'

interface ClaseAsistenciaPlana {
  keyUnique: string
  tipo: 'Turno Fijo' | 'Clase Individual'
  actividad: string
  instructor: string
  fecha: string
  fechaObjeto: Date // La usamos para ordenar de forma cronológica exacta en el Front
  horario: string
  asistio: boolean
}

const historialClases = ref<ClaseAsistenciaPlana[]>([])
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

const fetchHistorialAsistencias = async () => {
  try {
    isLoading.value = true
    hasError.value = false

    // CAMBIO CLAVE: Cambiar '/my/monthly' por '/my/subscription'
    const [resSubscription, resSingle] = await Promise.all([
      api.get('/subscriptions/me'),
      api.get('/single-enrollments/me')
    ])
    
    
    const listaPlana: ClaseAsistenciaPlana[] = []

    // 1. Procesamos los desgloses internos de las suscripciones (turnos fijos)
    // Cambiamos resMonthly por resSubscription
    resSubscription.data.forEach((turno: any) => {
      const clasesAsociadas = turno.clases_asociadas || turno.slots || []
      clasesAsociadas.forEach((c: any) => {
        const fechaStr = c.date || c.fecha || c.clase?.date;
        listaPlana.push({
          keyUnique: `subscription-${turno.id}-${c.id}`,
          tipo: 'Turno Fijo',
          actividad: turno.actividad || turno.activity_name || 'Actividad',
          instructor: turno.instructor || 'Profesor',
          fecha: formatearFecha(fechaStr),
          fechaObjeto: new Date(fechaStr),
          horario: c.horario || turno.start_time?.slice(0, 5) || '00:00',
          asistio: c.asistio ?? c.has_attended ?? false
        })
      })
    })

    // 2. Procesamos las clases sueltas individuales (queda igual)
    resSingle.data.forEach((clase: any) => {
      const fechaStr = clase.date || clase.fecha || clase.clase?.date;
      listaPlana.push({
        keyUnique: `single-${clase.id}`,
        tipo: 'Clase Individual',
        actividad: clase.actividad || clase.activity_name || 'Clase Suelta',
        instructor: clase.instructor || 'Profesor',
        fecha: formatearFecha(fechaStr),
        fechaObjeto: new Date(fechaStr),
        horario: clase.horario || clase.start_time?.slice(0, 5) || '00:00',
        asistio: clase.asistio ?? clase.has_attended ?? false
      })
    })

    // Ordenamos el listado de forma segura
    historialClases.value = listaPlana.sort((a, b) => {
      const tiempoA = isNaN(a.fechaObjeto.getTime()) ? 0 : a.fechaObjeto.getTime()
      const tiempoB = isNaN(b.fechaObjeto.getTime()) ? 0 : b.fechaObjeto.getTime()
      return tiempoB - tiempoA
    })

  } catch (error) {
    console.error('Error al armar el historial de asistencias:', error)
    hasError.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchHistorialAsistencias()
})
</script>

<template>
  <ListLayout pageTitle="Mis Asistencias">
    <div class="central-wrapper">
      
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <span>Sincronizando historial de asistencias...</span>
      </div>

      <div v-else-if="hasError" class="error-state">
        <span>No se pudo procesar tu historial médico-deportivo.</span>
        <button type="button" class="btn-retry" @click="fetchHistorialAsistencias">Reintentar</button>
      </div>

      <div v-else class="cards-stack">
        <div v-if="historialClases.length === 0" class="empty-column-sub">
          <span>No tenés asistencias registradas en el sistema</span>
        </div>

        <template v-else>
          <ItemCard
            v-for="clase in historialClases"
            :key="clase.keyUnique"
            :title="clase.actividad"
            :subtitle="`Prof. ${clase.instructor}`"
            class="asistencia-card"
          >
            <template #right>
              <div class="inscripcion-right">
                <div class="tags-row">
                  <span :class="['type-badge', clase.tipo === 'Turno Fijo' ? 'badge-turno' : 'badge-clase']">
                    {{ clase.tipo }}
                  </span>
                  <span :class="['status-badge-inline', clase.asistio ? 'asistio' : 'no-asistio']">
                    {{ clase.asistio ? 'Asistió' : 'No asistió' }}
                  </span>
                </div>

                <span class="horario-label-single">{{ clase.fecha }}</span>
                <span class="periodo-label">{{ clase.horario }} hs</span>
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
  min-height: 106px;
  display: flex;
  align-items: center;
}

.inscripcion-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 6px;
  height: 100%;
  min-width: 150px;
}

.tags-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.type-badge {
  font-size: 9px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 6px;
  text-transform: uppercase;
}

.type-badge.badge-turno {
  background-color: #f5f5f5;
  color: #616161;
  border: 1px solid #e0e0e0;
}

.type-badge.badge-clase {
  background-color: #f5f5f5;
  color: #616161;
  border: 1px solid #e0e0e0;
}

.status-badge-inline {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 8px;
  text-transform: uppercase;
}

.status-badge-inline.asistio {
  background-color: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}

.status-badge-inline.no-asistio {
  background-color: #ffebee;
  color: #c62828;
  border: 1px solid #ffcdd2;
}

.horario-label-single {
  color: #2c3e50;
  font-weight: 700;
  font-size: 14px;
}

.periodo-label {
  color: #7f8c8d;
  font-size: 12px;
}

.empty-column-sub {
  background: rgba(255, 255, 255, 0.25);
  border: 1px dashed #b0bec5;
  padding: 32px 16px;
  text-align: center;
  border-radius: 12px;
  color: #78909c;
  font-size: 13px;
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