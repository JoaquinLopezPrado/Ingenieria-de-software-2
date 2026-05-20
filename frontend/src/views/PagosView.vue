<script setup lang="ts">
import { ref } from 'vue'
import ListLayout from '@/components/ListLayout.vue'
import ItemCard from '@/components/ItemCard.vue'

interface PagoTurno {
  id: number
  actividad: string
  descripcion: string
  precio: string
  horario: string
  dias: string[]
  periodo: string
}

interface PagoClase {
  id: number
  actividad: string
  precio: string
  fecha: string
  hora: string
}

const pagosTurnos = ref<PagoTurno[]>([
  { 
    id: 1, 
    actividad: 'Crossfit', 
    descripcion: 'Turno Tarde Avanzado', 
    precio: '$18.000', 
    horario: '19:00 - 20:00',
    dias: ['Lunes', 'Miércoles', 'Viernes'],
    periodo: 'Mayo 2026' 
  },
  { 
    id: 2, 
    actividad: 'Funcional', 
    descripcion: 'Turno Mañana Inicial', 
    precio: '$18.000', 
    horario: '08:00 - 09:00',
    dias: ['Martes', 'Jueves'],
    periodo: 'Mayo 2026' 
  }
])

const pagosClases = ref<PagoClase[]>([
  { id: 101, actividad: 'Pilates', precio: '$4.500', fecha: '22 Mayo', hora: '17:00 hs' },
  { id: 102, actividad: 'Crossfit', precio: '$5.000', fecha: '23 Mayo', hora: '11:00 hs' }
])
</script>

<template>
  <ListLayout pageTitle="Mis Pagos">
    <div class="central-wrapper">
      <div class="columns-grid">
        
        <section class="pago-section">
          <div class="section-header">
            <h3>Turnos Fijos</h3>
          </div>

          <div class="cards-stack">
            <div v-if="pagosTurnos.length === 0" class="empty-column">
              <span>No hay registros de turnos</span>
            </div>
            <template v-else>
              <ItemCard
                v-for="turno in pagosTurnos"
                :key="turno.id"
                :title="turno.actividad"
                :subtitle="turno.descripcion"
                class="pago-card"
              >
                <template #right>
                  <div class="pago-right">
                    <span class="precio-label">{{ turno.precio }}</span>
                    <div class="dias-badge-container">
                      <span v-for="dia in turno.dias" :key="dia" class="dia-badge">
                        {{ dia.slice(0, 3) }}
                      </span>
                    </div>
                    <span class="horario-label">{{ turno.horario }}</span>
                    <span class="periodo-label">{{ turno.periodo }}</span>
                  </div>
                </template>
              </ItemCard>
            </template>
          </div>
        </section>

        <section class="pago-section">
          <div class="section-header">
            <h3>Clases Individuales</h3>
          </div>

          <div class="cards-stack">
            <div v-if="pagosClases.length === 0" class="empty-column">
              <span>No hay registros de clases sueltas</span>
            </div>
            <template v-else>
              <ItemCard
                v-for="clase in pagosClases"
                :key="clase.id"
                :title="clase.actividad"
                subtitle="Clase Individual"
                class="pago-card"
              >
                <template #right>
                  <div class="pago-right">
                    <span class="precio-label">{{ clase.precio }}</span>
                    <span class="fecha-badge">{{ clase.fecha }}</span>
                    <span class="horario-label-single">{{ clase.hora }}</span>
                  </div>
                </template>
              </ItemCard>
            </template>
          </div>
        </section>

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
  gap: 24px;
  width: 100%;
}

.pago-section {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.section-header {
  margin-bottom: 14px;
  border-bottom: 2px solid #cfeee6;
  padding-bottom: 6px;
}

.section-header h3 {
  color: #12695f;
  font-size: 18px;
  font-weight: 800;
  margin: 0;
}

.cards-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.pago-card {
  width: 100%;
}

.pago-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.precio-label {
  color: #11a691;
  font-weight: 800;
  font-size: 16px;
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
  font-size: 12px;
}

.fecha-badge {
  background: linear-gradient(135deg, #11a691 0%, #0d8277 100%);
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 10px;
}

.empty-column {
  background: rgba(255, 255, 255, 0.4);
  border: 2px dashed #cfeee6;
  padding: 32px;
  text-align: center;
  border-radius: 16px;
  color: #546e7a;
  font-size: 14px;
  font-weight: 600;
}

@media (min-width: 768px) {
  .central-wrapper {
    max-width: 960px;
  }

  .columns-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 32px;
  }
}

@media (max-width: 768px) {
  .pago-right {
    gap: 2px;
  }
}
</style>