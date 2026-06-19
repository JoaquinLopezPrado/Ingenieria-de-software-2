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

      <div v-if="motivoRechazo" class="motivo-card">
        <div class="motivo-titulo">Motivo del rechazo</div>
        <div class="motivo-texto">{{ motivoRechazo }}</div>
      </div>

      <div class="botones">
        <button class="btn-secondary" :disabled="cancelando" @click="verActividades">
          {{ cancelando ? 'Cancelando reserva...' : 'Ver actividades' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { enrollmentService } from '@/services/enrollmentService'

const route  = useRoute()
const router = useRouter()

const cancelando    = ref(false)
const motivoRechazo = ref(null)

const MOTIVOS = {
  cc_rejected_insufficient_amount:      'Fondos insuficientes en la tarjeta.',
  cc_rejected_bad_filled_card_number:   'El número de tarjeta es incorrecto.',
  cc_rejected_bad_filled_date:          'La fecha de vencimiento es incorrecta.',
  cc_rejected_bad_filled_security_code: 'El código de seguridad es incorrecto.',
  cc_rejected_bad_filled_other_reason:  'Los datos de la tarjeta son incorrectos.',
  cc_rejected_other_reason:             'El pago fue rechazado. Intentá con otra tarjeta.',
  cc_rejected_call_for_authorize:       'Debés autorizar el pago con tu banco antes de continuar.',
  cc_rejected_card_disabled:            'La tarjeta está deshabilitada. Contactá a tu banco.',
  cc_rejected_high_risk:                'El pago fue rechazado por razones de seguridad.',
  cc_rejected_max_attempts:             'Superaste el límite de intentos permitidos.',
  cc_rejected_blacklist:                'La tarjeta fue rechazada.',
  cc_rejected_duplicated_payment:       'Este pago ya fue procesado anteriormente.',
  cc_rejected_invalid_installments:     'La cantidad de cuotas no está disponible para esta tarjeta.',
  cc_amount_rate_limit_exceeded:        'Superaste el límite de monto permitido para este período.',
  rejected_by_bank:                     'El banco rechazó el pago. Contactá a tu entidad bancaria.',
  rejected_insufficient_data:           'Los datos de la tarjeta son incompletos o incorrectos.',
}

onMounted(async () => {
  const rawId = route.query.payment_id

  if (rawId === undefined) return

  if (!rawId || rawId === '0') {
    motivoRechazo.value = 'El tiempo para completar el pago expiró. Volvé a iniciar la inscripción.'
    return
  }

  try {
    const res = await enrollmentService.getMpStatusDetail(String(rawId))
    console.log('[MP failure] payment_id:', rawId)
    console.log('[MP failure] res.data:', res.data)
    const detail = res.data.status_detail
    console.log('[MP failure] status_detail:', detail)
    motivoRechazo.value = detail
      ? (MOTIVOS[detail] ?? 'El pago fue rechazado por Mercado Pago.')
      : 'Tiempo para realizar la compra expirado.'
  } catch {
    // no mostramos motivo si falla la consulta
  }
})

const verActividades = async () => {
  // ref: "single:{id}" | "sub:{charge_id}" (MP lo reenvía en la back_url y en external_reference).
  const ref = String(route.query.ref || route.query.external_reference || '')
  const [source, idStr] = ref.split(':')
  const id = Number(idStr)
  // Solo cancelamos sueltas acá; la suscripción pendiente la libera el job de expiración.
  if (source === 'single' && id) {
    cancelando.value = true
    try {
      await enrollmentService.cancelSingle(id)
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
.subtitle { font-size: 15px; color: #607D8B; margin: 0 0 24px; text-align: center; }

.motivo-card {
  width: 100%;
  background: #fff3f3;
  border: 1px solid #ffcdd2;
  border-radius: 14px;
  padding: 16px 20px;
  margin-bottom: 24px;
  text-align: center;
}
.motivo-titulo {
  font-size: 11px;
  font-weight: 700;
  color: #e53935;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 6px;
}
.motivo-texto {
  font-size: 14px;
  font-weight: 500;
  color: #b71c1c;
  line-height: 1.5;
}

.botones { display: flex; flex-direction: column; gap: 10px; width: 100%; }
.btn-secondary { width: 100%; padding: 14px; border-radius: 99px; border: 2px solid #90A4AE; background: #fff; color: #546E7A; font-weight: 700; font-size: 14px; cursor: pointer; transition: background 0.2s; }
.btn-secondary:hover:not(:disabled) { background: #F5F5F5; }
.btn-secondary:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
