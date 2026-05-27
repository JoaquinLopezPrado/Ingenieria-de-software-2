<template>
  <div class="page">
    <div class="main">
      <div class="icon failure-icon">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </div>

      <h1>El pago no se completó</h1>
      <p class="subtitle">No se pudo procesar el pago. Tu reserva fue cancelada.</p>

      <div class="botones">
        <button class="btn-secondary" :disabled="cancelando" @click="verActividades">
          {{ cancelando ? 'Cancelando reserva...' : 'Ver actividades' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { enrollmentService } from '@/services/enrollmentService'

const route  = useRoute()
const router = useRouter()

const cancelando = ref(false)

const verActividades = async () => {
  const enrollmentId = Number(route.query.enrollment_id)
  if (enrollmentId) {
    cancelando.value = true
    try {
      await enrollmentService.cancelEnrollment(enrollmentId)
    } catch {
      // Si falla la cancelación, el job de expiración lo limpiará
    } finally {
      cancelando.value = false
    }
  }
  router.push({ name: 'list' })
}
</script>

<style scoped>
* { box-sizing: border-box; }
.page { min-height: 100vh; background: linear-gradient(135deg, #FFF5F5 0%, #FFF8F8 50%, #FFF0F0 100%); font-family: 'Segoe UI', system-ui, sans-serif; padding-top: 60px; }
.main { max-width: 480px; margin: 0 auto; padding: 60px 16px; display: flex; flex-direction: column; align-items: center; }
.icon { width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 24px; }
.failure-icon { background: linear-gradient(135deg, #E53935, #EF5350); box-shadow: 0 8px 24px rgba(229,57,53,0.3); }
h1 { font-size: 26px; font-weight: 800; color: #C62828; margin: 0 0 8px; text-align: center; }
.subtitle { font-size: 15px; color: #607D8B; margin: 0 0 32px; text-align: center; }
.botones { display: flex; flex-direction: column; gap: 10px; width: 100%; }
.btn-secondary { width: 100%; padding: 14px; border-radius: 99px; border: 2px solid #90A4AE; background: #fff; color: #546E7A; font-weight: 700; font-size: 14px; cursor: pointer; transition: background 0.2s; }
.btn-secondary:hover:not(:disabled) { background: #F5F5F5; }
.btn-secondary:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
