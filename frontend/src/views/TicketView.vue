<template>
  <div class="page">
 
    <div class="main">
      <!-- Ícono de éxito -->
      <div class="success-icon">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      </div>
 
      <h1 v-if="creditConfirmed">¡Inscripción confirmada!</h1>
      <h1 v-else-if="creditOffer">{{ creditMessage }}</h1>
      <h1 v-else>¡Se reservo tu lugar hasta finalizar el pago!</h1>
      <p class="subtitle">Te esperamos.</p>
 
      <!-- Comprobante -->
      <div class="comprobante">
 
        <div class="comp-header">
          <div>
            <div class="comp-titulo">Comprobante de inscripción</div>
            <div class="comp-numero">N° {{ route.query.numero }}</div>
          </div>
          <div class="comp-fecha">{{ fechaHoy }}</div>
        </div>
 
        <div class="divider"></div>
 
        <div class="actividad-nombre">{{ route.query.actividad }}{{ route.query.descripcion ? ' - ' + route.query.descripcion : '' }}</div>
 
        <div class="datos-grid">
          <div class="dato">
            <div class="dato-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00897B" stroke-width="2" stroke-linecap="round">
                <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
            </div>
            <div>
              <div class="dato-label">Días</div>
              <div class="day-chips">
                <span v-for="day in diasArray" :key="day" class="day-chip">
                  {{ DAY_LABELS[day] ?? day }}
                </span>
              </div>
            </div>
          </div>
 
          <div class="dato">
            <div class="dato-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00897B" stroke-width="2" stroke-linecap="round">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
            </div>
            <div>
              <div class="dato-label">Horario</div>
              <div class="dato-valor">{{ route.query.duracion }}</div>
            </div>
          </div>
 
          <div class="dato">
            <div class="dato-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00897B" stroke-width="2" stroke-linecap="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <div>
              <div class="dato-label">Instructor/a</div>
              <div class="dato-valor">{{ route.query.instructor }}</div>
            </div>
          </div>

          <div v-if="kind === 'subscription' && route.query.periodo" class="dato">
            <div class="dato-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00897B" stroke-width="2" stroke-linecap="round">
                <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
            </div>
            <div>
              <div class="dato-label">Primer período</div>
              <div class="dato-valor">{{ route.query.periodo }}</div>
            </div>
          </div>
 
          <div class="dato">
            <div class="dato-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00897B" stroke-width="2" stroke-linecap="round">
              </svg>
            </div>
            <div>
            </div>
          </div>
        </div>
 
        <div class="divider"></div>
 
        <template v-if="creditConfirmed">
          <div class="monto-row">
            <span class="monto-label">Precio de la clase</span>
            <span class="monto-valor-base">$ {{ fmt(route.query.credit_amount) }}</span>
          </div>
          <div class="monto-row monto-row-descuento">
            <span class="monto-label">Crédito aplicado 🎟</span>
            <span class="monto-descuento">- $ {{ fmt(route.query.credit_amount) }}</span>
          </div>
          <div class="monto-row monto-row-total">
            <span class="monto-label"><strong>Total pagado</strong></span>
            <span class="monto-valor">$ 0,00</span>
          </div>
        </template>
        <template v-else-if="route.query.precio_clase">
          <div class="monto-row">
            <span class="monto-label">Valor de la clase</span>
            <span class="monto-valor-base">$ {{ fmt(route.query.precio_clase) }}</span>
          </div>
          <div class="monto-row monto-row-total">
            <span class="monto-label"><strong>Total a pagar</strong></span>
            <span class="monto-valor">$ {{ fmt(route.query.amount) }}</span>
          </div>
        </template>
        <template v-else-if="tieneDescuento">
          <div class="monto-row">
            <span class="monto-label">Precio mensual</span>
            <span class="monto-valor-base">$ {{ fmt(precioBase) }}</span>
          </div>
          <div v-if="discountFull > 0" class="monto-row monto-row-descuento">
            <span class="monto-label">Descuento por clase con cupo lleno</span>
            <span class="monto-descuento">- $ {{ fmt(discountFull) }}</span>
          </div>
          <div v-if="discountConfirmed > 0" class="monto-row monto-row-descuento">
            <span class="monto-label">Descuento por clases individuales ya abonadas</span>
            <span class="monto-descuento">- $ {{ fmt(discountConfirmed) }}</span>
          </div>
          <div v-if="discountDepositSingle > 0" class="monto-row monto-row-descuento">
            <span class="monto-label">Descuento por señas ya abonadas</span>
            <span class="monto-descuento">- $ {{ fmt(discountDepositSingle) }}</span>
          </div>
          <div class="monto-row monto-row-total">
            <span class="monto-label"><strong>Total a pagar</strong></span>
            <span class="monto-valor">$ {{ fmt(route.query.amount) }}</span>
          </div>
        </template>
        <div v-else class="monto-row">
          <span class="monto-label">Total a pagar</span>
          <span class="monto-valor">$ {{ fmt(route.query.amount) }}</span>
        </div>

      </div>
 
      <!-- Banner de crédito disponible -->
      <div v-if="creditOffer && !creditConfirmed" class="credit-banner-ticket">
        <div class="credit-banner-info">
          <span class="credit-icon">🎟</span>
          <div>
            <strong>{{ creditMessage }}</strong>
            <span class="credit-detail">Aplicalo y no pagues nada por esta clase</span>
          </div>
        </div>
      </div>

      <!-- Contador de tiempo -->
      <div v-if="!creditOffer && route.query.expires_at && !expirado" :class="['countdown', { urgente: countdownUrgente }]">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
        </svg>
        Tiempo para pagar: <strong>{{ countdown }}</strong>
      </div>
      <div v-else-if="!creditOffer && expirado" class="countdown expirado">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        El tiempo para pagar expiró. Tu reserva fue liberada.
      </div>

      <!-- Botones -->
      <div class="botones">
        <template v-if="creditConfirmed">
          <button class="btn-volver" @click="router.push({ name: 'list' })">← Volver a actividades</button>
        </template>
        <template v-else-if="creditOffer">
          <button class="btn-mp btn-credito" :disabled="pagando" @click="usarCredito">
            {{ pagando ? 'Confirmando...' : '🎟  Confirmar con crédito (¡Gratis!)' }}
          </button>
          <button class="btn-mp btn-mp--senia" :disabled="pagando" @click="pagarSinCredito">
            {{ pagando ? 'Procesando...' : 'Pagar sin usar el crédito' }}
          </button>
          <button class="btn-volver" :disabled="pagando" @click="router.push({ name: 'list' })">← Cancelar</button>
        </template>
        <template v-else-if="esSinCosto">
          <button class="btn-mp" :disabled="pagando" @click="confirmarGratis">
            {{ pagando ? 'Confirmando...' : 'Confirmar suscripción (sin costo)' }}
          </button>
        </template>
        <template v-else>
          <button v-if="!expirado" class="btn-mp" :disabled="pagando" @click="pagar">
            {{ pagando ? 'Redirigiendo...' : `Pagar total $${fmt(route.query.amount)}` }}
          </button>
          <button
            v-if="!expirado && esSingle && depositAvailable"
            class="btn-mp btn-mp--senia"
            :disabled="pagando"
            @click="pagarSenia"
          >
            {{ pagando ? 'Redirigiendo...' : `Pagar seña $${fmt(montoSenia)} (30%)` }}
          </button>
        </template>
        <button v-if="!creditOffer && !creditConfirmed" class="btn-volver" @click="router.push({ name: 'list' })">
          ← Volver a actividades
        </button>
      </div>
    </div>

    <!-- Modal de error -->
    <div v-if="errorMsg" class="error-modal-backdrop" @click.self="errorMsg = ''">
      <div class="error-modal">
        <div class="error-modal-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#C62828" stroke-width="2.5" stroke-linecap="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <circle cx="12" cy="16" r="0.5" fill="#C62828"/>
          </svg>
        </div>
        <p class="error-modal-msg">{{ errorMsg }}</p>
        <button class="error-modal-btn" @click="errorMsg = ''">Entendido</button>
      </div>
    </div>
  </div>
