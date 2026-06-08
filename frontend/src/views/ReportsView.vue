<template>
  <div class="reportes-page">
 
    <!-- Topbar -->
    <div class="topbar">
      <div class="topbar-left centered-header">
        <h1>Reportes</h1>
        <p>Análisis y métricas del centro</p>
      </div>
      <div class="export-wrapper" ref="exportWrapperRef">
        <button class="btn-export" @click="toggleMenu">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Exportar reporte
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </button>
        <div class="export-menu" :class="{ open: menuOpen }">
          <button class="export-opt" @click="doExport('csv')">
            <span class="opt-badge csv">CSV</span>
            <div><p>Descargar CSV</p><span>Compatible con Excel</span></div>
          </button>
          <div class="export-divider"></div>
          <button class="export-opt" @click="doExport('json')">
            <span class="opt-badge json">JSON</span>
            <div><p>Descargar JSON</p><span>Para integraciones</span></div>
          </button>
        </div>
      </div>
    </div>
 
    <!-- Tarjetas -->
    <div class="report-cards">
      <div
        v-for="(report, idx) in reports"
        :key="idx"
        class="report-card"
        :class="{ selected: currentIndex === idx }"
        @click="selectReport(idx)"
      >
        <div class="report-card-icon" :style="{ background: report.iconBg }">
          <span>{{ report.emoji }}</span>
        </div>
        <div class="report-card-body">
          <p>{{ report.title }}</p>
          <span>{{ report.subtitle }}</span>
        </div>
        <div v-if="currentIndex === idx" class="card-check">✓</div>
      </div>
    </div>
 
    <!-- Panel del gráfico -->
    <div class="chart-panel">
      <div class="panel-header">
        <div>
          <h2>{{ current.title }}</h2>
          <p class="chart-meta">{{ current.meta }}</p>
        </div>
        <div class="chip-group">
          <button
            v-for="(chip, i) in current.chips"
            :key="i"
            class="chip"
            :class="{ active: activeChip === i }"
            @click="activeChip = i"
          >{{ chip }}</button>
        </div>
      </div>
 
      <div class="metrics-row">
        <div v-for="(m, i) in current.metrics" :key="i" class="metric">
          <span class="metric-label">{{ m.label }}</span>
          <strong class="metric-value">{{ m.value }}</strong>
          <span class="delta" :class="m.up ? 'up' : 'down'">
            {{ m.up ? '↑' : '↓' }} {{ m.delta }}
          </span>
        </div>
      </div>
 
      <!-- SVG Chart -->
      <div class="svg-chart-wrapper">
        <svg :viewBox="`0 0 ${svgW} ${svgH}`" width="100%" :height="svgH">
          <defs>
            <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stop-color="#11998e" stop-opacity="0.35"/>
              <stop offset="100%" stop-color="#11998e" stop-opacity="0.04"/>
            </linearGradient>
          </defs>
 
          <!-- Líneas guía -->
          <line
            v-for="(guide, i) in guides" :key="'g'+i"
            :x1="paddingLeft" :y1="guide.y"
            :x2="svgW - paddingRight" :y2="guide.y"
            stroke="#e5e9e8" stroke-width="1"
          />
          <!-- Etiquetas Y -->
          <text
            v-for="(guide, i) in guides" :key="'yl'+i"
            :x="paddingLeft - 8" :y="guide.y + 4"
            text-anchor="end" font-size="10" fill="#8fa8a2"
            font-family="system-ui, sans-serif"
          >{{ guide.label }}</text>
 
          <!-- Barras -->
          <g v-for="(bar, i) in bars" :key="'b'+i">
            <rect :x="bar.x" :y="bar.y" :width="bar.w" :height="bar.h"
              fill="url(#barGrad)" rx="5" />
            <rect :x="bar.x" :y="bar.y" :width="bar.w" :height="Math.min(bar.h, 4)"
              fill="#11998e" rx="5" />
            <text :x="bar.x + bar.w/2" :y="bar.y - 6"
              text-anchor="middle" font-size="10" font-weight="600"
              fill="#0d3027" font-family="system-ui, sans-serif"
            >{{ bar.label }}</text>
            <text :x="bar.x + bar.w/2" :y="svgH - paddingBottom + 16"
              text-anchor="middle" font-size="10" fill="#8fa8a2"
              font-family="system-ui, sans-serif"
            >{{ bar.name }}</text>
          </g>
 
          <!-- Línea base -->
          <line
            :x1="paddingLeft" :y1="svgH - paddingBottom"
            :x2="svgW - paddingRight" :y2="svgH - paddingBottom"
            stroke="#d1dadd" stroke-width="1.5"
          />
        </svg>
      </div>
    </div>
 
    <!-- Toast -->
    <transition name="toast">
      <div v-if="toastVisible" class="toast">
        <span class="toast-icon">✓</span>
        {{ toastMsg }}
      </div>
    </transition>
    <button class="btn-volver" @click="volver">
      ← Volver
    </button>  
  </div>
