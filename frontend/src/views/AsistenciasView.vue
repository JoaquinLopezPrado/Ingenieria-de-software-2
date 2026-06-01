<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api' // Usamos tu cliente HTTP preconfigurado
import ListLayout from '@/components/ListLayout.vue'
import ItemCard from '@/components/ItemCard.vue'

interface ClaseInterna {
  id: number
  fecha: string
  horario: string
  asistio: boolean
}

interface TurnoInscripcion {
  id: number
  actividad: string
  descripcion: string
  instructor: string
  horario: string
  dias: string[]
  periodo: string
  is_active: boolean
  clasesAsociadas: ClaseInterna[]
}

interface ClaseIndividualInscripcion {
  id: number
  actividad: string
  instructor: string
  fecha: string
  horario: string
  is_active: boolean
  asistio: boolean
}

const router = useRouter()
const turnoSeleccionadoId = ref<number | null>(null)

// Estados para controlar el ciclo de vida de la petición de red
const turnos = ref<TurnoInscripcion[]>([])
const clases = ref<ClaseIndividualInscripcion[]>([])
const isLoading = ref(true)
const hasError = ref(false)

// Helper para pasar fechas nativas ISO (2026-05-22) a formato legible de interfaz ("22 Mayo")
const formatearFecha = (fechaRaw: string): string => {
  if (!fechaRaw) return ''
  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ]
  // Separamos los componentes para evitar desajustes de zona horaria local de JS
  const partes = fechaRaw.split('-')
  if (partes.length !== 3) return fechaRaw
  const dia = parseInt(partes[2] ?? '0', 10)
  const mesIndex = parseInt(partes[1] ?? '0', 10) - 1
  return `${dia} ${meses[mesIndex]}`
}

const fetchInscripcionesData = async () => {
  try {
    isLoading.value = true
    hasError.value = false

    // Solución al 404: Usamos el prefijo '/enrollments' coincidente con router.py
    // y removemos '/api/v1' ya que tu instancia base de 'api' lo incluye por defecto.
    const [resMonthly, resSingle] = await Promise.all([
      api.get('/enrollments/my/monthly'),
      api.get('/enrollments/my/single')
    ])

    // Mapeo adaptativo: transformamos la data pura del Back al modelo reactivo del Front
    turnos.value = resMonthly.data.map((item: any) => ({
      id: item.id,
      actividad: item.actividad || item.activity_name || 'Actividad',
      descripcion: item.descripcion || item.turno_description || 'Turno fijo',
      instructor: item.instructor || 'Profesor',
      horario: item.horario || `${item.start_time?.slice(0, 5)} - ${item.end_time?.slice(0, 5)}`,
      dias: item.dias || [],
      periodo: item.periodo || `Mes ${item.month}/${item.year}`,
      is_active: item.is_active ?? true,
      clasesAsociadas: (item.clases_asociadas || item.slots || []).map((c: any) => ({
        id: c.id,
        fecha: formatearFecha(c.fecha || c.date),
        horario: c.horario || c.start_time?.slice(0, 5) || '00:00',
        asistio: c.asistio ?? c.has_attended ?? false
      }))
    }))

    clases.value = resSingle.data.map((item: any) => ({
      id: item.id,
      actividad: item.actividad || item.activity_name || 'Clase Individual',
      instructor: item.instructor || 'Profesor',
      fecha: formatearFecha(item.fecha || item.date),
      horario: item.horario || item.start_time?.slice(0, 5) || '00:00',
      is_active: item.is_active ?? true,
      asistio: item.asistio ?? item.has_attended ?? false
    }))

  } catch (error) {
    console.error('Error al sincronizar con el backend de inscripciones:', error)
    hasError.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchInscripcionesData()
})

const turnosActivos = computed(() => turnos.value.filter(t => t.is_active))
const turnosPasados = computed(() => turnos.value.filter(t => !t.is_active))
const clasesActivas = computed(() => clases.value.filter(c => c.is_active))
const clasesPasadas = computed(() => clases.value.filter(c => !c.is_active))

const clasesDelTurnoSeleccionado = computed(() => {
  const turno = turnos.value.find(t => t.id === turnoSeleccionadoId.value)
  return turno ? turno.clasesAsociadas : []
})

const toggleVerAsistencias = (id: number) => {
  turnoSeleccionadoId.value = turnoSeleccionadoId.value === id ? null : id
}

const irAInscripciones = () => {
  router.push('/list')
}
</script>