</template>
 
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { enrollmentService } from '@/services/enrollmentService'

const route  = useRoute()
const router = useRouter()

const fmt = (val) => Number(val ?? 0).toLocaleString('es-AR', { minimumFractionDigits: 2 })

const esSinCosto = computed(() => Number(route.query.amount ?? 0) === 0)
// kind: 'subscription' | 'single' (compat: enrollment_type viejo === 'single')
const kind       = computed(() => route.query.kind || (route.query.enrollment_type === 'single' ? 'single' : 'subscription'))
const esSingle   = computed(() => kind.value === 'single')
const montoSenia = computed(() => Math.round(Number(route.query.amount ?? 0) * 0.30 * 100) / 100)

const discountFull          = computed(() => Number(route.query.discount_full_classes ?? 0))
const discountDepositSingle = computed(() => Number(route.query.discount_deposit_single ?? 0))
const discountSingle        = computed(() => Number(route.query.original_amount ?? 0) - Number(route.query.amount ?? 0))
const discountConfirmed     = computed(() => discountSingle.value - discountDepositSingle.value - discountFull.value)
const precioBase            = computed(() => Number(route.query.original_amount ?? 0))

const tieneDescuento = computed(() => discountFull.value > 0 || discountSingle.value > 0)

const depositAvailable = computed(() => {
  const raw = route.query.clase_start
  if (!raw) return true
  const claseStart = new Date(raw)
  const oneHourBefore = new Date(claseStart.getTime() - 60 * 60 * 1000)
  return Date.now() < oneHourBefore.getTime()
})

