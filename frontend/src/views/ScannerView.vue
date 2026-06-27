<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import jsQR from 'jsqr'
import api from '@/services/api'
import AdminLayout from '@/components/layout/AdminLayout.vue'

interface CheckinResult {
  ok: boolean
  first_name: string
  last_name: string
  activity_name: string
  horario: string
}

type ScannerState = 'idle' | 'scanning' | 'processing' | 'success' | 'error'

const state = ref<ScannerState>('idle')
const errorMsg = ref('')
const lastResult = ref<CheckinResult | null>(null)

const videoEl = ref<HTMLVideoElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)
let stream: MediaStream | null = null
let rafId: number | null = null
let lastScannedPayload = ''
let cooldownUntil = 0

const startCamera = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' },
    })
    if (!videoEl.value) return
    videoEl.value.srcObject = stream
    await videoEl.value.play()
    state.value = 'scanning'
    lastScannedPayload = ''
    scanLoop()
  } catch {
    state.value = 'error'
    errorMsg.value = 'No se pudo acceder a la cámara. Verificá los permisos del navegador.'
  }
}

const stopScanLoop = () => {
  if (rafId !== null) cancelAnimationFrame(rafId)
  rafId = null
}

const stopCamera = () => {
  stopScanLoop()
  stream?.getTracks().forEach((t) => t.stop())
  stream = null
}

const scanLoop = () => {
  if (!videoEl.value || !canvasEl.value) return
  const video = videoEl.value
  if (video.readyState !== video.HAVE_ENOUGH_DATA) {
    rafId = requestAnimationFrame(scanLoop)
    return
  }
  const canvas = canvasEl.value
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
  const code = jsQR(imageData.data, imageData.width, imageData.height)
  if (code && code.data) {
    const now = Date.now()
    if (code.data !== lastScannedPayload || now > cooldownUntil) {
      lastScannedPayload = code.data
      cooldownUntil = now + 3000
      handleQRData(code.data)
      return
    }
  }
  rafId = requestAnimationFrame(scanLoop)
}

const handleQRData = async (raw: string) => {
  let payload: { u: number; c: number }
  try {
    payload = JSON.parse(raw)
    if (typeof payload.u !== 'number' || typeof payload.c !== 'number') throw new Error()
  } catch {
    rafId = requestAnimationFrame(scanLoop)
    return
  }

  stopScanLoop()
  stream?.getTracks().forEach((t) => t.stop())
  stream = null
  state.value = 'processing'

  try {
    const res = await api.post('/attendances/checkin', {
      user_id: payload.u,
      clase_id: payload.c,
    })
    lastResult.value = res.data as CheckinResult
    state.value = 'success'
  } catch (err: any) {
    state.value = 'error'
    errorMsg.value =
      err?.response?.data?.detail ?? 'No se pudo registrar la asistencia.'
  }
}

const reset = () => {
  lastResult.value = null
  errorMsg.value = ''
  state.value = 'idle'
  lastScannedPayload = ''
}

onUnmounted(stopCamera)
</script>

