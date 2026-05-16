<template>
  <div class="page">
    <div class="header">
      <div class="header-inner">
        <span class="logo">SIEMPREGYM</span>
      </div>
    </div>

    <div class="main">
      <div class="icon failure-icon">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </div>

      <h1>El pago no se completó</h1>
      <p class="subtitle">Podés intentarlo de nuevo o elegir otro método de pago.</p>

      <div class="card">
        <div class="card-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#E53935" stroke-width="2" stroke-linecap="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <div>
          <div class="card-label">Tu inscripción sigue reservada</div>
          <div class="card-value">Tenés 10 minutos para completar el pago</div>
        </div>
      </div>

      <div class="botones">
        <button class="btn-primary" @click="reintentar">
          Reintentar pago
        </button>
        <button class="btn-secondary" @click="router.push({ name: 'list' })">
          Ver actividades
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { enrollmentService } from '@/services/enrollmentService'

const route  = useRoute()
const router = useRouter()

const reintentar = async () => {
  const enrollmentId = Number(route.query.enrollment_id)
  if (!enrollmentId) return
  try {
    const { data } = await enrollmentService.createPaymentPreference(enrollmentId)
    window.location.href = data.init_point
  } catch {
    router.push({ name: 'list' })
  }
}
</script>

<style scoped>
* { box-sizing: border-box; }
.page { min-height: 100vh; background: linear-gradient(135deg, #FFF5F5 0%, #FFF8F8 50%, #FFF0F0 100%); font-family: 'Segoe UI', system-ui, sans-serif; }
.header { background: #fff; border-bottom: 1px solid #FFCDD2; padding: 0 24px; box-shadow: 0 2px 12px rgba(229,57,53,0.06); }
.header-inner { max-width: 600px; margin: 0 auto; display: flex; align-items: center; height: 60px; }
.logo { font-size: 19px; font-weight: 900; color: #00695C; letter-spacing: 0.08em; }
.main { max-width: 480px; margin: 0 auto; padding: 60px 16px; display: flex; flex-direction: column; align-items: center; }
.icon { width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 24px; }
.failure-icon { background: linear-gradient(135deg, #E53935, #EF5350); box-shadow: 0 8px 24px rgba(229,57,53,0.3); }
h1 { font-size: 26px; font-weight: 800; color: #C62828; margin: 0 0 8px; text-align: center; }
.subtitle { font-size: 15px; color: #607D8B; margin: 0 0 32px; text-align: center; }
.card { width: 100%; background: #fff; border-radius: 16px; padding: 20px 24px; display: flex; align-items: center; gap: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.07); border: 1px solid #FFCDD2; margin-bottom: 32px; }
.card-icon { width: 44px; height: 44px; border-radius: 12px; background: #FFEBEE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.card-label { font-size: 12px; color: #90A4AE; margin-bottom: 4px; }
.card-value { font-size: 15px; font-weight: 700; color: #C62828; }
.botones { display: flex; flex-direction: column; gap: 10px; width: 100%; }
.btn-primary { width: 100%; padding: 14px; border-radius: 99px; border: none; background: #009EE3; color: #fff; font-weight: 700; font-size: 14px; cursor: pointer; transition: background 0.2s; }
.btn-primary:hover { background: #0080C0; }
.btn-secondary { width: 100%; padding: 14px; border-radius: 99px; border: 2px solid #90A4AE; background: #fff; color: #546E7A; font-weight: 700; font-size: 14px; cursor: pointer; transition: background 0.2s; }
.btn-secondary:hover { background: #F5F5F5; }
</style>