const DAY_LABELS = {
  lunes: 'Lun', martes: 'Mar', miercoles: 'Mié',
  jueves: 'Jue', viernes: 'Vie', sabado: 'Sáb',
}

const diasArray = computed(() =>
  String(route.query.dia || '').split(' / ').filter(Boolean)
)

const creditOffer     = computed(() => route.query.credit_offer === 'true')
const creditConfirmed = ref(false)
const creditCount     = computed(() => Number(route.query.credit_count) || 1)
const creditMessage   = computed(() =>
  `Tenés ${creditCount.value} crédito${creditCount.value !== 1 ? 's' : ''} disponible${creditCount.value !== 1 ? 's' : ''}`
)

const pagando  = ref(false)
const expirado = ref(false)
const errorMsg = ref('')
const segundosRestantes = ref(0)
let intervalo = null

const fechaHoy = (() => {
  const s = new Date().toLocaleDateString('es-AR', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  })
  return s.charAt(0).toUpperCase() + s.slice(1)
})()

const countdown = computed(() => {
  const s = segundosRestantes.value
  const mm = String(Math.floor(s / 60)).padStart(2, '0')
  const ss = String(s % 60).padStart(2, '0')
  return `${mm}:${ss}`
})

const countdownUrgente = computed(() => segundosRestantes.value <= 60)

onMounted(() => {
  const raw = route.query.expires_at
  if (!raw) return

  const deadline = new Date(raw).getTime()

  const tick = () => {
    const remaining = Math.max(0, Math.floor((deadline - Date.now()) / 1000))
    segundosRestantes.value = remaining
    if (remaining === 0) {
      expirado.value = true
      clearInterval(intervalo)
      if (esSingle.value) {
        const enrollmentId = Number(route.query.enrollment_id)
        if (enrollmentId) enrollmentService.cancelSingle(enrollmentId).catch(() => {})
      } else {
        const subscriptionId = Number(route.query.subscription_id)
        if (subscriptionId) enrollmentService.cancelSubscription(subscriptionId).catch(() => {})
      }
    }
  }

  tick()
  intervalo = setInterval(tick, 1000)
})

onUnmounted(() => clearInterval(intervalo))

const confirmarGratis = async () => {
  // Solo suscripciones pueden tener costo 0.
  const chargeId = Number(route.query.charge_id)
  if (!chargeId) return
  pagando.value = true
  try {
    await enrollmentService.freeConfirmSubscription(chargeId)
    router.push({ name: 'list' })
  } catch {
    alert('No se pudo confirmar la suscripción. Intentá de nuevo.')
  } finally {
    pagando.value = false
  }
}

const pagar = async () => {
  if (expirado.value) return

  pagando.value = true
  try {
    let data
    if (esSingle.value) {
      const enrollmentId = Number(route.query.enrollment_id)
      if (!enrollmentId) { pagando.value = false; return }
      ;({ data } = await enrollmentService.createSinglePreference(enrollmentId))
    } else {
      const chargeId = Number(route.query.charge_id)
      if (!chargeId) { pagando.value = false; return }
      ;({ data } = await enrollmentService.createSubscriptionPreference(chargeId))
    }
    window.location.href = data.init_point
  } catch {
    pagando.value = false
    alert('No se pudo iniciar el pago. Intentá de nuevo.')
  }
}