</template>
 
<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
function volver() {
    router.back()
}
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
 
const reports = [
  {
    title: 'Ingresos mensual',
    subtitle: 'Facturación y cobros por mes',
    emoji: '💰',
    iconBg: 'rgba(17,153,142,0.12)',
    color: '#11998e',
    chips: ['2025', '2024'],
    meta: 'Período: enero – mayo 2025 · Actualizado hoy',
    metrics: [
      { label: 'Total acumulado',  value: '$842.500', delta: '+12% vs año anterior', up: true  },
      { label: 'Promedio mensual', value: '$168.500', delta: '+8% vs año anterior',  up: true  },
      { label: 'Mejor mes',        value: 'Marzo',    delta: '$201.200',             up: true  },
    ],
    labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May'],
    data:   [142000, 168000, 201200, 175400, 155900],
    csvHeaders: ['Mes', 'Ingresos (ARS)'],
    filename: 'ingresos_mensual_2025',
  },
  {
    title: 'Ocupación por turno',
    subtitle: '% de clases llenas por franja',
    emoji: '👥',
    iconBg: 'rgba(17,153,142,0.12)',
    color: '#11998e',
    chips: ['Esta semana', 'Mes actual'],
    meta: 'Semana actual · Promedio de lunes a viernes',
    metrics: [
      { label: 'Turno más ocupado',        value: '8–10h', delta: '94% de ocupación',       up: true  },
      { label: 'Ocupación promedio',        value: '71%',   delta: '+5 pp vs sem. anterior', up: true  },
      { label: 'Clases con baja ocupación', value: '3',     delta: '< 50% de capacidad',     up: false },
    ],
    labels: ['7–8h', '8–10h', '10–12h', '12–14h', '16–18h', '18–20h', '20–22h'],
    data:   [58, 94, 82, 47, 69, 88, 75],
    csvHeaders: ['Turno', 'Ocupación (%)'],
    filename: 'ocupacion_por_turno',
  },
  {
    title: 'Ausencias por clase',
    subtitle: 'Clientes que no asistieron',
    emoji: '🔕',
    iconBg: 'rgba(17,153,142,0.12)',
    color: '#11998e',
    chips: ['4 semanas', '8 semanas'],
    meta: 'Últimas 4 semanas · Top clases con mayor ausentismo',
    metrics: [
      { label: 'Total ausencias',    value: '124',  delta: '-9% vs período anterior', up: true  },
      { label: 'Tasa de ausentismo', value: '18%',  delta: 'Meta: < 15%',             up: false },
      { label: 'Clase más afectada', value: 'Yoga', delta: '31 ausencias',            up: false },
    ],
    labels: ['Yoga', 'Spinning', 'Pilates', 'Funcional', 'Zumba', 'CrossFit'],
    data:   [31, 24, 22, 18, 16, 13],
    csvHeaders: ['Clase', 'Ausencias'],
    filename: 'ausencias_por_clase',
  },
  {
    title: 'Cancelaciones por clase',
    subtitle: 'Bajas y cancelaciones de inscripción',
    emoji: '❌',
    iconBg: 'rgba(17,153,142,0.12)',
    color: '#11998e',
    chips: ['Este mes', 'Últimos 3 meses'],
    meta: 'Último mes · Bajas formales de inscripción',
    metrics: [
      { label: 'Total cancelaciones', value: '47',       delta: '+3 vs mes anterior', up: false },
      { label: 'Tasa de cancelación', value: '6,2%',     delta: 'Meta: < 5%',         up: false },
      { label: 'Clase con más bajas', value: 'Spinning', delta: '12 cancelaciones',   up: false },
    ],
    labels: ['Spinning', 'Yoga', 'CrossFit', 'Pilates', 'Zumba', 'Funcional'],
    data:   [12, 9, 8, 7, 6, 5],
    csvHeaders: ['Clase', 'Cancelaciones'],
    filename: 'cancelaciones_por_clase',
  },
]
 
