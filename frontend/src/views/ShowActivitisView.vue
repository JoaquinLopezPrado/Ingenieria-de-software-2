<template>
  <div class="page">

    <div class="main">
      <div v-if="googleLinked" class="banner banner-success">
        Tu cuenta de Google fue vinculada correctamente.
      </div>
      <div v-if="googleAlreadyInUse" class="banner banner-error">
        Esta cuenta de Google ya está asociada a otro usuario. Por favor, utilizá una cuenta diferente.
      </div>
      <div v-if="googleUnlinked" class="banner banner-success">
        Tu cuenta de Google fue desvinculada correctamente.
      </div>
      <div v-if="googleLinkError" class="banner banner-error">
        {{ googleErrorReason ?? 'No se pudo vincular la cuenta de Google. Intentá de nuevo.' }}
      </div>
      <div v-if="googleUnlinkError" class="banner banner-error">
        No se pudo desvincular la cuenta de Google. Intentá de nuevo.
      </div>

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
          <span class="badge-label">Turnos disponibles</span>
        </div>

        <div class="badge">
          <span class="badge-num" style="color: #E53935">
            {{ completos }}
          </span>
          <span class="badge-label">Turnos completos</span>
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
          <!-- CARD TOP: nombre + hora | agotado badge -->
          <div class="card-top">
            <div>
              <div class="turno-nombre">{{ turno.nombre }}</div>
              <div class="hora-row">
                <span class="hora">{{ turno.descripcion }}</span>
              </div>
              <div class="dia">{{ turno.dur }} · {{ turno.dia }}</div>
            </div>
            <span
              v-if="turno.ocup >= turno.total"
              class="agotado-badge"
            >
              AGOTADO
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
              <div class="inst-label">Instructor/a</div>
              <div class="inst-name">{{ turno.inst }}</div>
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

          <div v-if="turnosPendienteMensual.has(turno.id)" class="acciones-card">
            <button
              class="continuar-btn"
              type="button"
              @click="continuarPago(turno)"
            >
              Continuar con el pago
            </button>
          </div>

          <div v-else-if="!inscriptos.has(turno.id)" class="acciones-card">
            <button
              class="accion-btn"
              :disabled="inscriptos.has(turno.id)"
              :class="{
                espera: turno.ocup >= turno.total && !inscriptos.has(turno.id),
                inscripto: inscriptos.has(turno.id)
              }"
              @click="handleInscripcion(turno)"
            >
              {{ inscriptos.has(turno.id)
                ? 'Cancelar inscripción'
                : turno.ocup >= turno.total
                ? 'Inscribirse a la lista de espera'
                : 'Inscribirse' }}
            </button>

            <button
              v-if="!turnosConClaseSuelta.has(turno.id)"
              class="secondary-btn"
              :class="{ 'secondary-btn--espera': turno.ocup >= turno.total }"
              type="button"
              @click="goToClassSelection(turno)"
            >
              {{ turno.ocup >= turno.total
                ? 'Anotarse en lista de espera para clase de prueba'
                : 'Ver clases de prueba individual' }}
            </button>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { enrollmentService } from '@/services/enrollmentService'
import { turnoService } from '@/services/turnoService'
import { getFormOptions } from '@/services/sessionService'
import ActivitiesBar from '@/components/ui/ActivitiesBar.vue'
import ActivityBtn from '@/components/ui/ActivityBtn.vue'
import { ACTIVITY_ICONS, DEFAULT_ACTIVITY_ICON } from '@/constants/activityIcons'

const router = useRouter()
const route = useRoute()

const googleLinked = computed(() => route.query.google_linked === 'true')
const googleAlreadyInUse = computed(() => route.query.error === 'google_already_in_use')
const googleLinkError = computed(() => route.query.error === 'google_link_failed')
const googleUnlinked = computed(() => route.query.google_unlinked === 'true')
const googleUnlinkError = computed(() => route.query.error === 'google_unlink_failed')
const googleErrorReason = computed(() => googleLinkError.value && route.query.reason ? String(route.query.reason) : null)