const pagarSenia = async () => {
  if (expirado.value) return
  const enrollmentId = Number(route.query.enrollment_id)
  if (!enrollmentId) return

  pagando.value = true
  try {
    const { data } = await enrollmentService.createDepositPreference(enrollmentId)
    window.location.href = data.init_point
  } catch (e) {
    pagando.value = false
    errorMsg.value = e?.response?.data?.errors?.general || 'No se pudo iniciar el pago de la seña. Intentá de nuevo.'
  }
}

const usarCredito = async () => {
  pagando.value = true
  try {
    const { data } = await enrollmentService.createSingle(
      [Number(route.query.clase_id)],
      Number(route.query.credit_id),
    )
    if (data.status === 'confirmed') {
      creditConfirmed.value = true
    } else {
      // Crédito cubre parcialmente: ir al ticket normal con el monto restante
      router.replace({
        name: 'ticket',
        query: {
          kind:          'single',
          enrollment_id: data.id,
          actividad:     route.query.actividad,
          dia:           route.query.dia,
          duracion:      route.query.duracion,
          instructor:    route.query.instructor,
          numero:        data.id,
          amount:        data.amount,
          precio_clase:  data.amount,
          expires_at:    data.expires_at,
          clase_start:   route.query.clase_start,
        },
      })
    }
  } catch (e) {
    errorMsg.value = e?.response?.data?.errors?.general || 'No se pudo aplicar el crédito. Intentá de nuevo.'
  } finally {
    pagando.value = false
  }
}

const pagarSinCredito = async () => {
  pagando.value = true
  try {
    const { data } = await enrollmentService.createSingle([Number(route.query.clase_id)])
    router.replace({
      name: 'ticket',
      query: {
        kind:          'single',
        enrollment_id: data.id,
        actividad:     route.query.actividad,
        dia:           route.query.dia,
        duracion:      route.query.duracion,
        instructor:    route.query.instructor,
        numero:        data.id,
        amount:        data.amount,
        precio_clase:  data.amount,
        expires_at:    data.expires_at,
        clase_start:   route.query.clase_start,
      },
    })
  } catch (e) {
    errorMsg.value = e?.response?.data?.errors?.general || 'No se pudo crear la inscripción. Intentá de nuevo.'
    pagando.value = false
  }
}
</script>
 