const currentIndex     = ref(0)
const activeChip       = ref(0)
const menuOpen         = ref(false)
const toastVisible     = ref(false)
const toastMsg         = ref('')
const exportWrapperRef = ref<HTMLElement | null>(null)
 
const current = computed(() => reports[currentIndex.value])
 
function selectReport(idx: number) {
  currentIndex.value = idx
  activeChip.value   = 0
}
 
const svgW = 640, svgH = 230, paddingLeft = 44, paddingRight = 16, paddingTop = 28, paddingBottom = 30
 
const guides = computed(() => {
  const max  = Math.max(...current.value.data)
  const step = Math.ceil(max / 4)
  return Array.from({ length: 5 }, (_, i) => {
    const val = step * i
    const y   = svgH - paddingBottom - (val / (step * 4)) * (svgH - paddingTop - paddingBottom)
    return { y, label: val >= 1000 ? `${Math.round(val / 1000)}k` : String(val) }
  })
})
 
const bars = computed(() => {
  const { data, labels } = current.value
  const max    = Math.max(...data)
  const chartW = svgW - paddingLeft - paddingRight
  const chartH = svgH - paddingTop - paddingBottom
  const slotW  = chartW / data.length
  const barW   = Math.min(52, slotW * 0.55)
  return data.map((val, i) => {
    const h     = (val / max) * chartH
    const x     = paddingLeft + slotW * i + (slotW - barW) / 2
    const y     = svgH - paddingBottom - h
    const label = val >= 1000 ? `${Math.round(val / 1000)}k` : String(val)
    return { x, y, w: barW, h, name: labels[i], label }
  })
})
 
function toggleMenu() { menuOpen.value = !menuOpen.value }
 
function onDocClick(e: MouseEvent) {
  if (!exportWrapperRef.value?.contains(e.target as Node)) menuOpen.value = false
}
onMounted(()       => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
 
function doExport(fmt: 'csv' | 'json') {
  menuOpen.value = false
  const r = current.value
  let content: string, mime: string, ext: string
  if (fmt === 'csv') {
    content = [r.csvHeaders.join(','), ...r.labels.map((l, i) => `${l},${r.data[i]}`)].join('\n')
    mime = 'text/csv'; ext = 'csv'
  } else {
    const obj = r.labels.map((l, i) => ({ [r.csvHeaders[0]]: l, [r.csvHeaders[1]]: r.data[i] }))
    content = JSON.stringify({ reporte: r.title, generado: new Date().toISOString(), datos: obj }, null, 2)
    mime = 'application/json'; ext = 'json'
  }
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(new Blob([content], { type: mime })),
    download: `${r.filename}.${ext}`
  })
  a.click()
  setTimeout(() => {
  URL.revokeObjectURL(a.href)
}, 100)
  showToast(`${r.filename}.${ext} descargado`)
}
 
function showToast(msg: string) {
  toastMsg.value = msg; toastVisible.value = true
  setTimeout(() => { toastVisible.value = false }, 3000)
}
</script>
 
<style scoped>

/* ── Topbar ── */
.topbar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: stretch;
}
.topbar-left h1 {
  font-size: 22px;
  font-weight: 700;
  color: #0d3027;
  margin: 0;
  letter-spacing: -0.3px;
}
.topbar-left p {
  font-size: 13px;
  color: #8fa8a2;
  margin: 3px 0 0;
}
 
/* ── Botón exportar ── */
.export-wrapper {
  position: relative;
  align-self: flex-end;
}
 