const activities = ref([])
const tabs = computed(() => activities.value.map(a => a.name))
const currentTab = ref('')
const inscriptos = ref(new Set())
const turnosConClaseSuelta = ref(new Set())
const turnosPendienteMensual = ref(new Map())
const avisoLleno = ref(null)
const errorMensaje = ref(null)
const loadingTurno = ref(null)

const loading = ref(false)
const turnos = ref([])

const tabIcons = computed(() =>
  Object.fromEntries(activities.value.map(a => [a.name, ACTIVITY_ICONS[a.name] ?? DEFAULT_ACTIVITY_ICON]))
)

onMounted(async () => {
  try {
    loading.value = true

    const [{ activities: acts }, turnosRes, myMonthlyRes, mySingleRes] = await Promise.all([
      getFormOptions(),
      turnoService.getTurnos(),
      enrollmentService.getMyMonthly(),
      enrollmentService.getMySingle(),
    ])

    activities.value = acts
    if (acts.length > 0) currentTab.value = acts[0].name

    const nameMap = new Map(acts.map(a => [a.id, a.name]))
    const items = turnosRes.data.items || []

    turnos.value = items.map((turno) => ({
      id: turno.id,
      activityId: turno.activity_id,
      actividad: nameMap.get(turno.activity_id) ?? `Actividad #${turno.activity_id}`,
      nombre: (turno.name || turno.nombre || nameMap.get(turno.activity_id) || '')
        .replace(/:/g, '')
        .trim(),
      dia: turno.days?.join(' / ') || 'Sin días',
      hora: turno.start_time,
      horaFin: turno.end_time,
      dur: `${turno.start_time} - ${turno.end_time}`,
      inst: turno.instructor_name || turno.instructor || 'Instructor',
      total: turno.capacity,
      ocup: turno.enrolled ?? 0,
      nivel: turno.level || 'Todos los niveles',
      descripcion: turno.description ?? '',
      sala: turno.room_number ?? turno.room ?? 'Sin sala',
    }))

    inscriptos.value = new Set(
      myMonthlyRes.data
        .filter((e) => e.status === 'confirmed')
        .map((e) => e.turno_id)
    )

    turnosPendienteMensual.value = new Map(
      myMonthlyRes.data
        .filter((e) => e.status === 'pending')
        .map((e) => [e.turno_id, e])
    )

    turnosConClaseSuelta.value = new Set(
      mySingleRes.data
        .filter((e) => e.status === 'confirmed' || e.status === 'pending')
        .map((e) => e.turno_id)
    )
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
  if (inscriptos.value.has(turno.id)) return

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
        descripcion:        turno.descripcion,
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

const continuarPago = (turno) => {
  const enrollment = turnosPendienteMensual.value.get(turno.id)
  if (!enrollment) return
  router.push({
    name: 'ticket',
    query: {
      enrollment_id: enrollment.enrollment_id,
      actividad:     turno.actividad,
      descripcion:   turno.descripcion,
      dia:           turno.dia,
      hora:          turno.hora,
      duracion:      turno.dur,
      instructor:    turno.inst,
      nivel:         turno.nivel,
      numero:        enrollment.enrollment_id,
      amount:        enrollment.amount,
      expires_at:    enrollment.expires_at,
    },
  })
}

const goToClassSelection = (turno) => {
  router.push({
    name: 'class-selection',
    query: {
      turnoId:    String(turno.id),
      activityId: String(turno.activityId),
      actividad:  turno.actividad,
      horaInicio: turno.hora,
      horaFin:    turno.horaFin,
      dias:       turno.dia,
      sala:       String(turno.sala),
      instructor: turno.inst,
      nivel:      turno.nivel,
    },
  })
}
</script>

<style scoped>
* { box-sizing: border-box; }
.tab-icon { display: flex; align-items: center; }

.page {
  min-height: 100vh;
  background: linear-gradient(135deg, #e4f3f0 0%, #edf7f5 50%, #f3faf8 100%);
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  padding-top: 60px;
}

/* HEADER */
.header {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 137, 123, 0.08);
  padding: 0 28px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-inner {
  max-width: 1180px;
  margin: 0 auto;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  font-size: 1.55rem;
  font-weight: 900;
  color: #00695c;
  letter-spacing: 0.08em;
}

.account {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: 999px;
  transition: background 0.2s ease;
  cursor: pointer;
}

.account:hover { background: rgba(0, 137, 123, 0.06); }

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #e0f2f1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.account-label {
  font-size: 14px;
  color: #546e7a;
  font-weight: 600;
}

/* MAIN */
.main {
  max-width: 1180px;
  margin: 0 auto;
  padding: 24px 24px 70px;
}

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
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06), 0 2px 8px rgba(0, 0, 0, 0.03);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.08), 0 4px 12px rgba(0, 0, 0, 0.04);
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

.turno-nombre {
  font-size: 1.05rem;
  font-weight: 800;
  color: #00695c;
  line-height: 1.2;
  margin-bottom: 4px;
  letter-spacing: -0.3px;
}

.hora-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.hora {
  font-size: 1.45rem;
  font-weight: 800;
  color: #455a64;
  letter-spacing: -0.5px;
}

.duracion {
  font-size: 12px;
  color: #90a4ae;
  font-weight: 600;
}

.dia {
  font-size: 11px;
  color: #78909c;
  font-weight: 500;
  margin-top: 3px;
  line-height: 1.4;
}

.agotado-badge {
  font-size: 10px;
  font-weight: 800;
  padding: 5px 11px;
  border-radius: 999px;
  background: #FFEBEE;
  color: #C62828;
  letter-spacing: 0.06em;
  white-space: nowrap;
  flex-shrink: 0;
  border: 1px solid #FFCDD2;
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
  gap: 10px;
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
  transition: transform 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
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

.accion-btn.inscripto:hover:not(:disabled) {
  background: #f1faf9;
  transform: translateY(-1px);
}

.accion-btn.espera {
  background: #F57C00;
  color: white;
  box-shadow: 0 10px 18px rgba(245, 124, 0, 0.20);
}

.accion-btn.espera:hover:not(:disabled) {
  background: #E65100;
  transform: translateY(-1px);
}

.continuar-btn {
  width: 100%;
  padding: 13px 0;
  border-radius: 999px;
  border: none;
  background: #F57C00;
  color: white;
  font-weight: 800;
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 0.02em;
  transition: transform 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
  box-shadow: 0 10px 18px rgba(245, 124, 0, 0.20);
}

.continuar-btn:hover {
  background: #E65100;
  transform: translateY(-1px);
}

.secondary-btn {
  width: 100%;
  padding: 12px 0;
  border-radius: 999px;
  border: 1.5px solid #00897b;
  background: transparent;
  color: #00897b;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.18s ease, transform 0.18s ease;
  line-height: 1.3;
}

.secondary-btn:hover {
  background: rgba(0, 137, 123, 0.08);
  transform: translateY(-1px);
}

.secondary-btn--espera {
  border-color: #F57C00;
  color: #F57C00;
}

.secondary-btn--espera:hover {
  background: rgba(245, 124, 0, 0.08);
}

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

/* MOBILE */
@media (max-width: 768px) {
  .header { padding: 0 18px; }
  .header-inner { height: 64px; }
  .main { padding: 20px 18px 50px; }
  h1 { font-size: 1.9rem; }
  .grid { grid-template-columns: 1fr; }
  .badge { width: 100%; }
}

.banner {
  border-radius: 12px;
  padding: 14px 18px;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 16px;
}

.banner-success {
  background-color: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

.banner-error {
  background-color: #fff5f5;
  color: #c0392b;
  border: 1px solid #fecaca;
}
</style>