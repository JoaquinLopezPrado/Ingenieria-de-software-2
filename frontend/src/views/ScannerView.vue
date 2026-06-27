<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import jsQR from 'jsqr'
import api from '@/services/api'

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

  // Detener solo el loop de scan; el video sigue mostrando el último frame
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
  <div class="scanner-page">
    <div class="scanner-header">
      <h1 class="scanner-title">Escáner QR</h1>
      <p class="scanner-sub">Apuntá la cámara al QR del alumno</p>
    </div>

    <div class="scanner-body">

      <!-- Idle -->
      <div v-if="state === 'idle'" class="center-card">
        <div class="cam-icon">📷</div>
        <p class="card-title">Listo para escanear</p>
        <p class="card-sub">Presioná el botón para activar la cámara</p>
        <button type="button" class="btn-primary" @click="startCamera">
          Activar cámara
        </button>
      </div>

      <!-- Cámara (scanning + processing comparten el frame de video) -->
      <div v-else-if="state === 'scanning' || state === 'processing'" class="scanner-frame-wrapper">
        <div class="scanner-frame" :class="{ 'frame-detected': state === 'processing' }">
          <video ref="videoEl" class="scanner-video" muted playsinline></video>
          <canvas ref="canvasEl" class="scanner-canvas"></canvas>

          <!-- Overlay de escaneo activo -->
          <div v-if="state === 'scanning'" class="scanner-overlay">
            <div class="scan-corner tl"></div>
            <div class="scan-corner tr"></div>
            <div class="scan-corner bl"></div>
            <div class="scan-corner br"></div>
            <div class="scan-line"></div>
          </div>

          <!-- Overlay de QR detectado -->
          <div v-else class="detected-overlay">
            <div class="detected-check">✓</div>
            <p class="detected-label">QR leído</p>
            <div class="spinner-white"></div>
          </div>
        </div>

        <p v-if="state === 'scanning'" class="scan-hint">Enfocá el QR dentro del cuadro</p>
        <p v-else class="processing-hint">Registrando asistencia...</p>

        <button
          v-if="state === 'scanning'"
          type="button"
          class="btn-secondary"
          @click="() => { stopCamera(); reset() }"
        >
          Cancelar
        </button>
      </div>

      <!-- Success -->
      <div v-else-if="state === 'success' && lastResult" class="center-card success">
        <div class="result-check">✓</div>
        <p class="result-name">{{ lastResult.first_name }} {{ lastResult.last_name }}</p>
        <p class="result-actividad">{{ lastResult.activity_name }}</p>
        <p class="result-horario">{{ lastResult.horario }}</p>
        <span class="badge-presente">PRESENTE</span>
        <button type="button" class="btn-primary" @click="() => { reset(); startCamera() }">
          Escanear otro
        </button>
      </div>

      <!-- Error -->
      <div v-else-if="state === 'error'" class="center-card error">
        <div class="error-icon">✕</div>
        <p class="card-title">Error</p>
        <p class="card-sub">{{ errorMsg }}</p>
        <button type="button" class="btn-primary" @click="() => { reset(); startCamera() }">
          Reintentar
        </button>
      </div>

    </div>
  </div>
</template>

<style scoped>
.scanner-page {
  min-height: 100vh;
  background: #0d3027;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px 60px;
}

.scanner-header {
  text-align: center;
  margin-bottom: 32px;
}
.scanner-title {
  margin: 0 0 6px;
  color: white;
  font-size: 1.8rem;
  font-weight: 800;
}
.scanner-sub {
  margin: 0;
  color: #8fa8a2;
  font-size: 0.95rem;
}

.scanner-body {
  width: 100%;
  max-width: 480px;
}

.center-card {
  background: white;
  border-radius: 24px;
  padding: 40px 28px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.cam-icon { font-size: 3rem; }
.card-title { margin: 0; font-size: 1.2rem; font-weight: 700; color: #1f2937; }
.card-sub { margin: 0; font-size: 0.9rem; color: #6b7280; }

/* ── Frame de cámara ── */
.scanner-frame-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.scanner-frame {
  position: relative;
  width: 100%;
  max-width: 360px;
  aspect-ratio: 1;
  background: black;
  border-radius: 20px;
  overflow: hidden;
  border: 3px solid transparent;
  transition: border-color 0.2s;
}

.scanner-frame.frame-detected {
  border-color: #4caf50;
  box-shadow: 0 0 0 4px rgba(76, 175, 80, 0.25);
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

/* ── Overlay de escaneo ── */
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

/* ── Overlay de QR detectado ── */
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
  letter-spacing: 0.3px;
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

.scan-hint { color: #c8dbd8; font-size: 0.85rem; font-weight: 600; }
.processing-hint { color: #a5d6a7; font-size: 0.85rem; font-weight: 700; }

/* ── Success ── */
.center-card.success { border: 3px solid #c8e6c9; }
.result-check {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #e8f5e9;
  color: #2e7d32;
  font-size: 2rem;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}
.result-name { margin: 4px 0 0; font-size: 1.3rem; font-weight: 800; color: #1f2937; }
.result-actividad { margin: 0; font-size: 1rem; font-weight: 600; color: #374151; }
.result-horario { margin: 0 0 4px; font-size: 0.9rem; color: #6b7280; }
.badge-presente {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
  font-size: 0.75rem;
  font-weight: 800;
  padding: 3px 14px;
  border-radius: 20px;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

/* ── Error ── */
.center-card.error { border: 3px solid #ffcdd2; }
.error-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #ffebee;
  color: #c62828;
  font-size: 1.8rem;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ── Botones ── */
.btn-primary {
  background: #0d9b8a;
  color: white;
  border: none;
  border-radius: 999px;
  padding: 12px 28px;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  margin-top: 4px;
  transition: background 0.15s;
}
.btn-primary:hover { background: #0b8577; }

.btn-secondary {
  background: rgba(255,255,255,0.15);
  color: white;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 999px;
  padding: 10px 24px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-secondary:hover { background: rgba(255,255,255,0.22); }
</style>