<template>
  <AdminLayout>
  <div class="scanner-page">

    <div class="scanner-header">
      <h1 class="scanner-title">Escáner QR</h1>
      <p class="scanner-sub">Registrá la asistencia escaneando el código QR del alumno</p>
    </div>

    <div class="scanner-body">

      <!-- Idle -->
      <div v-if="state === 'idle'" class="idle-card">
        <div class="idle-icon-wrap">
          <svg viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <path d="M14 14h2v2h-2zM18 14h3M14 18h1M17 18h4M14 21h3M20 18v3"/>
          </svg>
        </div>
        <div class="idle-text">
          <h2 class="idle-title">Listo para escanear</h2>
          <p class="idle-sub">Activá la cámara y apuntá al código QR que muestra el alumno desde su teléfono.</p>
        </div>
        <div class="idle-steps">
          <div class="step">
            <span class="step-num">1</span>
            <span class="step-label">El alumno abre su QR en la app</span>
          </div>
          <div class="step">
            <span class="step-num">2</span>
            <span class="step-label">Activás la cámara con el botón de abajo</span>
          </div>
          <div class="step">
            <span class="step-num">3</span>
            <span class="step-label">Apuntás al código — la asistencia se registra sola</span>
          </div>
        </div>
        <button type="button" class="btn-primary" @click="startCamera">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0">
            <path d="M23 7 16 12 23 17V7z"/>
            <rect x="1" y="5" width="15" height="14" rx="2"/>
          </svg>
          Activar cámara
        </button>
      </div>

      <!-- Cámara: v-show para que <video> siempre esté en el DOM y el ref sea válido -->
      <div v-show="state === 'scanning' || state === 'processing'" class="camera-card">
        <div class="camera-card-header">
          <span class="status-dot" :class="state === 'processing' ? 'dot-green' : 'dot-pulse'"></span>
          <span class="status-label">{{ state === 'processing' ? 'QR detectado — registrando…' : 'Cámara activa — buscando QR…' }}</span>
        </div>

        <div class="scanner-frame" :class="{ 'frame-detected': state === 'processing' }">
          <video ref="videoEl" class="scanner-video" muted playsinline></video>
          <canvas ref="canvasEl" class="scanner-canvas"></canvas>

          <div v-if="state === 'scanning'" class="scanner-overlay">
            <div class="scan-corner tl"></div>
            <div class="scan-corner tr"></div>
            <div class="scan-corner bl"></div>
            <div class="scan-corner br"></div>
            <div class="scan-line"></div>
          </div>

          <div v-else class="detected-overlay">
            <div class="detected-check">&#x2713;</div>
            <p class="detected-label">QR leído</p>
            <div class="spinner-white"></div>
          </div>
        </div>

        <div class="camera-card-footer">
          <p class="scan-hint">Mantené el código centrado y bien iluminado</p>
          <button
            v-if="state === 'scanning'"
            type="button"
            class="btn-secondary"
            @click="() => { stopCamera(); reset() }"
          >
            Cancelar
          </button>
        </div>
      </div>

      <!-- Success -->
      <div v-if="state === 'success' && lastResult" class="result-card success-card">
        <div class="result-icon-wrap success-wrap">
          <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </div>
        <span class="badge-presente">PRESENTE</span>
        <p class="result-name">{{ lastResult?.first_name }} {{ lastResult?.last_name }}</p>
        <div class="result-meta">
          <span class="meta-pill">{{ lastResult?.activity_name }}</span>
          <span class="meta-pill">{{ lastResult?.horario }}</span>
        </div>
        <button type="button" class="btn-primary" @click="() => { reset(); startCamera() }">
          Escanear otro
        </button>
      </div>

      <!-- Error -->
      <div v-if="state === 'error'" class="result-card error-card">
        <div class="result-icon-wrap error-wrap">
          <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </div>
        <p class="result-error-title">No se pudo registrar</p>
        <p class="result-error-msg">{{ errorMsg }}</p>
        <button type="button" class="btn-primary" @click="() => { reset(); startCamera() }">
          Reintentar
        </button>
      </div>

    </div>
  </div>
  </AdminLayout>
</template>

<style scoped>
.scanner-page {
  display: flex;
  flex-direction: column;
  max-width: 560px;
}

.scanner-header {
  margin-bottom: 24px;
}
.scanner-title {
  margin: 0 0 4px;
  color: #1f2937;
  font-size: 1.6rem;
  font-weight: 800;
}
.scanner-sub {
  margin: 0;
  color: #6b7280;
  font-size: 0.95rem;
}

