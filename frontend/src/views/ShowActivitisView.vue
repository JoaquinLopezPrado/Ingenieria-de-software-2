<template>
  <div class="page">

    <div class="main">
      <h1>Actividades disponibles</h1>
      <p class="subtitle">Elegí tu actividad y reservá tu lugar en el turno que más te convenga.</p>
 
      <!-- Tabs -->
      <ActivitiesBar v-model="currentTab">
        <ActivityBtn v-for="tab in tabs" :key="tab" :value="tab">
          <span v-html="tabIcons[tab]" class="tab-icon" />
          {{ tab }}
        </ActivityBtn>
      </ActivitiesBar>

      <div v-if="loading">
        Cargando turnos...
      </div>

      <div v-else class="badges">
        <div class="badge">
          <span class="badge-num" style="color: #00897B">
            {{ disponibles }}
          </span>

          <span class="badge-label">
            Turnos disponibles
          </span>
        </div>

        <div class="badge">
          <span class="badge-num" style="color: #E53935">
            {{ completos }}
          </span>

          <span class="badge-label">
            Turnos completos
          </span>
        </div>
      </div>

      <div class="grid">
        <div
          v-for="turno in currentTurnos"
          :key="turno.id"
          class="card"
          :class="{ inscripto: inscriptos.has(turno.id) }"
        >

          <div
            v-if="inscriptos.has(turno.id)"
            class="inscripto-badge"
          >
            INSCRIPTO ✓
          </div>

          <div class="card-top">
            <div>
              <div class="hora-row">
                <span class="hora">
                  {{ turno.hora }}
                </span>

                <span class="duracion">
                  hs · {{ turno.dur }}
                </span>
              </div>

              <div class="dia">
                {{ turno.dia }}
              </div>
            </div>

            <span
              class="nivel-badge"
              :style="{
                background: nivelColors[turno.nivel].bg,
                color: nivelColors[turno.nivel].text
              }"
            >
              {{ turno.nivel }}
            </span>
          </div>

          <div class="instructor-row">
            <div class="inst-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#00897B" stroke-width="2" stroke-linecap="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>

            <div>
              <div class="inst-label">
                Instructor/a
              </div>

              <div class="inst-name">
                {{ turno.inst }}
              </div>
            </div>
          </div>

          <div>
            <div class="cap-row">
              <span class="cap-text">
                {{ turno.ocup >= turno.total
                  ? 'Sin lugares disponibles'
                  : `${turno.total - turno.ocup} lugar${turno.total - turno.ocup !== 1 ? 'es' : ''} disponible${turno.total - turno.ocup !== 1 ? 's' : ''}` }}
              </span>

              <span
                class="cap-num"
                :style="{ color: barColor(turno) }"
              >
                {{ turno.ocup }}/{{ turno.total }}
              </span>
            </div>

            <div class="bar-bg">
              <div
                class="bar-fill"
                :style="{
                  width: pct(turno) + '%',
                  background: barColor(turno)
                }"
              ></div>
            </div>
          </div>
 
          <div class="acciones-card">
            <button
              class="accion-btn"
              :disabled="turno.ocup >= turno.total && !inscriptos.has(turno.id)"
              :class="{
                lleno: turno.ocup >= turno.total && !inscriptos.has(turno.id),
                inscripto: inscriptos.has(turno.id)
              }"
              @click="handleInscripcion(turno)"
            >
              {{ turno.ocup >= turno.total && !inscriptos.has(turno.id)
                ? 'Sin disponibilidad'
                : inscriptos.has(turno.id)
                ? 'Cancelar inscripción'
                : 'Inscribirse' }}
            </button>

            <button
              class="secondary-btn"
              type="button"
              @click="goToClassSelection(turno)"
            >
              Ver clases de prueba individual
            </button>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { enrollmentService } from '@/services/enrollmentService'
import { turnoService } from '@/services/turnoService'
import { getFormOptions } from '@/services/sessionService'
import ActivitiesBar from '@/components/ui/ActivitiesBar.vue'
import ActivityBtn from '@/components/ui/ActivityBtn.vue'
import { ACTIVITY_ICONS, DEFAULT_ACTIVITY_ICON } from '@/constants/activityIcons'

const router = useRouter()

const activities = ref([])
const tabs = computed(() => activities.value.map(a => a.name))
const currentTab = ref('')
const inscriptos = ref(new Set())
const avisoLleno = ref(null)
const errorMensaje = ref(null)
const loadingTurno = ref(null)

