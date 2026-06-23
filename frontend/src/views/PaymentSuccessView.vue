<template>
  <div class="page">

    <div class="main">
      <div class="icon success-icon">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      </div>

      <h1>¡Pago confirmado!</h1>
      <p class="subtitle">Tu inscripción quedó reservada. Te esperamos.</p>

      <div class="card">
        <div class="card-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00897B" stroke-width="2" stroke-linecap="round">
            <rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>
          </svg>
        </div>
        <div>
          <div class="card-label">Pago procesado correctamente</div>
          <div class="card-value">N° de comprobante {{ referencia }}</div>
        </div>
      </div>

      <div v-if="procesando" class="procesando-msg">
        Confirmando tu pago…
      </div>

      <div class="botones">
        <button class="btn-primary" :disabled="procesando" @click="router.push({ name: 'list' })">
          Ver actividades
        </button>
        <button class="btn-secondary" :disabled="procesando" @click="router.push({ name: 'home' })">
          Ir al inicio
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { enrollmentService } from '@/services/enrollmentService'

const route  = useRoute()
const router = useRouter()

const procesando = ref(false)

// ref: "single:{id}" | "sub:{charge_id}". Fallback al payment_id de MP.
const referencia = computed(() => {
  const ref = String(route.query.ref || route.query.external_reference || '')
  const [, idStr] = ref.split(':')
  return idStr || route.query.payment_id || ''
})

onMounted(async () => {
  const paymentId = String(route.query.payment_id || route.query.collection_id || '')
  if (!paymentId) return
  procesando.value = true
  try {
    await enrollmentService.notifyPayment(paymentId)
  } catch {
    // El webhook de MP lo procesará cuando llegue
  } finally {
    procesando.value = false
  }
})
</script>

<style scoped>
* { box-sizing: border-box; }
.page { min-height: 100vh; background: linear-gradient(135deg, #E0F7F4 0%, #F0FAF8 50%, #E8F5E9 100%); font-family: 'Segoe UI', system-ui, sans-serif; padding-top: 60px; }
.header { background: #fff; border-bottom: 1px solid #E0F2F1; padding: 0 24px; box-shadow: 0 2px 12px rgba(0,137,123,0.08); }
.header-inner { max-width: 600px; margin: 0 auto; display: flex; align-items: center; height: 60px; }
.logo { font-size: 19px; font-weight: 900; color: #00695C; letter-spacing: 0.08em; }
.main { max-width: 480px; margin: 0 auto; padding: 60px 16px; display: flex; flex-direction: column; align-items: center; }
.icon { width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 24px; }
.success-icon { background: linear-gradient(135deg, #00897B, #00BFA5); box-shadow: 0 8px 24px rgba(0,137,123,0.3); }
h1 { font-size: 26px; font-weight: 800; color: #00695C; margin: 0 0 8px; text-align: center; }
.subtitle { font-size: 15px; color: #607D8B; margin: 0 0 32px; text-align: center; }
.card { width: 100%; background: #fff; border-radius: 16px; padding: 20px 24px; display: flex; align-items: center; gap: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.07); border: 1px solid #E0F2F1; margin-bottom: 32px; }
.card-icon { width: 44px; height: 44px; border-radius: 12px; background: #E0F2F1; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.card-label { font-size: 12px; color: #90A4AE; margin-bottom: 4px; }
.card-value { font-size: 15px; font-weight: 700; color: #00695C; }
.botones { display: flex; flex-direction: column; gap: 10px; width: 100%; }
.btn-primary { width: 100%; padding: 14px; border-radius: 99px; border: none; background: #00897B; color: #fff; font-weight: 700; font-size: 14px; cursor: pointer; transition: background 0.2s; }
.btn-primary:hover { background: #00695C; }
.btn-secondary { width: 100%; padding: 14px; border-radius: 99px; border: 2px solid #00897B; background: #fff; color: #00897B; font-weight: 700; font-size: 14px; cursor: pointer; transition: background 0.2s; }
.btn-secondary:hover { background: #E0F2F1; }
.btn-primary:disabled, .btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }
.procesando-msg { font-size: 14px; color: #00695C; margin-bottom: 12px; font-weight: 500; }
</style>