.btn-export {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 18px;
  background: #11998e;
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
}
.btn-export:hover  { background: #0d3027; }
.btn-export:active { transform: scale(0.98); }
 
.export-menu {
  display: none;
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: #fff;
  border: 1px solid #e5e9e8;
  border-radius: 12px;
  min-width: 210px;
  z-index: 50;
  box-shadow: 0 8px 28px rgba(13,48,39,0.12);
  overflow: hidden;
  padding: 6px;
}
.export-menu.open { display: block; }
.export-divider   { height: 1px; background: #f0f4f3; margin: 2px 0; }
 
.export-opt {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  cursor: pointer;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  border-radius: 8px;
  transition: background 0.12s;
}
.export-opt:hover { background: #f0f7f6; }
.export-opt p     { margin: 0; font-weight: 600; font-size: 13px; color: #0d3027; }
.export-opt span  { font-size: 11px; color: #8fa8a2; margin-top: 1px; display: block; }
 
.opt-badge {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.3px;
  flex-shrink: 0;
}
.opt-badge.csv  { background: rgba(17,153,142,0.12); color: #0d3027; }
.opt-badge.json { background: rgba(13,48,39,0.08);   color: #0d3027; }
 
/* ── Tarjetas ── */
.report-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.report-card {
  background: #fff;
  border: 1.5px solid #e5e9e8;
  border-radius: 14px;
  padding: 15px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 13px;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.12s;
  position: relative;
}
.report-card:hover {
  border-color: #8fa8a2;
  box-shadow: 0 2px 12px rgba(13,48,39,0.08);
  transform: translateY(-1px);
}
.report-card.selected {
  border-color: #11998e;
  border-width: 2px;
  background: linear-gradient(135deg, #f0f9f7 0%, #fff 100%);
  box-shadow: 0 4px 16px rgba(17,153,142,0.14);
}
 
.report-card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.report-card-body { flex: 1; min-width: 0; }
.report-card-body p {
  font-size: 13px;
  font-weight: 600;
  color: #0d3027;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.report-card-body span {
  font-size: 11px;
  color: #8fa8a2;
  margin-top: 3px;
  display: block;
}
.card-check {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #11998e;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
 
/* ── Panel gráfico ── */
.chart-panel {
  background: #fff;
  border: 1.5px solid #e5e9e8;
  border-radius: 16px;
  padding: 20px 22px 14px;
  box-shadow: 0 2px 16px rgba(13,48,39,0.05);
}
.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 18px;
}
.panel-header h2 {
  font-size: 15px;
  font-weight: 700;
  color: #0d3027;
  margin: 0 0 4px;
  letter-spacing: -0.2px;
}
.chart-meta { font-size: 11px; color: #8fa8a2; margin: 0; }
 
.chip-group { display: flex; gap: 6px; }
.chip {
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
  border: 1.5px solid #d1dadd;
  cursor: pointer;
  color: #8fa8a2;
  background: #f6faf9;
  transition: all 0.15s;
}
.chip:hover  { border-color: #11998e; color: #0d3027; }
.chip.active { background: #11998e; color: #fff; border-color: #11998e; }
 
/* ── Métricas ── */
.metrics-row { display: flex; gap: 10px; margin-bottom: 18px; }
.metric {
  flex: 1;
  background: #f6faf9;
  border: 1px solid #e5e9e8;
  border-top: 3px solid #11998e;
  border-radius: 10px;
  padding: 12px 14px;
  transition: box-shadow 0.15s;
}
.metric:hover { box-shadow: 0 2px 10px rgba(17,153,142,0.10); }
.metric-label {
  font-size: 10px;
  color: #8fa8a2;
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #0d3027;
  display: block;
  letter-spacing: -0.5px;
}
.delta {
  font-size: 11px;
  margin-top: 4px;
  display: block;
  font-weight: 500;
}
.delta.up   { color: #11998e; }
.delta.down { color: #c0392b; }
 
/* ── SVG ── */
.svg-chart-wrapper { width: 100%; overflow-x: auto; }
 
/* ── Toast ── */
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: #0d3027;
  color: #d1dadd;
  padding: 12px 18px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  z-index: 999;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 20px rgba(13,48,39,0.25);
}
.toast-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #11998e;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  flex-shrink: 0;
}
.toast-enter-active, .toast-leave-active { transition: opacity 0.25s, transform 0.25s; }
.toast-enter-from,   .toast-leave-to     { opacity: 0; transform: translateY(8px); }
/* ── Header centrado ── */
.centered-header {
  width: 100%;
  text-align: center;
  background: linear-gradient(135deg, #11998e 0%, #0d3027 100%);
  padding: 22px 20px;
  border-radius: 18px;
  box-shadow: 0 4px 18px rgba(17,153,142,0.18);
}

.centered-header h1 {
  color: white;
  margin: 0;
  font-size: 28px;
  font-weight: 700;
}

.centered-header p {
  color: rgba(255,255,255,0.82);
  margin-top: 6px;
  font-size: 14px;
}

/* Topbar */

/* Botón volver */
.btn-volver {
  position: fixed;
  bottom: 24px;
  left: 24px;

  background: #0d3027;
  color: white;

  border: none;
  border-radius: 12px;

  padding: 12px 18px;

  font-size: 14px;
  font-weight: 600;

  cursor: pointer;

  box-shadow: 0 4px 14px rgba(13,48,39,0.25);

  transition: 0.15s;
}

.btn-volver:hover {
  background: #11998e;
  transform: translateY(-2px);
}
.reportes-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: #f4f8f7;
  min-height: 100vh;
  padding: 20px;
}
</style>