const loading = ref(false)
const turnos = ref([])

const tabIcons = computed(() =>
  Object.fromEntries(activities.value.map(a => [a.name, ACTIVITY_ICONS[a.name] ?? DEFAULT_ACTIVITY_ICON]))
)

const nivelColors = {
  Principiante: {
    bg: '#E8F5E9',
    text: '#2E7D32',
  },
  Intermedio: {
    bg: '#FFF8E1',
    text: '#F57F17',
  },
  Avanzado: {
    bg: '#FCE4EC',
    text: '#880E4F',
  },
  'Todos los niveles': {
    bg: '#E0F2F1',
    text: '#00695C',
  },
}

onMounted(async () => {
  try {
    loading.value = true

    const [{ activities: acts }, turnosRes] = await Promise.all([
      getFormOptions(),
      turnoService.getTurnos(),
    ])

    activities.value = acts
    if (acts.length > 0) currentTab.value = acts[0].name

    const nameMap = new Map(acts.map(a => [a.id, a.name]))
    const items = turnosRes.data.items || []

    turnos.value = items.map((turno) => ({
      id: turno.id,
      activityId: turno.activity_id,
      actividad: nameMap.get(turno.activity_id) ?? `Actividad #${turno.activity_id}`,
      dia: turno.days?.join(' / ') || 'Sin días',
      hora: turno.start_time,
      horaFin: turno.end_time,
      dur: `${turno.start_time} - ${turno.end_time}`,
      inst: turno.instructor_name || turno.instructor || 'Instructor',
      total: turno.capacity,
      ocup: turno.occupied ?? 0,
      nivel: turno.level || 'Todos los niveles',
      sala: turno.room_number ?? turno.room ?? 'Sin sala',
    }))
  } catch (error) {
    console.error('Error al cargar actividades o turnos', error)
  } finally {
    loading.value = false
  }
})

const currentTurnos = computed(() => {
  return turnos.value.filter(
    (t) => t.actividad === currentTab.value
  )
})

const disponibles = computed(() => {
  return currentTurnos.value.filter(
    (t) => t.ocup < t.total
  ).length
})

const completos = computed(() => {
  return currentTurnos.value.filter(
    (t) => t.ocup >= t.total
  ).length
})

const pct = (t) => {
  return Math.min(
    Math.round((t.ocup / t.total) * 100),
    100
  )
}

const barColor = (t) => {
  const p = pct(t)

  return p >= 100
    ? '#E53935'
    : p >= 75
    ? '#FB8C00'
    : '#00897B'
}
 
const handleInscripcion = async (turno) => {
  if (inscriptos.value.has(turno.id) || turno.ocup >= turno.total) return

  loadingTurno.value = turno.id
  errorMensaje.value = null

  try {
    const { data } = await enrollmentService.createMonthly(turno.id)

    const s = new Set(inscriptos.value)
    s.add(turno.id)
    turno.ocup++
    inscriptos.value = s

    router.push({
      name: 'ticket',
      query: {
        enrollment_id:      data.id,
        actividad:          turno.actividad,
        dia:                turno.dia,
        hora:               turno.hora,
        duracion:           turno.dur,
        instructor:         turno.inst,
        nivel:              turno.nivel,
        numero:             data.id,
        amount:             data.amount,
        clases_excluidas:   data.excluded_clase_ids?.length ?? 0,
        expires_at:         data.expires_at,
      },
    })
  } catch (err) {
    const detail = err.response?.data?.errors?.general
    if (err.response?.status === 409) {
      errorMensaje.value = detail ?? 'No hay lugares disponibles.'
    } else if (err.response?.status === 404) {
      errorMensaje.value = 'El turno no está disponible.'
    } else {
      errorMensaje.value = 'Ocurrió un error. Intentá de nuevo.'
    }
    avisoLleno.value = turno.id
    setTimeout(() => { avisoLleno.value = null; errorMensaje.value = null }, 3000)
  } finally {
    loadingTurno.value = null
  }
}

const goToClassSelection = (turno) => {
  router.push({
    name: 'class-selection',
    query: {
      turnoId: String(turno.id),
      activityId: String(turno.activityId),
      actividad: turno.actividad,
      horaInicio: turno.hora,
      horaFin: turno.horaFin,
      dias: turno.dia,
      sala: String(turno.sala),
      instructor: turno.inst,
      nivel: turno.nivel,
    },
  })
}
</script>