<template>
  <ListLayout pageTitle="Mis Inscripciones">
    <div class="central-wrapper">
      
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <span>Sincronizando tus asistencias...</span>
      </div>

      <div v-else-if="hasError" class="error-state">
        <span>No se pudieron recuperar tus inscripciones actuales.</span>
        <button type="button" class="btn-retry" @click="fetchInscripcionesData">Reintentar</button>
      </div>
      
      <div v-else class="columns-grid">
        
        <section class="asistencia-section">
          <div class="section-header">
            <h3>Turnos Fijos</h3>
          </div>

          <div class="cards-stack">
            <div v-if="turnosActivos.length === 0" class="empty-column-sub">
              <span>No tenés turnos activos</span>
            </div>
            
            <template v-else>
              <div v-for="turno in turnosActivos" :key="turno.id" class="turno-group">
                <ItemCard 
                  :title="turno.actividad"
                  :subtitle="turno.descripcion"
                  class="inscripcion-card"
                >
                  <template #right>
                    <div class="inscripcion-right">
                      <div class="dias-badge-container">
                        <span v-for="dia in turno.dias" :key="dia" class="dia-badge">
                          {{ dia.slice(0, 3) }}
                        </span>
                      </div>
                      <span class="horario-label">{{ turno.horario }}</span>
                      <button type="button" class="btn-toggle-asistencias" @click="toggleVerAsistencias(turno.id)">
                        {{ turnoSeleccionadoId === turno.id ? 'Ocultar asistencias' : 'Ver asistencias' }}
                      </button>
                    </div>
                  </template>
                </ItemCard>

                <div v-if="turnoSeleccionadoId === turno.id" class="desglose-clases animate-fade">
                  <div class="desglose-header">Historial de clases del turno:</div>
                  <div v-if="clasesDelTurnoSeleccionado.length === 0" class="empty-column-sub">
                    <span>No hay clases registradas en este turno</span>
                  </div>
                  <ItemCard
                    v-for="cTurno in clasesDelTurnoSeleccionado"
                    :key="cTurno.id"
                    :title="turno.actividad"
                    :subtitle="'Prof. ' + turno.instructor"
                    class="inscripcion-card clase-desglose-card"
                  >
                    <template #right>
                      <div class="inscripcion-right">
                        <span :class="['status-badge-inline', cTurno.asistio ? 'asistio' : 'no-asistio']">
                          {{ cTurno.asistio ? 'Asistió' : 'No asistió' }}
                        </span>
                        <span class="horario-label-single">{{ cTurno.fecha }}</span>
                        <span class="periodo-label">{{ cTurno.horario }} hs</span>
                      </div>
                    </template>
                  </ItemCard>
                </div>
              </div>
            </template>

            <template v-if="turnosPasados.length > 0">
              <ItemCard 
                v-for="turno in turnosPasados" 
                :key="turno.id"
                :title="turno.actividad"
                :subtitle="turno.descripcion"
                class="inscripcion-card estado-pasado"
              >
                <template #right>
                  <div class="inscripcion-right">
                    <span class="status-badge-inactive">Inactivo</span>
                    <span class="horario-label">{{ turno.horario }}</span>
                    <span class="periodo-label">{{ turno.periodo }} · Prof. {{ turno.instructor }}</span>
                  </div>
                </template>
              </ItemCard>
            </template>
          </div>
        </section>

        <section class="asistencia-section">
          <div class="section-header">
            <h3>Clases Individuales</h3>
          </div>

          <div class="cards-stack">
            <div v-if="clasesActivas.length === 0" class="empty-column-sub">
              <span>No tenés clases activas</span>
            </div>
            <template v-else>
              <ItemCard 
                v-for="clase in clasesActivas" 
                :key="clase.id"
                :title="clase.actividad"
                :subtitle="'Prof. ' + clase.instructor"
                class="inscripcion-card"
              >
                <template #right>
                  <div class="inscripcion-right">
                    <span :class="['status-badge-inline', clase.asistio ? 'asistio' : 'no-asistio']">
                      {{ clase.asistio ? 'Asistió' : 'No asistió' }}
                    </span>
                    <span class="fecha-badge">{{ clase.fecha }}</span>
                    <span class="horario-label-single">{{ clase.horario }} hs</span>
                  </div>
                </template>
              </ItemCard>
            </template>

            <template v-if="clasesPasadas.length > 0">
              <ItemCard 
                v-for="clase in clasesPasadas" 
                :key="clase.id"
                :title="clase.actividad"
                :subtitle="'Prof. ' + clase.instructor"
                class="inscripcion-card estado-pasado"
              >
                <template #right>
                  <div class="inscripcion-right">
                    <div class="badges-row">
                      <span class="status-badge-inactive">Inactivo</span>
                      <span :class="['status-badge-inline', clase.asistio ? 'asistio' : 'no-asistio']">
                        {{ clase.asistio ? 'Asistió' : 'No asistió' }}
                      </span>
                    </div>
                    <span class="fecha-badge">{{ clase.fecha }}</span>
                    <span class="horario-label-single">{{ clase.horario }} hs</span>
                  </div>
                </template>
              </ItemCard>
            </template>
          </div>
        </section>

      </div>

      <div v-if="!isLoading && !hasError" class="suggestion-banner">
        <span class="suggestion-text">¿Buscás anotarte a nuevos turnos?</span>
        <button type="button" class="btn-action-link" @click="irAInscripciones">
          Hacé click acá
        </button>
      </div>

    </div>
  </ListLayout>