/* ── Idle ── */
.idle-card {
  background: white;
  border-radius: 20px;
  padding: 32px 28px;
  box-shadow: 0 4px 18px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.idle-icon-wrap {
  width: 72px;
  height: 72px;
  border-radius: 20px;
  background: rgba(13,155,138,0.1);
  color: #0d9b8a;
  display: flex;
  align-items: center;
  justify-content: center;
}

.idle-text {}
.idle-title { margin: 0 0 6px; font-size: 1.2rem; font-weight: 700; color: #1f2937; }
.idle-sub { margin: 0; font-size: 0.9rem; color: #6b7280; line-height: 1.5; }

.idle-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f9fafb;
  border-radius: 14px;
  padding: 16px 18px;
}
.step {
  display: flex;
  align-items: center;
  gap: 12px;
}
.step-num {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #0d9b8a;
  color: white;
  font-size: 0.78rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.step-label {
  font-size: 0.88rem;
  color: #374151;
  line-height: 1.4;
}

/* ── Camera card ── */
.camera-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 4px 18px rgba(0,0,0,0.06);
  overflow: hidden;
}

.camera-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  border-bottom: 1px solid #f3f4f6;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-pulse {
  background: #0d9b8a;
  animation: pulse-dot 1.4s ease-in-out infinite;
}
.dot-green {
  background: #4caf50;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(0.8); }
}

.status-label {
  font-size: 0.88rem;
  font-weight: 600;
  color: #374151;
}

.scanner-frame {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  background: black;
  border-top: none;
  border-bottom: none;
  transition: box-shadow 0.2s;
}

.scanner-frame.frame-detected {
  box-shadow: inset 0 0 0 4px #4caf50;
}

.scanner-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.scanner-canvas {
  display: none;
}

.camera-card-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
}

.scan-hint {
  margin: 0;
  font-size: 0.85rem;
  color: #6b7280;
  font-weight: 500;
}

/* ── Scan overlay ── */
.scanner-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.scan-corner {
  position: absolute;
  width: 32px;
  height: 32px;
  border-color: #0d9b8a;
  border-style: solid;
}
.tl { top: 20px; left: 20px; border-width: 4px 0 0 4px; border-radius: 4px 0 0 0; }
.tr { top: 20px; right: 20px; border-width: 4px 4px 0 0; border-radius: 0 4px 0 0; }
.bl { bottom: 20px; left: 20px; border-width: 0 0 4px 4px; border-radius: 0 0 0 4px; }
.br { bottom: 20px; right: 20px; border-width: 0 4px 4px 0; border-radius: 0 0 4px 0; }

@keyframes scan-move {
  0%   { top: 24px; }
  50%  { top: calc(100% - 28px); }
  100% { top: 24px; }
}
.scan-line {
  position: absolute;
  left: 24px;
  right: 24px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #0d9b8a, transparent);
  animation: scan-move 2s ease-in-out infinite;
}

/* ── Overlay detectado ── */
.detected-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
}
.detected-check {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #4caf50;
  color: white;
  font-size: 2rem;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 24px rgba(76, 175, 80, 0.6);
}
.detected-label {
  margin: 0;
  color: white;
  font-size: 1.1rem;
  font-weight: 800;
}

@keyframes spin { to { transform: rotate(360deg); } }
.spinner-white {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ── Result cards ── */
.result-card {
  background: white;
  border-radius: 20px;
  padding: 36px 28px;
  box-shadow: 0 4px 18px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  text-align: center;
}

.result-icon-wrap {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.success-wrap { background: #e8f5e9; color: #2e7d32; }
.error-wrap   { background: #ffebee; color: #c62828; }

.success-card { border-top: 4px solid #4caf50; }
.error-card   { border-top: 4px solid #ef5350; }

.badge-presente {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
  font-size: 0.72rem;
  font-weight: 800;
  padding: 4px 14px;
  border-radius: 20px;
  letter-spacing: 0.8px;
}

.result-name {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 800;
  color: #1f2937;
}

.result-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}
.meta-pill {
  background: #f3f4f6;
  color: #374151;
  font-size: 0.82rem;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 20px;
}

.result-error-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: #1f2937;
}
.result-error-msg {
  margin: 0;
  font-size: 0.9rem;
  color: #6b7280;
  line-height: 1.5;
}

/* ── Botones ── */
.btn-primary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #0d9b8a;
  color: white;
  border: none;
  border-radius: 999px;
  padding: 12px 28px;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s;
  width: 100%;
}
.btn-primary:hover { background: #0b8577; }

.btn-secondary {
  background: white;
  color: #374151;
  border: 2px solid #d1d5db;
  border-radius: 999px;
  padding: 10px 24px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.btn-secondary:hover { background: #f3f4f6; border-color: #9ca3af; }
</style>
