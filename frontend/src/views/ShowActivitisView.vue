<template>
  <div class="page">
 
    <!-- Header -->
    <div class="header">
      <div class="header-inner">
        <span class="logo">SIEMPREGYM</span>
        <div class="account">
          <div class="avatar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00897B" stroke-width="2" stroke-linecap="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <span class="account-label">Mi cuenta</span>
        </div>
      </div>
    </div>
 
    <!-- Main -->
    <div class="main">
      <h1>Actividades disponibles</h1>
      <p class="subtitle">Elegí tu actividad y reservá tu lugar en el turno que más te convenga.</p>
 
      <!-- Tabs -->
      <div class="tab-bar">
        <button
          v-for="tab in tabs"
          :key="tab"
          class="tab-btn"
          :class="{ active: currentTab === tab }"
          @click="currentTab = tab"
        >
          <span v-html="tabIcons[tab]" class="tab-icon"></span>
          {{ tab }}
        </button>
      </div>
 
      <!-- Badges -->
      <div class="badges">
        <div class="badge">
          <span class="badge-num" style="color: #00897B">{{ disponibles }}</span>
          <span class="badge-label">Turnos disponibles</span>
        </div>
        <div class="badge">
          <span class="badge-num" style="color: #E53935">{{ completos }}</span>
          <span class="badge-label">Turnos completos</span>
        </div>
      </div>
 
      <!-- Grid -->
      <div class="grid">
        <div
          v-for="turno in currentTurnos"
          :key="turno.id"
          class="card"
          :class="{ reserved: reservados.has(turno.id) }"
        >
          <div v-if="reservados.has(turno.id)" class="reserved-badge">RESERVADO ✓</div>
 
          <div class="card-top">
            <div>
              <div class="hora-row">
                <span class="hora">{{ turno.hora }}</span>
                <span class="duracion">hs · {{ turno.dur }}</span>
              </div>
              <div class="dia">{{ turno.dia }}</div>
            </div>
            <span
              class="nivel-badge"
              :style="{ background: nivelColors[turno.nivel].bg, color: nivelColors[turno.nivel].text }"
            >{{ turno.nivel }}</span>
          </div>
 
          <div class="instructor-row">
            <div class="inst-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#00897B" stroke-width="2" stroke-linecap="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <div>
              <div class="inst-label">Instructor/a</div>
              <div class="inst-name">{{ turno.inst }}</div>
            </div>
          </div>
 
          <div>
            <div class="cap-row">
              <span class="cap-text">
                {{ turno.ocup >= turno.total ? 'Sin lugares disponibles' : `${turno.total - turno.ocup} lugar${turno.total - turno.ocup !== 1 ? 'es' : ''} disponible${turno.total - turno.ocup !== 1 ? 's' : ''}` }}
              </span>
              <span class="cap-num" :style="{ color: barColor(turno) }">{{ turno.ocup }}/{{ turno.total }}</span>
            </div>
            <div class="bar-bg">
              <div class="bar-fill" :style="{ width: pct(turno) + '%', background: barColor(turno) }"></div>
            </div>
          </div>
 
          <button
            class="reservar-btn"
            :disabled="turno.ocup >= turno.total"
            :class="{ lleno: turno.ocup >= turno.total, reservado: reservados.has(turno.id) }"
            @click="toggleReserva(turno.id)"
          >
            {{ turno.ocup >= turno.total ? 'Sin disponibilidad' : reservados.has(turno.id) ? 'Cancelar reserva' : 'Reservar turno' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
 
<script setup>
import { ref, computed } from 'vue'
 
const tabs = ['Pilates', 'Yoga', 'Funcional']
const currentTab = ref('Pilates')
const reservados = ref(new Set())
 
const tabIcons = {
  Pilates: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="5" r="2"/><path d="M12 7v5l-3 3m3-3 3 3M8 21l1.5-4M16 21l-1.5-4"/></svg>`,
  Yoga: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="4" r="2"/><path d="M12 6v4M9 10c-2 2-3 4-2 6M15 10c2 2 3 4 2 6M7 16c2 2 5 3 5 3s3-1 5-3"/></svg>`,
  Funcional: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M6 4v16M18 4v16M6 12h12M3 8h3M18 8h3M3 16h3M18 16h3"/></svg>`,
}
 
const nivelColors = {
  'Principiante':      { bg: '#E8F5E9', text: '#2E7D32' },
  'Intermedio':        { bg: '#FFF8E1', text: '#F57F17' },
  'Avanzado':          { bg: '#FCE4EC', text: '#880E4F' },
  'Todos los niveles': { bg: '#E0F2F1', text: '#00695C' },
}
 
const data = {
  Pilates: [
    { id:1,  dia:'Lun / Mié / Vie', hora:'07:00', dur:'60 min', inst:'Laura Gómez',   total:12, ocup:8,  nivel:'Intermedio' },
    { id:2,  dia:'Mar / Jue',        hora:'09:00', dur:'60 min', inst:'Laura Gómez',   total:12, ocup:12, nivel:'Avanzado' },
    { id:3,  dia:'Lun / Mié',        hora:'18:00', dur:'60 min', inst:'Carla Torres',  total:12, ocup:3,  nivel:'Principiante' },
    { id:4,  dia:'Sábado',           hora:'10:00', dur:'75 min', inst:'Carla Torres',  total:10, ocup:7,  nivel:'Todos los niveles' },
  ],
  Yoga: [
    { id:5,  dia:'Lun / Mié / Vie', hora:'08:00', dur:'60 min', inst:'Sofía Martín',  total:15, ocup:5,  nivel:'Principiante' },
    { id:6,  dia:'Mar / Jue',        hora:'19:00', dur:'75 min', inst:'Sofía Martín',  total:15, ocup:11, nivel:'Intermedio' },
    { id:7,  dia:'Sábado',           hora:'09:00', dur:'90 min', inst:'Diego Ruiz',    total:10, ocup:2,  nivel:'Todos los niveles' },
    { id:8,  dia:'Domingo',          hora:'10:00', dur:'60 min', inst:'Diego Ruiz',    total:12, ocup:9,  nivel:'Avanzado' },
  ],
  Funcional: [
    { id:9,  dia:'Lun a Vie',        hora:'06:00', dur:'45 min', inst:'Marcos Díaz',   total:20, ocup:15, nivel:'Intermedio' },
    { id:10, dia:'Lun / Mié / Vie', hora:'12:00', dur:'45 min', inst:'Marcos Díaz',   total:20, ocup:8,  nivel:'Todos los niveles' },
    { id:11, dia:'Mar / Jue',        hora:'19:00', dur:'60 min', inst:'Ana Rodríguez', total:20, ocup:18, nivel:'Avanzado' },
    { id:12, dia:'Sábado',           hora:'08:00', dur:'60 min', inst:'Ana Rodríguez', total:15, ocup:6,  nivel:'Principiante' },
  ],
}
 
const currentTurnos = computed(() => data[currentTab.value])
const disponibles = computed(() => currentTurnos.value.filter(t => t.ocup < t.total).length)
const completos   = computed(() => currentTurnos.value.filter(t => t.ocup >= t.total).length)
 
const pct = (t) => Math.min(Math.round((t.ocup / t.total) * 100), 100)
const barColor = (t) => {
  const p = pct(t)
  return p >= 100 ? '#E53935' : p >= 75 ? '#FB8C00' : '#00897B'
}
 
const toggleReserva = (id) => {
  const s = new Set(reservados.value)
  s.has(id) ? s.delete(id) : s.add(id)
  reservados.value = s
}
</script>
 
<style scoped>
* { box-sizing: border-box; }
 
.page {
  min-height: 100vh;
  background: linear-gradient(135deg, #E0F7F4 0%, #F0FAF8 50%, #E8F5E9 100%);
  font-family: 'Segoe UI', system-ui, sans-serif;
}
 
.header {
  background: #fff;
  border-bottom: 1px solid #E0F2F1;
  padding: 0 24px;
  box-shadow: 0 2px 12px rgba(0,137,123,0.08);
}
.header-inner {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
}
.logo { font-size: 19px; font-weight: 900; color: #00695C; letter-spacing: 0.08em; }
.account { display: flex; align-items: center; gap: 8px; }
.avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: #E0F2F1; display: flex; align-items: center; justify-content: center;
}
.account-label { font-size: 13px; color: #546E7A; font-weight: 500; }
 
.main { max-width: 900px; margin: 0 auto; padding: 28px 16px 60px; }
 
h1 { font-size: 24px; font-weight: 800; color: #00695C; margin: 0 0 6px; letter-spacing: -0.5px; }
.subtitle { font-size: 14px; color: #607D8B; margin: 0 0 24px; }
 
.tab-bar {
  display: flex; gap: 8px;
  background: #fff; padding: 5px;
  border-radius: 99px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  width: fit-content;
  margin-bottom: 22px;
}
.tab-btn {
  display: flex; align-items: center; gap: 7px;
  padding: 9px 18px; border-radius: 99px;
  border: none; background: transparent;
  color: #78909C; font-weight: 500; font-size: 14px;
  cursor: pointer; transition: all 0.2s ease;
}
.tab-btn.active { background: #00897B; color: #fff; font-weight: 700; }
.tab-icon { display: flex; align-items: center; }
 
.badges { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.badge {
  background: #fff; border-radius: 12px;
  padding: 10px 16px; display: flex;
  align-items: center; gap: 10px;
  border: 1px solid #E0F2F1;
}
.badge-num { font-size: 22px; font-weight: 800; }
.badge-label { font-size: 13px; color: #78909C; }
 
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
 
.card {
  background: #fff; border-radius: 16px;
  border: 1px solid #E0E0E0;
  padding: 18px 20px;
  display: flex; flex-direction: column; gap: 13px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  transition: all 0.25s ease;
  position: relative; overflow: hidden;
}
.card.reserved { border-color: #00897B; box-shadow: 0 0 0 3px #E0F2F1; }
 
.reserved-badge {
  position: absolute; top: 0; right: 0;
  background: #00897B; color: #fff;
  font-size: 10px; font-weight: 700;
  padding: 4px 12px;
  border-radius: 0 16px 0 12px;
  letter-spacing: 0.04em;
}
 
.card-top { display: flex; justify-content: space-between; align-items: flex-start; }
.hora-row { display: flex; align-items: baseline; gap: 6px; }
.hora { font-size: 22px; font-weight: 800; color: #00695C; letter-spacing: -0.5px; }
.duracion { font-size: 13px; color: #90A4AE; font-weight: 500; }
.dia { font-size: 13px; color: #455A64; font-weight: 500; margin-top: 2px; }
.nivel-badge {
  font-size: 10px; font-weight: 700;
  padding: 4px 10px; border-radius: 99px;
  letter-spacing: 0.03em; white-space: nowrap;
}
 
.instructor-row { display: flex; align-items: center; gap: 8px; }
.inst-icon {
  width: 30px; height: 30px; border-radius: 50%;
  background: #E0F2F1; display: flex;
  align-items: center; justify-content: center; flex-shrink: 0;
}
.inst-label { font-size: 10px; color: #90A4AE; line-height: 1; }
.inst-name { font-size: 13px; font-weight: 600; color: #37474F; }
 
.cap-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
.cap-text { font-size: 12px; color: #607D8B; }
.cap-num { font-size: 12px; font-weight: 600; }
.bar-bg { background: #E0E0E0; border-radius: 99px; height: 6px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 99px; transition: width 0.6s ease; }
 
.reservar-btn {
  width: 100%; padding: 11px 0;
  border-radius: 99px; border: none;
  background: #00897B; color: #fff;
  font-weight: 700; font-size: 14px;
  cursor: pointer; letter-spacing: 0.02em;
  transition: all 0.2s ease;
}
.reservar-btn:hover:not(:disabled) { background: #00695C; }
.reservar-btn.reservado {
  background: #fff; color: #00897B;
  outline: 2px solid #00897B;
}
.reservar-btn.lleno {
  background: #ECEFF1; color: #90A4AE;
  cursor: not-allowed;
}
</style>