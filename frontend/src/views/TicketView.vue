<template>
  <div class="page">
 
    <div class="header">
      <div class="header-inner">
        <span class="logo">SIEMPREGYM</span>
      </div>
    </div>
 
    <div class="main">
      <!-- Ícono de éxito -->
      <div class="success-icon">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      </div>
 
      <h1>¡Inscripción confirmada!</h1>
      <p class="subtitle">Tu lugar está reservado. Te esperamos.</p>
 
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
 
        <div class="actividad-nombre">{{ route.query.actividad }}</div>
 
        <div class="datos-grid">
          <div class="dato">
            <div class="dato-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00897B" stroke-width="2" stroke-linecap="round">
                <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
            </div>
            <div>
              <div class="dato-label">Días</div>
              <div class="dato-valor">{{ route.query.dia }}</div>
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
              <div class="dato-valor">{{ route.query.hora }} hs · {{ route.query.duracion }}</div>
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
 
          <div class="dato">
            <div class="dato-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00897B" stroke-width="2" stroke-linecap="round">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
            </div>
            <div>
              <div class="dato-label">Nivel</div>
              <div class="dato-valor">{{ route.query.nivel }}</div>
            </div>
          </div>
        </div>
 
        <div class="divider"></div>
 
        <div class="monto-row">
          <span class="monto-label">Total a pagar</span>
          <span class="monto-valor">$ {{ Number(route.query.amount ?? 0).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}</span>
        </div>

        <div v-if="Number(route.query.clases_excluidas) > 0" class="aviso aviso-alerta">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F57F17" stroke-width="2" stroke-linecap="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          {{ route.query.clases_excluidas }} clase{{ Number(route.query.clases_excluidas) !== 1 ? 's' : '' }} sin cupo fueron excluidas del monto.
        </div>

        <div class="aviso">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00897B" stroke-width="2" stroke-linecap="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          Presentarse 5 minutos antes del inicio de la clase.
        </div>
      </div>
 
      <!-- Contador de tiempo -->
      <div v-if="route.query.expires_at && !expirado" :class="['countdown', { urgente: countdownUrgente }]">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
        </svg>
        Tiempo para pagar: <strong>{{ countdown }}</strong>
      </div>
      <div v-else-if="expirado" class="countdown expirado">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        El tiempo para pagar expiró. Tu reserva fue liberada.
      </div>

      <!-- Botones -->
      <div class="botones">
        <button class="btn-mp" :disabled="pagando || expirado" @click="pagar">
          {{ pagando ? 'Redirigiendo...' : 'Pagar con Mercado Pago' }}
        </button>
        <button class="btn-volver" @click="router.push({ name: 'list' })">
          ← Volver a actividades
        </button>
        <button class="btn-inicio" @click="router.push({ name: 'home' })">
          Ir al inicio
        </button>
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

const pagando  = ref(false)
const expirado = ref(false)
const segundosRestantes = ref(0)
let intervalo = null

const fechaHoy = new Date().toLocaleDateString('es-AR', {
  weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
})

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
    }
  }

  tick()
  intervalo = setInterval(tick, 1000)
})

onUnmounted(() => clearInterval(intervalo))

const pagar = async () => {
  if (expirado.value) return
  const enrollmentId = Number(route.query.enrollment_id)
  if (!enrollmentId) return

  pagando.value = true
  try {
    const { data } = await enrollmentService.createPaymentPreference(enrollmentId)
    window.location.href = data.init_point
  } catch {
    pagando.value = false
    alert('No se pudo iniciar el pago. Intentá de nuevo.')
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
* { box-sizing: border-box; }
.page { min-height: 100vh; background: linear-gradient(135deg, #E0F7F4 0%, #F0FAF8 50%, #E8F5E9 100%); font-family: 'Segoe UI', system-ui, sans-serif; }
.header { background: #fff; border-bottom: 1px solid #E0F2F1; padding: 0 24px; box-shadow: 0 2px 12px rgba(0,137,123,0.08); }
.header-inner { max-width: 600px; margin: 0 auto; display: flex; align-items: center; height: 60px; }
.logo { font-size: 19px; font-weight: 900; color: #00695C; letter-spacing: 0.08em; }
 
.main { max-width: 520px; margin: 0 auto; padding: 40px 16px 60px; display: flex; flex-direction: column; align-items: center; }
 
.success-icon {
  width: 72px; height: 72px; border-radius: 50%;
  background: linear-gradient(135deg, #00897B, #00BFA5);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 20px;
  box-shadow: 0 8px 24px rgba(0,137,123,0.3);
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
.comp-fecha { font-size: 12px; color: #90A4AE; text-align: right; text-transform: capitalize; max-width: 130px; }
 
.divider { height: 1px; background: #F0F4F8; margin: 0 0 20px; }
 
.actividad-nombre {
  font-size: 26px; font-weight: 900;
  color: #00695C; letter-spacing: -0.5px;
  margin-bottom: 20px;
}
 
.datos-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
 
.dato { display: flex; align-items: flex-start; gap: 10px; }
.dato-icon { width: 32px; height: 32px; border-radius: 8px; background: #E0F2F1; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px; }
.dato-label { font-size: 11px; color: #90A4AE; margin-bottom: 2px; }
.dato-valor { font-size: 14px; font-weight: 600; color: #37474F; }
 
.monto-row {
  display: flex; justify-content: space-between; align-items: center;
  background: #F0FAF8; border-radius: 10px;
  padding: 12px 16px; margin-bottom: 12px;
}
.monto-label { font-size: 13px; color: #607D8B; font-weight: 500; }
.monto-valor { font-size: 18px; font-weight: 800; color: #00695C; }

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
 
.btn-inicio {
  width: 100%; padding: 13px;
  border-radius: 99px; border: none;
  background: #00897B; color: #fff;
  font-weight: 700; font-size: 14px;
  cursor: pointer; transition: all 0.2s ease;
}
.btn-inicio:hover { background: #00695C; }
.btn-mp:disabled { opacity: 0.5; cursor: not-allowed; }

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
</style>