</template>

<style scoped>
.central-wrapper {
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
}

.columns-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 32px;
  width: 100%;
  margin-bottom: 24px;
}

.asistencia-section {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.section-header {
  margin-bottom: 16px;
  border-bottom: 2px solid #cfeee6;
  padding-bottom: 6px;
}

.section-header h3 {
  color: #12695f;
  font-size: 20px;
  font-weight: 800;
  margin: 0;
}

.cards-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.turno-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.inscripcion-card {
  transition: all 0.2s ease;
  width: 100%;
}

:deep(.item-card) {
  min-height: 106px;
  display: flex;
  align-items: center;
}

.clase-desglose-card {
  border-left: 4px solid #11a691 !important;
  background-color: #fbfdfd !important;
}

.inscripcion-card.estado-pasado {
  background-color: rgba(255, 255, 255, 0.5) !important;
  border-color: #cfd8dc !important;
  opacity: 0.65;
  filter: grayscale(0.6);
}

.inscripcion-card.estado-pasado .fecha-badge {
  background: #78909c !important;
  color: #ffffff !important;
}

.inscripcion-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 5px;
  height: 100%;
  min-width: 130px;
}

.dias-badge-container {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.dia-badge {
  background-color: #e0f2f1;
  color: #12695f;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 6px;
  text-transform: uppercase;
}

.btn-toggle-asistencias {
  background: transparent;
  border: none;
  color: #11a691;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  padding: 2px 0 0 0;
  text-decoration: underline;
  transition: color 0.2s;
}

.btn-toggle-asistencias:hover {
  color: #0d8277;
}

.desglose-clases {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 0 12px 16px;
}

.desglose-header {
  font-size: 12px;
  font-weight: 700;
  color: #546e7a;
  text-transform: uppercase;
  margin-bottom: 2px;
}

.badges-row {
  display: flex;
  gap: 4px;
  align-items: center;
}

.status-badge-inactive {
  background-color: #eceff1;
  color: #546e7a;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 8px;
  text-transform: uppercase;
  border: 1px solid #b0bec5;
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

.horario-label {
  color: #2c3e50;
  font-weight: 700;
  font-size: 13px;
}

.horario-label-single {
  color: #2c3e50;
  font-weight: 700;
  font-size: 13px;
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

.suggestion-banner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background-color: #ffffff;
  border: 2px dashed #11a691;
  padding: 20px;
  border-radius: 16px;
  text-align: center;
  margin-top: 24px;
  width: 100%;
  box-shadow: 0 4px 12px rgba(13, 110, 95, 0.04);
}

.suggestion-text {
  color: #12695f;
  font-size: 15px;
  font-weight: 700;
}

.btn-action-link {
  background: #11a691;
  color: white;
  border: none;
  border-radius: 20px;
  padding: 8px 24px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(17, 166, 145, 0.2);
  transition: all 0.2s ease;
}

.btn-action-link:hover {
  background: #0d8277;
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(13, 130, 119, 0.3);
}

.empty-column-sub {
  background: rgba(255, 255, 255, 0.25);
  border: 1px dashed #b0bec5;
  padding: 16px;
  text-align: center;
  border-radius: 12px;
  color: #78909c;
  font-size: 13px;
  font-weight: 600;
}

.animate-fade {
  animation: fadeIn 0.2s ease-out forwards;
}

/* Clases de Feedback de Red */
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

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (min-width: 768px) {
  .central-wrapper {
    max-width: 960px;
  }
  .columns-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .suggestion-banner {
    flex-direction: row;
    justify-content: space-between;
    padding: 16px 24px;
    text-align: left;
    gap: 0;
  }
  .suggestion-text {
    font-size: 16px;
  }
}

@media (max-width: 768px) {
  .inscripcion-right {
    gap: 4px;
  }
}
</style>