<style scoped>
* { box-sizing: border-box; }
.tab-icon { display: flex; align-items: center; }
.page { min-height: 100vh; background: linear-gradient(135deg, #E0F7F4 0%, #F0FAF8 50%, #E8F5E9 100%); font-family: 'Segoe UI', system-ui, sans-serif; }
.header { background: #fff; border-bottom: 1px solid #E0F2F1; padding: 0 24px; box-shadow: 0 2px 12px rgba(0,137,123,0.08); }
.header-inner { max-width: 900px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; height: 60px; }
.logo { font-size: 19px; font-weight: 900; color: #00695C; letter-spacing: 0.08em; }
.account { display: flex; align-items: center; gap: 8px; }
.avatar { width: 34px; height: 34px; border-radius: 50%; background: #E0F2F1; display: flex; align-items: center; justify-content: center; }
.account-label { font-size: 13px; color: #546E7A; font-weight: 500; }
.main { max-width: 900px; margin: 0 auto; padding: 28px 16px 60px; }
h1 { font-size: 24px; font-weight: 800; color: #00695C; margin: 0 0 6px; letter-spacing: -0.5px; }
.subtitle { font-size: 14px; color: #607D8B; margin: 0 0 24px; }
.badges { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.badge { background: #fff; border-radius: 12px; padding: 10px 16px; display: flex; align-items: center; gap: 10px; border: 1px solid #E0F2F1; }
.badge-num { font-size: 22px; font-weight: 800; }
.badge-label { font-size: 13px; color: #78909C; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
.card { background: #fff; border-radius: 16px; border: 1px solid #E0E0E0; padding: 18px 20px; display: flex; flex-direction: column; gap: 13px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); transition: all 0.25s ease; position: relative; overflow: hidden; }
.card.inscripto { border-color: #00897B; box-shadow: 0 0 0 3px #E0F2F1; }
.inscripto-badge { position: absolute; top: 0; right: 0; background: #00897B; color: #fff; font-size: 10px; font-weight: 700; padding: 4px 12px; border-radius: 0 16px 0 12px; letter-spacing: 0.04em; }
.card-top { display: flex; justify-content: space-between; align-items: flex-start; }
.hora-row { display: flex; align-items: baseline; gap: 6px; }
.hora { font-size: 22px; font-weight: 800; color: #00695C; letter-spacing: -0.5px; }
.duracion { font-size: 13px; color: #90A4AE; font-weight: 500; }
.dia { font-size: 13px; color: #455A64; font-weight: 500; margin-top: 2px; }
.nivel-badge { font-size: 10px; font-weight: 700; padding: 4px 10px; border-radius: 99px; letter-spacing: 0.03em; white-space: nowrap; }
.instructor-row { display: flex; align-items: center; gap: 8px; }
.inst-icon { width: 30px; height: 30px; border-radius: 50%; background: #E0F2F1; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.inst-label { font-size: 10px; color: #90A4AE; line-height: 1; }
.inst-name { font-size: 13px; font-weight: 600; color: #37474F; }
.cap-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
.cap-text { font-size: 12px; color: #607D8B; }
.cap-num { font-size: 12px; font-weight: 600; }
.bar-bg { background: #E0E0E0; border-radius: 99px; height: 6px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 99px; transition: width 0.6s ease; }
.accion-btn { width: 100%; padding: 11px 0; border-radius: 99px; border: none; background: #00897B; color: #fff; font-weight: 700; font-size: 14px; cursor: pointer; letter-spacing: 0.02em; transition: all 0.2s ease; }
.accion-btn:hover:not(:disabled) { background: #00695C; }
.accion-btn.inscripto { background: #fff; color: #00897B; outline: 2px solid #00897B; }
.accion-btn.lleno { background: #ECEFF1; color: #90A4AE; cursor: not-allowed; }
.aviso-lleno {
  background: #FFEBEE;
  color: #C62828;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  animation: fadeIn 0.2s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}

* {
  box-sizing: border-box;
}

.page {
  min-height: 100vh;
  background: linear-gradient(
    135deg,
    #e4f3f0 0%,
    #edf7f5 50%,
    #f3faf8 100%
  );
  font-family:
    'Inter',
    'Segoe UI',
    system-ui,
    sans-serif;
  padding-top: 60px;
}

/* HEADER */


/* MAIN */

.main {
  max-width: 1180px;
  margin: 0 auto;
  padding: 42px 24px 70px;
}

/* HERO */

h1 {
  font-size: 2.35rem;
  font-weight: 900;
  color: #00695c;
  margin: 0 0 10px;
  letter-spacing: -1px;
}

.subtitle {
  font-size: 1rem;
  color: #607d8b;
  margin: 0 0 32px;
  max-width: 620px;
  line-height: 1.5;
}

/* BADGES */

.badges {
  display: flex;
  gap: 14px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

.badge {
  min-width: 190px;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(10px);
  border-radius: 18px;
  padding: 16px 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid rgba(0, 137, 123, 0.08);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.04);
}

.badge-num {
  font-size: 1.9rem;
  font-weight: 900;
  line-height: 1;
}

.badge-label {
  font-size: 0.92rem;
  color: #78909c;
  font-weight: 600;
}

/* GRID */

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  align-items: start;
}

/* CARD */

.card {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  border-radius: 28px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(0, 137, 123, 0.08);
  box-shadow:
    0 10px 30px rgba(0, 0, 0, 0.06),
    0 2px 8px rgba(0, 0, 0, 0.03);
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow:
    0 18px 40px rgba(0, 0, 0, 0.08),
    0 4px 12px rgba(0, 0, 0, 0.04);
}

.card.inscripto {
  border: 2px solid #00897b;
}

.inscripto-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #00897b;
  color: white;
  font-size: 10px;
  font-weight: 800;
  padding: 6px 14px;
  border-radius: 0 24px 0 16px;
  letter-spacing: 0.05em;
}

/* CARD TOP */

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.hora-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.hora {
  font-size: 2rem;
  font-weight: 900;
  color: #00695c;
  letter-spacing: -1px;
}

.duracion {
  font-size: 13px;
  color: #90a4ae;
  font-weight: 600;
}

.dia {
  font-size: 14px;
  color: #455a64;
  font-weight: 600;
  margin-top: 4px;
  line-height: 1.4;
}

.nivel-badge {
  font-size: 11px;
  font-weight: 800;
  padding: 6px 12px;
  border-radius: 999px;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

/* INSTRUCTOR */

.instructor-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.inst-icon {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #e0f2f1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.inst-label {
  font-size: 11px;
  color: #90a4ae;
  line-height: 1;
  margin-bottom: 2px;
}

.inst-name {
  font-size: 14px;
  font-weight: 700;
  color: #37474f;
}

/* CAPACIDAD */

.cap-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.cap-text {
  font-size: 13px;
  color: #607d8b;
  font-weight: 500;
}

.cap-num {
  font-size: 13px;
  font-weight: 700;
}

.bar-bg {
  background: #e0e0e0;
  border-radius: 999px;
  height: 8px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.5s ease;
}

/* BOTONES */

.acciones-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 4px;
}

.accion-btn {
  width: 100%;
  padding: 13px 0;
  border-radius: 999px;
  border: none;
  background: #00897b;
  color: white;
  font-weight: 800;
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 0.02em;
  transition:
    transform 0.18s ease,
    background 0.18s ease,
    box-shadow 0.18s ease;
  box-shadow: 0 10px 18px rgba(0, 137, 123, 0.18);
}

.accion-btn:hover:not(:disabled) {
  background: #00695c;
  transform: translateY(-1px);
}

.accion-btn.inscripto {
  background: white;
  color: #00897b;
  border: 2px solid #00897b;
  box-shadow: none;
}

.accion-btn.lleno {
  background: #eceff1;
  color: #90a4ae;
  cursor: not-allowed;
  box-shadow: none;
}

.secondary-btn {
  width: 100%;
  padding: 13px 0;
  border-radius: 999px;
  border: 1.5px solid #00897b;
  background: transparent;
  color: #00897b;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition:
    background 0.18s ease,
    transform 0.18s ease;
}

.secondary-btn:hover {
  background: rgba(0, 137, 123, 0.08);
  transform: translateY(-1px);
}

/* MOBILE */

@media (max-width: 768px) {
  .header {
    padding: 0 18px;
  }

  .header-inner {
    height: 64px;
  }

  .main {
    padding: 28px 18px 50px;
  }

  h1 {
    font-size: 1.9rem;
  }

  .grid {
    grid-template-columns: 1fr;
  }

  .badge {
    width: 100%;
  }

}
</style>