<style scoped>
.btn-mp {
  width: 100%; padding: 13px;
  border-radius: 99px; border: none;
  background: #009EE3; color: #fff;
  font-weight: 700; font-size: 14px;
  cursor: pointer; transition: all 0.2s ease;
  display: flex; align-items: center;
  justify-content: center; gap: 10px;
}
.btn-mp:hover { background: #0080C0; }
.btn-mp--senia { background: #00897B; }
.btn-mp--senia:hover { background: #00695C; }
* { box-sizing: border-box; }
.page { min-height: 100vh; background: linear-gradient(135deg, #E0F7F4 0%, #F0FAF8 50%, #E8F5E9 100%); font-family: 'Segoe UI', system-ui, sans-serif; padding-top: 60px; }
 
.main { max-width: 520px; margin: 0 auto; padding: 40px 16px 60px; display: flex; flex-direction: column; align-items: center; }
 
.success-icon {
  width: 72px; height: 72px; border-radius: 50%;
  background: linear-gradient(135deg, #00897B, #00BFA5);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 20px;
  box-shadow: 0 8px 24px rgba(0,137,123,0.3);
  animation: pop-in 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) both;
}

.success-icon svg {
  animation: draw-check 0.4s ease 0.4s both;
}

@keyframes pop-in {
  0%   { transform: scale(0); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes draw-check {
  0%   { stroke-dasharray: 30; stroke-dashoffset: 30; opacity: 0; }
  100% { stroke-dasharray: 30; stroke-dashoffset: 0;  opacity: 1; }
}
 
h1 { font-size: 24px; font-weight: 800; color: #00695C; margin: 0 0 8px; text-align: center; }
.subtitle { font-size: 15px; color: #607D8B; margin: 0 0 32px; text-align: center; }
 
.comprobante {
  width: 100%;
  background: #fff;
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  border: 1px solid #E0F2F1;
}
 
.comp-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.comp-titulo { font-size: 13px; color: #90A4AE; font-weight: 500; margin-bottom: 4px; }
.comp-numero { font-size: 18px; font-weight: 800; color: #00695C; }
.comp-fecha { font-size: 12px; color: #90A4AE; text-align: right; max-width: 130px; }
 
.divider { height: 1px; background: #F0F4F8; margin: 0 0 20px; }
 
.actividad-nombre {
  font-size: 26px; font-weight: 900;
  color: #00695C; letter-spacing: -0.5px;
  margin-bottom: 20px;
}
 
.datos-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
 
.dato { display: flex; align-items: flex-start; gap: 10px; }
.dato-label { font-size: 11px; color: #90A4AE; margin-bottom: 2px; }
.dato-valor { font-size: 14px; font-weight: 600; color: #37474F; }

.day-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 2px;
}

.day-chip {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 999px;
  background-color: rgba(0, 137, 123, 0.1);
  color: #00897b;
  letter-spacing: 0.03em;
}
 
.monto-row {
  display: flex; justify-content: space-between; align-items: center;
  background: #F0FAF8; border-radius: 10px;
  padding: 12px 16px; margin-bottom: 12px;
}
.monto-label { font-size: 13px; color: #607D8B; font-weight: 500; }
.monto-valor { font-size: 18px; font-weight: 800; color: #00695C; white-space: nowrap; flex-shrink: 0; }
.monto-valor-base { font-size: 15px; font-weight: 600; color: #37474F; white-space: nowrap; flex-shrink: 0; }
.monto-row-descuento { background: #FFF8E1; margin-bottom: 4px; }
.monto-descuento { font-size: 15px; font-weight: 700; color: #F57F17; white-space: nowrap; flex-shrink: 0; }
.monto-row-total { border-top: 1px solid #E0F2F1; padding-top: 14px; }

.aviso {
  display: flex; align-items: center; gap: 8px;
  background: #E0F2F1; border-radius: 10px;
  padding: 12px 14px; font-size: 13px;
  color: #00695C; font-weight: 500;
  margin-bottom: 8px;
}
.aviso-alerta {
  background: #FFF8E1; color: #F57F17;
}
 
.botones { display: flex; flex-direction: column; gap: 10px; width: 100%; margin-top: 24px; }
 
.btn-volver {
  width: 100%; padding: 13px;
  border-radius: 99px;
  border: 2px solid #00897B;
  background: #fff; color: #00897B;
  font-weight: 700; font-size: 14px;
  cursor: pointer; transition: all 0.2s ease;
}
.btn-volver:hover { background: #E0F2F1; }
 
.countdown {
  display: flex; align-items: center; gap: 7px;
  width: 100%; padding: 10px 14px;
  border-radius: 10px; font-size: 14px; font-weight: 500;
  background: #E0F2F1; color: #00695C;
  border: 1px solid #B2DFDB;
  margin-top: 20px; margin-bottom: 14px;
}
.countdown.urgente {
  background: #FFF3E0; color: #E65100;
  border-color: #FFCC80;
  animation: pulso 1s ease-in-out infinite;
}
.countdown.expirado {
  background: #FFEBEE; color: #C62828;
  border-color: #FFCDD2;
  animation: none;
}
@keyframes pulso {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.7; }
}

.error-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
}

.error-modal {
  background: #fff;
  border-radius: 20px;
  padding: 32px 28px 24px;
  max-width: 380px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.18);
  animation: pop-in 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275) both;
}

.error-modal-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #FFEBEE;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-modal-msg {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #37474F;
  text-align: center;
  line-height: 1.5;
}

.error-modal-btn {
  width: 100%;
  padding: 12px;
  border-radius: 999px;
  border: none;
  background: #C62828;
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.error-modal-btn:hover { background: #B71C1C; }

.credit-banner-ticket {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(237, 231, 246, 0.95), rgba(255, 255, 255, 0.9));
  border: 1.5px solid rgba(103, 58, 183, 0.3);
  margin-top: 20px;
  margin-bottom: 4px;
}

.credit-banner-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.credit-icon { font-size: 1.4rem; }

.credit-banner-info strong {
  display: block;
  color: #4527a0;
  font-size: 0.92rem;
  font-weight: 800;
}

.credit-detail {
  display: block;
  color: #5e35b1;
  font-size: 0.8rem;
  margin-top: 2px;
}

.btn-credito {
  background: #673ab7;
}
.btn-credito:hover { background: #512da8; }
</style>