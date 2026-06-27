<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import ListLayout from '@/components/ListLayout.vue'
import ItemCard from '@/components/ItemCard.vue'

type EstadoClase = 'estado-activa' | 'estado-pendiente' | 'estado-baja' | 'estado-confirmada' | 'estado-deposito'

interface InscripcionUnificada {
  id: number
  tipo: 'Suscripción Mensual' | 'Suscripción a Clase'
  actividad: string
  subtitulo: string
  instructor: string
  horario: string
  fechaInscripcion: string
  estadoLabel: string
  estadoClase: EstadoClase
  badgeFecha?: string
  dias?: string[]
}

const inscripciones = ref<InscripcionUnificada[]>([])
const isLoading = ref(true)
const hasError = ref(false)

const fmtTime = (t: string | undefined) => (t ?? '').padStart(5, '0')

const fmtFecha = (raw: string | undefined): string => {
  if (!raw) return ''
  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ]
  const datePart = raw.includes('T') ? raw.split('T')[0] : raw
  const parts = (datePart ?? '').split('-')
  if (parts.length !== 3) return raw
  const dia = parseInt(parts[2] as string, 10)
  const mesIndex = parseInt(parts[1] as string, 10) - 1
  return `${dia} ${meses[mesIndex]}`
}

const fetchInscripcionesActivas = async () => {
  try {
    isLoading.value = true
    hasError.value = false

    const [resSubscription, resSingle] = await Promise.all([
      api.get('/subscriptions/me'),
      api.get('/single-enrollments/me')
    ])

    const turnosMapeados: InscripcionUnificada[] = resSubscription.data.map((item: any) => {
      const desde = fmtFecha(item.start_date)
      const hasta = item.ends_on ? fmtFecha(item.ends_on) : null
      const bajaProgramada = item.status === 'active' && !!item.ends_on
      return {
        id: item.subscription_id,
        tipo: 'Suscripción Mensual' as const,
        actividad: item.activity_name,
        subtitulo: item.turno_description,
        instructor: item.instructor,
        horario: `${fmtTime(item.start_time)} - ${fmtTime(item.end_time)}`,
        fechaInscripcion: hasta ? `${desde} → ${hasta}` : `Desde ${desde}`,
        estadoLabel: bajaProgramada ? 'Baja programada' : item.status === 'active' ? 'Activa' : 'Pendiente de pago',
        estadoClase: (bajaProgramada ? 'estado-baja' : item.status === 'active' ? 'estado-activa' : 'estado-pendiente') as EstadoClase,
        dias: item.days ?? []
      }
    })

    const estadoSingle = (status: string): { label: string; clase: EstadoClase } => {
      if (status === 'confirmed') return { label: 'Confirmada', clase: 'estado-confirmada' }
      if (status === 'deposit_paid') return { label: 'Depósito pagado', clase: 'estado-deposito' }
      return { label: 'Pendiente de pago', clase: 'estado-pendiente' }
    }

    const clasesMapeadas: InscripcionUnificada[] = resSingle.data.map((item: any) => {
      const { label, clase } = estadoSingle(item.status)
      return {
        id: item.enrollment_id,
        tipo: 'Suscripción a Clase' as const,
        actividad: item.activity_name,
        subtitulo: item.turno_description,
        instructor: item.instructor,
        horario: `${fmtTime(item.start_time)} - ${fmtTime(item.end_time)}`,
        fechaInscripcion: `Inscripto el ${fmtFecha(item.created_at)}`,
        estadoLabel: label,
        estadoClase: clase,
        badgeFecha: fmtFecha(item.clase_date)
      }
    })

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
            <template #left-detail>
              <span class="instructor-label">Prof. {{ item.instructor }}</span>
              <span :class="['estado-badge', item.estadoClase]">{{ item.estadoLabel }}</span>
            </template>

            <template #right>
              <div class="inscripcion-right">
                <span :class="['type-badge', item.tipo === 'Suscripción Mensual' ? 'badge-turno' : 'badge-clase']">
                  {{ item.tipo }}
                </span>

                <div v-if="item.dias && item.dias.length > 0" class="dias-badge-container">
                  <span v-for="dia in item.dias" :key="dia" class="dia-badge">
                    {{ dia.slice(0, 3) }}
                  </span>
                </div>

                <span v-if="item.badgeFecha" class="fecha-badge">{{ item.badgeFecha }}</span>
                <span class="horario-label">{{ item.horario }}</span>
                <span class="inscripcion-detalle">{{ item.fechaInscripcion }}</span>
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

.instructor-label {
  color: #11a691;
  font-size: 12px;
  font-weight: 600;
}

.estado-badge {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
.estado-activa {
  background-color: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}
.estado-pendiente {
  background-color: #fff8e1;
  color: #f57f17;
  border: 1px solid #ffe082;
}
.estado-baja {
  background-color: #fff3e0;
  color: #e65100;
  border: 1px solid #ffcc80;
}
.estado-confirmada {
  background-color: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}
.estado-deposito {
  background-color: #e3f2fd;
  color: #1565c0;
  border: 1px solid #bbdefb;
}

.inscripcion-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 5px;
  height: 100%;
  min-width: 160px;
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

.inscripcion-detalle {
  color: #aab7b8;
  font-size: 10px;
  font-style: italic;
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
