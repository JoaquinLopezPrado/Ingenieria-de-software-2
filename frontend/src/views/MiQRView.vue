<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import QRCode from 'qrcode'
import api from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import ListLayout from '@/components/ListLayout.vue'

interface ClaseHoy {
  clase_id: number
  activity_name: string
  horario: string
}

const authStore = useAuthStore()
const clasesHoy = ref<ClaseHoy[]>([])
const selectedClase = ref<ClaseHoy | null>(null)
const qrDataUrl = ref<string>('')
const isLoading = ref(true)
const hasError = ref(false)

const todayStr = (): string => {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const fetchClasesHoy = async () => {
  try {
    isLoading.value = true
    hasError.value = false
    const today = todayStr()
    const res = await api.get('/attendances/me')
    clasesHoy.value = (res.data as any[])
      .filter((item: any) => item.clase_date === today)
      .map((item: any) => ({
        clase_id: item.clase_id,
        activity_name: item.activity_name,
        horario: item.horario,
      }))
    if (clasesHoy.value.length === 1) {
      selectedClase.value = clasesHoy.value[0] ?? null
    }
  } catch {
    hasError.value = true
  } finally {
    isLoading.value = false
  }
}

const generateQR = async (clase: ClaseHoy) => {
  const userId = authStore.user?.id
  if (!userId) return
  const payload = JSON.stringify({ u: userId, c: clase.clase_id })
  qrDataUrl.value = await QRCode.toDataURL(payload, { width: 280, margin: 2 })
}

watch(selectedClase, (clase) => {
  if (clase) generateQR(clase)
  else qrDataUrl.value = ''
})

onMounted(fetchClasesHoy)
</script>

<template>
  <ListLayout pageTitle="Mi QR de asistencia">
    <div class="qr-wrapper">

      <div v-if="isLoading" class="state-box">
        <div class="spinner"></div>
        <span>Cargando tus clases de hoy...</span>
      </div>

      <div v-else-if="hasError" class="state-box error">
        <span>No se pudo cargar. Intentá de nuevo.</span>
        <button type="button" class="btn-retry" @click="fetchClasesHoy">Reintentar</button>
      </div>

      <div v-else-if="clasesHoy.length === 0" class="empty-card">
        <p class="empty-icon">📅</p>
        <p class="empty-title">Sin clases hoy</p>
        <p class="empty-sub">No tenés clases programadas para el día de hoy.</p>
      </div>

      <template v-else>
        <div v-if="clasesHoy.length > 1" class="selector-block">
          <p class="selector-label">¿A qué clase vas a entrar?</p>
          <div class="clase-options">
            <button
              v-for="clase in clasesHoy"
              :key="clase.clase_id"
              type="button"
              :class="['clase-btn', selectedClase?.clase_id === clase.clase_id ? 'selected' : '']"
              @click="selectedClase = clase"
            >
              <span class="clase-name">{{ clase.activity_name }}</span>
              <span class="clase-horario">{{ clase.horario }}</span>
            </button>
          </div>
        </div>

        <div v-if="selectedClase" class="qr-card">
          <p class="qr-actividad">{{ selectedClase.activity_name }}</p>
          <p class="qr-horario">{{ selectedClase.horario }}</p>
          <div class="qr-frame">
            <img v-if="qrDataUrl" :src="qrDataUrl" alt="QR de asistencia" class="qr-img" />
            <div v-else class="qr-placeholder">
              <div class="spinner"></div>
            </div>
          </div>
          <p class="qr-instruccion">Mostrá este código en la recepción</p>
        </div>

        <div v-else class="hint-card">
          <p>Seleccioná una clase para ver tu QR</p>
        </div>
      </template>

    </div>
  </ListLayout>
</template>

<style scoped>
.qr-wrapper {
  width: 100%;
  max-width: 420px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.state-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 80px 20px;
  color: #12695f;
  font-weight: 700;
  font-size: 16px;
}
.state-box.error { color: #c62828; }

.btn-retry {
  background: #c62828;
  color: white;
  border: none;
  border-radius: 20px;
  padding: 8px 24px;
  font-weight: 700;
  cursor: pointer;
}

.empty-card {
  background: white;
  border-radius: 20px;
  padding: 40px 24px;
  text-align: center;
  box-shadow: 0 4px 18px rgba(0,0,0,0.07);
}
.empty-icon { font-size: 2.8rem; margin: 0 0 12px; }
.empty-title { margin: 0 0 6px; font-size: 1.1rem; font-weight: 700; color: #1f2937; }
.empty-sub { margin: 0; color: #6b7280; font-size: 0.9rem; }

.selector-block { display: flex; flex-direction: column; gap: 10px; }
.selector-label { margin: 0; font-weight: 700; font-size: 0.95rem; color: #374151; }

.clase-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.clase-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 14px;
  padding: 14px 18px;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
}
.clase-btn.selected {
  border-color: #0d9b8a;
  background: #f0fdfa;
}
.clase-name { font-weight: 700; font-size: 0.95rem; color: #1f2937; }
.clase-horario { font-size: 0.82rem; color: #6b7280; }

.qr-card {
  background: white;
  border-radius: 24px;
  padding: 28px 24px;
  text-align: center;
  box-shadow: 0 6px 24px rgba(0,0,0,0.09);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.qr-actividad { margin: 0; font-size: 1.15rem; font-weight: 800; color: #0d9b8a; }
.qr-horario { margin: 0 0 12px; font-size: 0.9rem; color: #6b7280; font-weight: 600; }

.qr-frame {
  width: 280px;
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid #cfeee6;
  border-radius: 16px;
  overflow: hidden;
}
.qr-img { width: 100%; height: 100%; object-fit: contain; }

.qr-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr-instruccion {
  margin: 10px 0 0;
  font-size: 0.85rem;
  color: #9ca3af;
  font-weight: 600;
}

.hint-card {
  background: rgba(255,255,255,0.5);
  border: 2px dashed #cfeee6;
  border-radius: 16px;
  padding: 30px;
  text-align: center;
  color: #78909c;
  font-size: 0.9rem;
  font-weight: 600;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 4px solid #cfeee6;
  border-top-color: #11a691;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
