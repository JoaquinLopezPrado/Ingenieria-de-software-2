<template>
  <div class="page">

    <div class="main">
      <div class="icon pending-icon">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
        </svg>
      </div>

      <h1>Pago en revisión</h1>
      <p class="subtitle">Tu pago está siendo procesado. Te avisaremos cuando se confirme.</p>

      <div class="card">
        <div class="card-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F57F17" stroke-width="2" stroke-linecap="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <div>
          <div class="card-label">Estado de tu inscripción</div>
          <div class="card-value">Pendiente de confirmación</div>
        </div>
      </div>

      <div class="botones">
        <button class="btn-primary" @click="router.push({ name: 'list' })">
          Ver actividades
        </button>
        <button class="btn-secondary" @click="router.push({ name: 'home' })">
          Ir al inicio
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped>
* { box-sizing: border-box; }
.page { min-height: 100vh; background: linear-gradient(135deg, #FFFDE7 0%, #FFFFF0 50%, #FFF8E1 100%); font-family: 'Segoe UI', system-ui, sans-serif; padding-top: 60px; }
.header { background: #fff; border-bottom: 1px solid #FFF9C4; padding: 0 24px; box-shadow: 0 2px 12px rgba(245,127,23,0.06); }
.header-inner { max-width: 600px; margin: 0 auto; display: flex; align-items: center; height: 60px; }
.logo { font-size: 19px; font-weight: 900; color: #00695C; letter-spacing: 0.08em; }
.main { max-width: 480px; margin: 0 auto; padding: 60px 16px; display: flex; flex-direction: column; align-items: center; }
.icon { width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 24px; }
.pending-icon { background: linear-gradient(135deg, #F9A825, #FFB300); box-shadow: 0 8px 24px rgba(249,168,37,0.3); }
h1 { font-size: 26px; font-weight: 800; color: #E65100; margin: 0 0 8px; text-align: center; }
.subtitle { font-size: 15px; color: #607D8B; margin: 0 0 32px; text-align: center; }
.card { width: 100%; background: #fff; border-radius: 16px; padding: 20px 24px; display: flex; align-items: center; gap: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.07); border: 1px solid #FFE082; margin-bottom: 32px; }
.card-icon { width: 44px; height: 44px; border-radius: 12px; background: #FFF8E1; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.card-label { font-size: 12px; color: #90A4AE; margin-bottom: 4px; }
.card-value { font-size: 15px; font-weight: 700; color: #E65100; }
.botones { display: flex; flex-direction: column; gap: 10px; width: 100%; }
.btn-primary { width: 100%; padding: 14px; border-radius: 99px; border: none; background: #00897B; color: #fff; font-weight: 700; font-size: 14px; cursor: pointer; transition: background 0.2s; }
.btn-primary:hover { background: #00695C; }
.btn-secondary { width: 100%; padding: 14px; border-radius: 99px; border: 2px solid #00897B; background: #fff; color: #00897B; font-weight: 700; font-size: 14px; cursor: pointer; transition: background 0.2s; }
.btn-secondary:hover { background: #E0F2F1; }
</style>
