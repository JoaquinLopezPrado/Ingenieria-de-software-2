<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import AdminLayout from '@/components/layout/AdminLayout.vue'

interface ClaseHoy {
  clase_id: number
  activity_name: string
  instructor: string
  start_time: string
  end_time: string
  capacity: number
  is_active: boolean
}

const router = useRouter()
const clases = ref<ClaseHoy[]>([])
const isLoading = ref(true)
const hasError = ref(false)

const fetchClases = async () => {
  try {
    isLoading.value = true
    hasError.value = false
    const res = await api.get('/clases/hoy')
    clases.value = res.data as ClaseHoy[]
  } catch {
    hasError.value = true
  } finally {
    isLoading.value = false
  }
}

const goToAsistencias = (clase: ClaseHoy) => {
  router.push({
    name: 'clase-asistencias',
    params: { claseId: clase.clase_id },
    query: {
      actividad: clase.activity_name,
      instructor: clase.instructor,
      horario: `${clase.start_time} – ${clase.end_time}`,
    },
  })
}

const todayLabel = (() => {
  const d = new Date()
  return d.toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })
})()

onMounted(fetchClases)
</script>

<template>
  <AdminLayout>
    <div class="clases-content">
      <div class="page-header">
        <h1 class="page-title">Asistencias</h1>
        <p class="page-sub">{{ todayLabel }}</p>
      </div>

      <div v-if="isLoading" class="state-box">
        <div class="spinner"></div>
        <span>Cargando clases de hoy...</span>
      </div>

      <div v-else-if="hasError" class="state-box error">
        <span>No se pudieron cargar las clases.</span>
        <button type="button" class="btn-retry" @click="fetchClases">Reintentar</button>
      </div>

      <div v-else-if="clases.length === 0" class="empty-card">
        <p class="empty-icon">📅</p>
        <p class="empty-title">Sin clases hoy</p>
        <p class="empty-sub">No hay clases programadas para el día de hoy.</p>
      </div>

      <div v-else class="clases-grid">
        <div
          v-for="clase in clases"
          :key="clase.clase_id"
          class="clase-card"
          :class="{ 'inactive': !clase.is_active }"
          @click="goToAsistencias(clase)"
        >
          <div class="clase-left">
            <span v-if="!clase.is_active" class="badge-cancelada">Cancelada</span>
            <p class="clase-actividad">{{ clase.activity_name }}</p>
            <p class="clase-instructor">Prof. {{ clase.instructor }}</p>
          </div>
          <div class="clase-right">
            <p class="clase-horario">{{ clase.start_time }} – {{ clase.end_time }}</p>
            <p class="clase-cupo">Cupo: {{ clase.capacity }}</p>
            <span v-if="clase.is_active" class="btn-asistencias">Ver asistencias →</span>
          </div>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<style scoped>
.clases-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 760px;
}

.page-header { display: flex; flex-direction: column; gap: 4px; }
.page-title { margin: 0; font-size: 1.6rem; font-weight: 800; color: #1f2937; }
.page-sub { margin: 0; font-size: 0.9rem; color: #6b7280; text-transform: capitalize; }

.state-box {
  display: flex; flex-direction: column; align-items: center;
  gap: 16px; padding: 60px 20px;
  color: #12695f; font-weight: 700; font-size: 1rem;
}
.state-box.error { color: #c62828; }
.btn-retry {
  background: #c62828; color: white; border: none;
  border-radius: 20px; padding: 8px 24px; font-weight: 700; cursor: pointer;
}

.empty-card {
  background: white; border-radius: 20px; padding: 48px 28px;
  text-align: center; box-shadow: 0 4px 14px rgba(0,0,0,0.06);
}
.empty-icon { font-size: 2.4rem; margin: 0 0 10px; }
.empty-title { margin: 0 0 6px; font-size: 1.1rem; font-weight: 700; color: #1f2937; }
.empty-sub { margin: 0; color: #6b7280; font-size: 0.9rem; }

.clases-grid { display: flex; flex-direction: column; gap: 12px; }

.clase-card {
  background: white;
  border-radius: 16px;
  padding: 18px 22px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  border-left: 4px solid #0d9b8a;
}
.clase-card:hover { transform: translateX(3px); box-shadow: 0 4px 18px rgba(0,0,0,0.1); }
.clase-card.inactive { border-left-color: #e0e0e0; opacity: 0.7; cursor: default; }
.clase-card.inactive:hover { transform: none; }

.clase-left { display: flex; flex-direction: column; gap: 4px; }
.clase-actividad { margin: 0; font-size: 1rem; font-weight: 700; color: #1f2937; }
.clase-instructor { margin: 0; font-size: 0.85rem; color: #6b7280; }

.clase-right { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.clase-horario { margin: 0; font-size: 0.95rem; font-weight: 700; color: #0d9b8a; }
.clase-cupo { margin: 0; font-size: 0.8rem; color: #9ca3af; }
.btn-asistencias { font-size: 0.82rem; font-weight: 700; color: #0d9b8a; }

.badge-cancelada {
  display: inline-block;
  background: #fce4e4; color: #c62828;
  border: 1px solid #ffcdd2;
  font-size: 0.7rem; font-weight: 800;
  padding: 2px 10px; border-radius: 20px;
  letter-spacing: 0.3px; margin-bottom: 2px;
}

.spinner {
  width: 32px; height: 32px;
  border: 4px solid #cfeee6; border-top-color: #11a691;
  border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
