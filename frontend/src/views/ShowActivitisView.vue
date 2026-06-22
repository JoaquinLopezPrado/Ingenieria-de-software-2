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
        {{ googleUnlinkErrorReason ?? 'No se pudo desvincular la cuenta de Google. Intentá de nuevo.' }}
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

      <!-- Date strip -->
      <div class="date-strip-header">
        <span class="strip-month">{{ stripMonthLabel }}</span>
        <button v-if="!todayInStrip" class="strip-hoy-btn" type="button" @click="goToToday">Hoy</button>
      </div>

      <div class="date-strip-nav">
        <button
          class="strip-arrow"
          :class="{ invisible: !canPrev }"
          type="button"
          aria-label="Anterior"
          @click="prevDay"
        >&#8249;</button>

        <div class="date-strip">
          <button
            v-for="date in visibleDates"
            :key="date"
            class="date-card"
            :class="{ active: selectedDate === date }"
            @click="selectedDate = date"
            type="button"
          >
            <span class="dc-day">{{ dateDay(date) }}</span>
            <span class="dc-num">{{ dateDayNum(date) }}</span>
            <span v-if="date === todayStr" class="dc-dot"></span>
          </button>
        </div>

        <button
          class="strip-arrow"
          :class="{ invisible: !canNext }"
          type="button"
          aria-label="Siguiente"
          @click="nextDay"
        >&#8250;</button>
      </div>

      <div v-if="loading">
        Cargando turnos...
      </div>

      <div class="grid">
        <div
          v-for="turno in currentTurnos"
          :key="turno.id"
          class="card"
          :class="{ inscripto: inscriptoEnFecha(turno) }"
        >

          <div
            v-if="inscriptoEnFecha(turno)"
            class="inscripto-badge"
          >
            SUSCRIPTO ✓
          </div>
          <div
            v-else-if="turnosConSeniaPagada.has(turno.id)"
            class="senia-badge"
          >
            SEÑADA
          </div>
          <div
            v-if="turnosConClaseConfirmadaEnFecha.has(turno.id)"
            class="lazo-clase"
          ><span class="lazo-star">✦</span></div>
          <!-- CARD TOP: nombre + hora | agotado badge -->
          <div class="card-top">
            <div>
              <div class="turno-nombre">{{ turno.nombre }}</div>
              <div class="hora-row">
                <span class="hora">{{ turno.descripcion }}</span>
              </div>
              <div class="dia">{{ turno.dur }}</div>
              <div class="day-chips">
                <span
                  v-for="day in turno.days"
                  :key="day"
                  class="day-chip"
                >{{ DAY_LABELS[day] ?? day }}</span>
              </div>
            </div>
            <span v-if="turno.hasRemainingClasses && sinCupoEnMes(turno)" class="agotado-badge">
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
              <div class="inst-name">{{ turno.inst.charAt(0).toUpperCase() + turno.inst.slice(1) }}</div>
            </div>
          </div>

          <div v-if="turno.hasRemainingClasses">
            <div class="cap-row">
              <span
                class="cap-num"
                :style="{ color: barColor(turno) }"
              >
                {{ cupoOcupado(turno) }}/{{ cupoTotal(turno) }}
              </span>
            </div>

            <div class="bar-bg" :style="{ background: barBgColor(turno) }">
              <div
                class="bar-fill"
                :style="{
                  width: pct(turno) + '%',
                  background: barColor(turno)
                }"
              ></div>
            </div>
          </div>

          <div v-if="!turno.hasFutureClasses" class="sin-clases-aviso">
            Este turno no tiene clases disponibles próximamente. Consultá con el centro para más información.
          </div>

          <template v-else>
            <div v-if="turnosPendienteMensual.has(turno.id)" class="acciones-card">
              <p class="pago-pendiente-info">
                Suscripción Mensual Pendiente
              </p>
              <button
                class="continuar-btn"
                type="button"
                @click="continuarPago(turno)"
              >
                Continuar con el pago
              </button>
            </div>

            <div v-else-if="turnosPendienteSingle.has(turno.id)" class="acciones-card">
              <p class="pago-pendiente-info">
                Clase individual pendiente · {{ formatFechaSingle(turnosPendienteSingle.get(turno.id).clase_date) }}
              </p>
              <button
                class="continuar-btn"
                type="button"
                @click="continuarPagoSingle(turno)"
              >
                Continuar con el pago de la clase individual
              </button>
            </div>

            <div v-else-if="!inscriptoEnFecha(turno)" class="acciones-card">
              <template v-if="enListaDeEspera(turno)">
                <p class="espera-info">Estás en la lista de espera de este turno.</p>
                <button
                  class="baja-btn"
                  type="button"
                  :disabled="loadingTurno === turno.id"
                  @click="handleLeaveWaitlist(turno)"
                >
                  {{ loadingTurno === turno.id ? 'Procesando...' : 'Salir de la lista' }}
                </button>
              </template>
              <template v-else>
              <button
                class="accion-btn"
                :class="{ espera: sinCupoEnMes(turno) }"
                @click="handleInscripcion(turno)"
                :disabled="loadingTurno === turno.id"
              >
                {{ loadingTurno === turno.id
                  ? 'Procesando...'
                  : sinCupoEnMes(turno)
                    ? 'Lista de espera · Suscripción Mensual'
                    : 'Suscripción Mensual' }}
              </button>

              <button
                v-if="turnosConSeniaPagada.has(turno.id)"
                class="secondary-btn"
                type="button"
                @click="handlePagarSaldo(turno)"
                :disabled="loadingTurno === turno.id"
              >
                Completar pago de seña
              </button>
              <button
                v-else-if="!turnosConClaseConfirmadaEnFecha.has(turno.id)"
                class="secondary-btn"
                :class="{ 'secondary-btn--espera': sinCupo(turno) }"
                type="button"
                @click="handleInscripcionSingle(turno)"
                :disabled="loadingTurno === turno.id"
              >
                {{ sinCupo(turno)
                  ? 'Lista de espera · Suscripción a Clase'
                  : 'Suscripción a Clase' }}
              </button>
              </template>
            </div>

            <div v-else class="acciones-card">
              <div v-if="activeSubsByTurno.get(turno.id)?.ends_on" class="baja-info">
                Baja programada: tu lugar sigue activo hasta el
                {{ formatBaja(activeSubsByTurno.get(turno.id).ends_on) }}
              </div>
              <template v-else-if="confirmandoBaja === turno.id">
                <p class="baja-confirm-msg">¿Confirmás la baja? Mantenés el lugar hasta el fin del período pagado.</p>
                <div class="baja-confirm-btns">
                  <button
                    class="baja-btn baja-btn--confirmar"
                    type="button"
                    :disabled="loadingTurno === turno.id"
                    @click="handleBaja(turno)"
                  >
                    {{ loadingTurno === turno.id ? 'Procesando...' : 'Sí, dar de baja' }}
                  </button>
                  <button
                    class="baja-btn baja-btn--cancelar"
                    type="button"
                    :disabled="loadingTurno === turno.id"
                    @click="confirmandoBaja = null"
                  >
                    Cancelar
                  </button>
                </div>
              </template>
              <button
                v-else
                class="baja-btn"
                type="button"
                @click="confirmandoBaja = turno.id"
              >
                Dar de baja
              </button>
            </div>
          </template>

          <div v-if="avisoLleno === turno.id && errorMensaje" class="error-aviso">
            {{ errorMensaje }}
          </div>

          <div v-if="pocosAbonosEnMes(turno) && !sinCupoEnMes(turno) && turno.hasRemainingClasses" class="marquee-wrapper">
            <span class="marquee-text">✦ ¡Pocos abonos disponibles! ✦ ¡Pocos abonos disponibles!</span>
          </div>

        </div>
      </div>

      <div v-if="!loading && currentTurnos.length === 0" class="no-turnos-msg">
        No hay turnos disponibles para este día.
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
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
const googleUnlinkErrorReason = computed(() => googleUnlinkError.value && route.query.reason ? String(route.query.reason) : null)

const DAY_LABELS = {
  lunes: 'Lun', martes: 'Mar', miercoles: 'Mié',
  jueves: 'Jue', viernes: 'Vie', sabado: 'Sáb',
}

const SHORT_DAYS = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
const dateDay = (str) => SHORT_DAYS[new Date(`${str}T00:00:00`).getDay()]
const dateDayNum = (str) => new Date(`${str}T00:00:00`).getDate()

const localDateStr = (d = new Date()) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

const todayStr = localDateStr()

const selectedDate = ref(localDateStr())
const classesByTurno = ref(new Map())

const MONTH_NAMES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

const selectedDateIdx = computed(() => availableDates.value.indexOf(selectedDate.value))
const canPrev = computed(() => selectedDateIdx.value > 0)
const canNext = computed(() => selectedDateIdx.value < availableDates.value.length - 1)

const visibleDates = computed(() => {
  const idx = selectedDateIdx.value
  const total = availableDates.value.length
  const start = Math.max(0, Math.min(idx - 3, total - 7))
  return availableDates.value.slice(start, start + 7)
})

function prevDay() {
  if (canPrev.value) selectedDate.value = availableDates.value[selectedDateIdx.value - 1]
}
function nextDay() {
  if (canNext.value) selectedDate.value = availableDates.value[selectedDateIdx.value + 1]
}

const stripMonthLabel = computed(() => {
  const dates = visibleDates.value
  if (!dates.length) return ''
  const first = new Date(`${dates[0]}T00:00:00`)
  const last  = new Date(`${dates[dates.length - 1]}T00:00:00`)
  if (first.getMonth() === last.getMonth())
    return `${MONTH_NAMES[first.getMonth()]} ${first.getFullYear()}`
  return `${MONTH_NAMES[first.getMonth()]} – ${MONTH_NAMES[last.getMonth()]} ${last.getFullYear()}`
})

const todayInStrip = computed(() => visibleDates.value.includes(todayStr))

function goToToday() {
  if (availableDates.value.includes(todayStr)) selectedDate.value = todayStr
}



const activities = ref([])
const TODOS_ICON = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`

const tabs = computed(() => ['Todos', ...activities.value.map(a => a.name)])
const currentTab = ref('')
const inscriptos = ref(new Set())
const activeSubsByTurno = ref(new Map()) // turno_id → { subscription_id, ends_on }
const turnosPendienteMensual = ref(new Map())
const turnosPendienteSingle = ref(new Map())
const myWaitlistByTurno = ref(new Map()) // turno_id → { entry_id }
const seniasRaw = ref([])
const turnosConSeniaPagada = computed(() => new Map(
  seniasRaw.value
    .filter(e => e.clase_date === selectedDate.value)
    .map(e => [e.turno_id, e])
))
const confirmadasRaw = ref([])
const turnosConClaseConfirmadaEnFecha = computed(() => new Map(
  confirmadasRaw.value
    .filter(e => e.clase_date === selectedDate.value)
    .map(e => [e.turno_id, e])
))
const avisoLleno = ref(null)
const errorMensaje = ref(null)
const loadingTurno = ref(null)
const confirmandoBaja = ref(null)

const loading = ref(false)
const turnos = ref([])

const tabIcons = computed(() => ({
  'Todos': TODOS_ICON,
  ...Object.fromEntries(activities.value.map(a => [a.name, ACTIVITY_ICONS[a.name] ?? DEFAULT_ACTIVITY_ICON])),
}))

const formatFechaSingle = (dateStr) => {
  if (!dateStr) return ''
  return new Intl.DateTimeFormat('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date(`${dateStr}T00:00:00`))
}

const loadTurnos = async (activityId) => {
  if (!activityId) return
  try {
    loading.value = true
    const nameMap = new Map(activities.value.map(a => [a.id, a.name]))
    const turnosRes = await turnoService.getTurnos({ activity_id: activityId })
    turnos.value = (turnosRes.data.items || []).map(t => mapTurno(t, nameMap))
  } catch (error) {
    console.error('Error al cargar turnos', error)
  } finally {
    loading.value = false
  }
}

const loadEnrollments = async () => {
  const [mySubscriptionRes, mySingleRes, myWaitlistRes] = await Promise.all([
    enrollmentService.getMySubscription(),
    enrollmentService.getMySingle(),
    enrollmentService.getMyWaitlist().catch(() => ({ data: [] })),
  ])

  const now = Date.now()
  const notExpired = (e) => !e.expires_at || new Date(e.expires_at).getTime() > now
  const chargeNotExpired = (s) =>
    !s.pending_charge?.expires_at || new Date(s.pending_charge.expires_at).getTime() > now

  const activeSubs = mySubscriptionRes.data.filter((s) => s.status === 'active')
  inscriptos.value = new Set(activeSubs.map((s) => s.turno_id))
  activeSubsByTurno.value = new Map(
    activeSubs.map((s) => [s.turno_id, { subscription_id: s.subscription_id, start_date: s.start_date, ends_on: s.ends_on }])
  )

  turnosPendienteMensual.value = new Map(
    mySubscriptionRes.data
      .filter((s) => s.status === 'pending' && s.pending_charge && chargeNotExpired(s))
      .map((s) => [s.turno_id, s])
  )

  turnosPendienteSingle.value = new Map(
    mySingleRes.data
      .filter((e) => e.status === 'pending' && notExpired(e))
      .map((e) => [e.turno_id, e])
  )

  seniasRaw.value = mySingleRes.data.filter(e => e.status === 'deposit_paid')
  confirmadasRaw.value = mySingleRes.data.filter(e => e.status === 'confirmed')

  myWaitlistByTurno.value = new Map(
    (myWaitlistRes.data || []).map(e => [e.turno_id, { entry_id: e.entry_id }])
  )
}

const loadAllClases = async () => {
  const entries = await Promise.all(
    turnos.value.map(async (turno) => {
      try {
        const res = await turnoService.getClasesByTurno(turno.id)
        const items = Array.isArray(res.data) ? res.data : res.data.items || []
        return [turno.id, items.map(c => ({
          id: c.id,
          rawDate: c.date,
          displayDate: new Intl.DateTimeFormat('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date(`${c.date}T00:00:00`)),
          dayLabel: (() => { const d = new Intl.DateTimeFormat('es-AR', { weekday: 'long' }).format(new Date(`${c.date}T00:00:00`)); return d.charAt(0).toUpperCase() + d.slice(1) })(),
          capacity: c.capacity ?? 0,
          occupied: c.enrolled ?? c.occupied ?? 0,
          availableSpots: Math.max((c.capacity ?? 0) - (c.enrolled ?? c.occupied ?? 0), 0),
          isActive: c.is_active ?? true,
        }))]
      } catch {
        return [turno.id, []]
      }
    })
  )
  classesByTurno.value = new Map(entries)
}

const mapTurno = (turno, nameMap) => ({
  id: turno.id,
  activityId: turno.activity_id,
  actividad: nameMap.get(turno.activity_id) ?? `Actividad #${turno.activity_id}`,
  nombre: (turno.name || turno.nombre || nameMap.get(turno.activity_id) || '').replace(/:/g, '').trim(),
  dia: turno.days?.join(' / ') || 'Sin días',
  days: turno.days || [],
  hora: turno.start_time,
  horaFin: turno.end_time,
  dur: `${turno.start_time} - ${turno.end_time}`,
  inst: turno.instructor_name || turno.instructor || 'Instructor',
  total: turno.capacity,
  ocup: turno.enrolled ?? 0,
  nivel: turno.level || 'Todos los niveles',
  descripcion: turno.description ?? '',
  sala: turno.room_number ?? turno.room ?? 'Sin sala',
  hasRemainingClasses: turno.has_remaining_classes ?? true,
  hasFutureClasses: turno.has_future_classes ?? true,
})

const loadAllTurnos = async () => {
  if (!activities.value.length) return
  try {
    loading.value = true
    const nameMap = new Map(activities.value.map(a => [a.id, a.name]))
    const results = await Promise.all(activities.value.map(a => turnoService.getTurnos({ activity_id: a.id })))
    turnos.value = results.flatMap(r => (r.data.items || []).map(t => mapTurno(t, nameMap)))
  } catch (error) {
    console.error('Error al cargar todos los turnos', error)
  } finally {
    loading.value = false
  }
}

watch(currentTab, async (newTab) => {
  selectedDate.value = localDateStr()
  if (newTab === 'Todos') {
    await loadAllTurnos()
    loadEnrollments()
    loadAllClases()
  } else {
    const activity = activities.value.find(a => a.name === newTab)
    if (activity) {
      await loadTurnos(activity.id)
      loadEnrollments()
      loadAllClases()
    }
  }
})

onMounted(async () => {
  try {
    loading.value = true

    const { activities: acts } = await getFormOptions()
    activities.value = acts

    await loadEnrollments()

    if (acts.length > 0) currentTab.value = 'Todos'
  } catch (error) {
    console.error('Error al cargar actividades', error)
    loading.value = false
  }
})

const availableDates = computed(() => {
  const today = new Date()
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const end = new Date(today.getFullYear(), today.getMonth() + 2, 0)
  const dates = []
  const cur = new Date(start)
  while (cur <= end) {
    dates.push(localDateStr(cur))
    cur.setDate(cur.getDate() + 1)
  }
  return dates
})

const currentTurnos = computed(() =>
  turnos.value.filter(t =>
    (classesByTurno.value.get(t.id) || []).some(c => c.rawDate === selectedDate.value)
  )
)

// --- Capacidad por FECHA seleccionada (no a nivel turno) ---
// La clase del día ya trae ocupación period-aware: un abonado con baja programada
// ocupa su mes pagado y libera el siguiente.
const claseSel = (t) => (classesByTurno.value.get(t.id) || []).find(c => c.rawDate === selectedDate.value)
const cupoTotal = (t) => claseSel(t)?.capacity ?? t.total
const cupoOcupado = (t) => { const c = claseSel(t); return c ? c.occupied : t.ocup }
const cupoLibre = (t) => Math.max(cupoTotal(t) - cupoOcupado(t), 0)
const sinCupo = (t) => cupoLibre(t) <= 0

// Para suscripción mensual: sin cupo solo si TODAS las clases del mes están llenas.
// Un abonado saliente con baja programada libera el mes siguiente, por eso hay que
// mirar el mes completo, no solo la fecha seleccionada.
const sinCupoEnMes = (t) => {
  const selDate = new Date(`${selectedDate.value}T00:00:00`)
  const mes = selDate.getMonth()
  const anio = selDate.getFullYear()
  const clasesDelMes = (classesByTurno.value.get(t.id) ?? []).filter(c => {
    const d = new Date(`${c.rawDate}T00:00:00`)
    return d.getMonth() === mes && d.getFullYear() === anio
  })
  if (!clasesDelMes.length) return true
  return clasesDelMes.every(c => c.availableSpots <= 0)
}

const pocosAbonosEnMes = (t) => {
  if (!t.total) return false
  return t.ocup > 0 && t.ocup / t.total >= 0.7
}

// ¿El cliente está suscripto para la fecha seleccionada? (sub cubre [start_date, ends_on])
const inscriptoEnFecha = (t) => {
  const sub = activeSubsByTurno.value.get(t.id)
  if (!sub) return false
  const d = selectedDate.value
  return (!sub.start_date || sub.start_date <= d) && (!sub.ends_on || d <= sub.ends_on)
}


const pct = (t) => {
  const tot = cupoTotal(t)
  return tot ? Math.min(Math.round((cupoOcupado(t) / tot) * 100), 100) : 0
}

const barColor = (t) => {
  const p = pct(t)
  return p >= 100 ? '#E53935' : p >= 75 ? '#FB8C00' : '#00897B'
}

const barBgColor = (t) => {
  const p = pct(t)
  return p >= 100
    ? 'rgba(229, 57, 53, 0.15)'
    : p >= 75
    ? 'rgba(251, 140, 0, 0.15)'
    : 'rgba(0, 137, 123, 0.15)'
}

const handleInscripcion = async (turno) => {
  if (inscriptoEnFecha(turno)) return
  if (sinCupoEnMes(turno)) {
    await handleJoinWaitlist(turno)
    return
  }

  loadingTurno.value = turno.id
  errorMensaje.value = null

  try {
    const { data } = await enrollmentService.createSubscription(turno.id)

    const s = new Set(inscriptos.value)
    s.add(turno.id)
    turno.ocup++
    inscriptos.value = s

    router.push({
      name: 'ticket',
      query: {
        kind:            'subscription',
        charge_id:       data.charge_id,
        subscription_id: data.subscription_id,
        actividad:       turno.actividad,
        descripcion:     turno.descripcion,
        dia:             turno.dia,
        hora:            turno.hora,
        duracion:        turno.dur,
        instructor:      turno.inst,
        nivel:           turno.nivel,
        numero:          data.subscription_id,
        amount:                  data.amount,
        original_amount:         data.original_amount,
        discount_deposit_single: data.discount_deposit_single,
        discount_full_classes:   data.discount_full_classes,
        expires_at:              data.expires_at,
      },
    })
  } catch (err) {
    if (err.response?.status === 409) {
      turno.ocup = turno.total
      errorMensaje.value = 'Otro usuario tomó el último lugar disponible. El cupo se liberará automáticamente si no completa el pago.'
    } else if (err.response?.status === 404) {
      errorMensaje.value = 'El turno no está disponible.'
    } else {
      errorMensaje.value = 'Ocurrió un error. Intentá de nuevo.'
    }
    avisoLleno.value = turno.id
    setTimeout(() => { avisoLleno.value = null; errorMensaje.value = null }, 5000)
  } finally {
    loadingTurno.value = null
  }
}

const formatBaja = (rawDate) => {
  if (!rawDate) return ''
  const d = new Date(`${rawDate}T00:00:00`)
  return new Intl.DateTimeFormat('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(d)
}

const handleBaja = async (turno) => {
  const sub = activeSubsByTurno.value.get(turno.id)
  if (!sub) return

  loadingTurno.value = turno.id
  try {
    const { data } = await enrollmentService.unsubscribe(sub.subscription_id)
    confirmandoBaja.value = null
    const next = new Map(activeSubsByTurno.value)
    next.set(turno.id, { ...sub, ends_on: data.ends_on })
    activeSubsByTurno.value = next
  } catch {
    confirmandoBaja.value = null
    errorMensaje.value = 'No se pudo dar de baja la suscripción. Intentá de nuevo.'
    avisoLleno.value = turno.id
    setTimeout(() => { avisoLleno.value = null; errorMensaje.value = null }, 5000)
  } finally {
    loadingTurno.value = null
  }
}

const continuarPago = (turno) => {
  const sub = turnosPendienteMensual.value.get(turno.id)
  if (!sub || !sub.pending_charge) return
  const charge = sub.pending_charge
  router.push({
    name: 'ticket',
    query: {
      kind:            'subscription',
      charge_id:       charge.charge_id,
      subscription_id: sub.subscription_id,
      actividad:       turno.actividad,
      descripcion:     turno.descripcion,
      dia:             turno.dia,
      hora:            turno.hora,
      duracion:        turno.dur,
      instructor:      turno.inst,
      nivel:           turno.nivel,
      numero:          sub.subscription_id,
      amount:          charge.amount,
      original_amount: charge.original_amount,
      expires_at:      charge.expires_at,
    },
  })
}

const continuarPagoSingle = (turno) => {
  const enrollment = turnosPendienteSingle.value.get(turno.id)
  if (!enrollment) return
  const d = new Date(`${enrollment.clase_date}T00:00:00`)
  const dayLabel = new Intl.DateTimeFormat('es-AR', { weekday: 'long' }).format(d)
  const displayDate = new Intl.DateTimeFormat('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(d)
  const claseStart = new Date(`${enrollment.clase_date}T${enrollment.start_time.padStart(5, '0')}:00`)
  router.push({
    name: 'ticket',
    query: {
      kind:          'single',
      enrollment_id: enrollment.enrollment_id,
      actividad:     turno.actividad,
      dia:           `${dayLabel.charAt(0).toUpperCase() + dayLabel.slice(1)} ${displayDate}`,
      duracion:      `${enrollment.start_time} - ${enrollment.end_time}`,
      instructor:    enrollment.instructor,
      numero:        enrollment.enrollment_id,
      amount:        enrollment.amount,
      precio_clase:  enrollment.amount,
      expires_at:    enrollment.expires_at,
      clase_start:   claseStart.toISOString(),
    },
  })
}

const handlePagarSaldo = async (turno) => {
  const enrollment = turnosConSeniaPagada.value.get(turno.id)
  if (!enrollment) return
  loadingTurno.value = turno.id
  try {
    const { data } = await enrollmentService.createBalancePreference(enrollment.enrollment_id)
    window.location.href = data.init_point
  } catch {
    errorMensaje.value = 'No se pudo iniciar el pago del saldo. Intentá de nuevo.'
    avisoLleno.value = turno.id
    setTimeout(() => { avisoLleno.value = null; errorMensaje.value = null }, 5000)
  } finally {
    loadingTurno.value = null
  }
}

const enListaDeEspera = (turno) => myWaitlistByTurno.value.has(turno.id)

const handleJoinWaitlist = async (turno) => {
  loadingTurno.value = turno.id
  errorMensaje.value = null
  try {
    const { data } = await enrollmentService.joinWaitlist(turno.id)
    const next = new Map(myWaitlistByTurno.value)
    next.set(turno.id, { entry_id: data.entry_id })
    myWaitlistByTurno.value = next
  } catch (err) {
    if (err.response?.status === 409) {
      errorMensaje.value = err.response.data?.detail || 'Ya estás en la lista de espera o tenés una suscripción activa.'
    } else {
      errorMensaje.value = 'Ocurrió un error. Intentá de nuevo.'
    }
    avisoLleno.value = turno.id
    setTimeout(() => { avisoLleno.value = null; errorMensaje.value = null }, 5000)
  } finally {
    loadingTurno.value = null
  }
}

const handleLeaveWaitlist = async (turno) => {
  const w = myWaitlistByTurno.value.get(turno.id)
  if (!w) return
  loadingTurno.value = turno.id
  try {
    await enrollmentService.leaveWaitlist(w.entry_id)
    const next = new Map(myWaitlistByTurno.value)
    next.delete(turno.id)
    myWaitlistByTurno.value = next
  } catch {
    errorMensaje.value = 'No se pudo salir de la lista. Intentá de nuevo.'
    avisoLleno.value = turno.id
    setTimeout(() => { avisoLleno.value = null; errorMensaje.value = null }, 5000)
  } finally {
    loadingTurno.value = null
  }
}

const handleInscripcionSingle = async (turno) => {
  const clases = classesByTurno.value.get(turno.id) || []
  const clase = clases.find(c => c.rawDate === selectedDate.value)
  if (!clase) return

  loadingTurno.value = turno.id
  errorMensaje.value = null

  try {
    // Verificar créditos disponibles antes de crear el enrollment
    let creditToOffer = null
    try {
      const { data: credits } = await enrollmentService.getCreditsForTurno(turno.id)
      if (credits.length > 0) creditToOffer = credits[0]
    } catch {}

    const d = new Date(`${clase.rawDate}T00:00:00`)
    const dayLabel = new Intl.DateTimeFormat('es-AR', { weekday: 'long' }).format(d)
    const displayDate = new Intl.DateTimeFormat('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(d)
    const claseStart = new Date(`${clase.rawDate}T${turno.hora.padStart(5, '0')}:00`)

    if (creditToOffer) {
      // Ir al ticket en modo "oferta de crédito" (sin crear enrollment aún)
      router.push({
        name: 'ticket',
        query: {
          kind:          'single',
          credit_offer:  'true',
          credit_id:     String(creditToOffer.id),
          credit_amount: String(creditToOffer.amount),
          clase_id:      String(clase.id),
          actividad:     turno.actividad,
          dia:           `${dayLabel.charAt(0).toUpperCase() + dayLabel.slice(1)} ${displayDate}`,
          duracion:      turno.dur,
          instructor:    turno.inst,
          clase_start:   claseStart.toISOString(),
        },
      })
      return
    }

    // Sin crédito: crear enrollment y redirigir al ticket normalmente
    const { data } = await enrollmentService.createSingle([clase.id])

    router.push({
      name: 'ticket',
      query: {
        kind:            'single',
        enrollment_id:   data.id,
        actividad:       turno.actividad,
        dia:             `${dayLabel.charAt(0).toUpperCase() + dayLabel.slice(1)} ${displayDate}`,
        duracion:        turno.dur,
        instructor:      turno.inst,
        numero:          data.id,
        amount:          data.amount,
        precio_clase:    data.amount,
        expires_at:      data.expires_at,
        clase_start:     claseStart.toISOString(),
      },
    })
  } catch (err) {
    if (err.response?.status === 409) {
      errorMensaje.value = 'No hay cupo disponible para esta clase.'
    } else {
      errorMensaje.value = 'Ocurrió un error. Intentá de nuevo.'
    }
    avisoLleno.value = turno.id
    setTimeout(() => { avisoLleno.value = null; errorMensaje.value = null }, 5000)
  } finally {
    loadingTurno.value = null
  }
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

.no-turnos-msg {
  text-align: center;
  padding: 48px 20px;
  color: #90a4ae;
  font-size: 15px;
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

.sin-clases-aviso {
  background-color: #f5f5f5;
  color: #78909c;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.5;
  text-align: center;
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


.senia-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #F57C00;
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

.day-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
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

.lazo-clase {
  position: absolute;
  top: 0;
  left: 0;
  width: 52px;
  height: 52px;
  background: #00897b;
  clip-path: polygon(0 0, 100% 0, 0 100%);
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  padding: 7px 0 0 7px;
  color: white;
  pointer-events: none;
}

.lazo-star {
  display: inline-block;
  font-size: 16px;
  transform: rotate(20deg);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.85), 0 1px 3px rgba(0, 0, 0, 0.2);
  line-height: 1;
}

.periodo-chip {
  display: inline-block;
  margin-top: 6px;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 999px;
  background-color: rgba(69, 90, 100, 0.09);
  color: #546e7a;
  letter-spacing: 0.04em;
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

.marquee-wrapper {
  overflow: hidden;
  white-space: nowrap;
  margin: 0 -24px -24px -24px;
  padding: 7px 0;
  background: rgba(0, 137, 123, 0.06);
  border-top: 1px solid rgba(0, 137, 123, 0.1);
}

.marquee-text {
  display: inline-block;
  padding-left: 100%;
  white-space: nowrap;
  animation: marquee-scroll 8s linear infinite;
  font-size: 11px;
  font-weight: 700;
  color: #00897b;
  letter-spacing: 0.05em;
}

@keyframes marquee-scroll {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-100%); }
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
  justify-content: flex-end;
  margin-bottom: 8px;
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
  background: #FFE0B2;
  color: #E65100;
  box-shadow: 0 10px 18px rgba(255, 152, 0, 0.12);
}

.accion-btn.espera:hover:not(:disabled) {
  background: #FFCC80;
  transform: translateY(-1px);
}

.espera-info {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 600;
  color: #e65100;
  text-align: center;
  padding: 6px 10px;
  background: #FFF3E0;
  border: 1px solid rgba(255, 152, 0, 0.3);
  border-radius: 8px;
}

.pago-pendiente-info {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  color: #78909c;
  text-align: center;
  padding: 6px 10px;
  background: rgba(245, 124, 0, 0.07);
  border: 1px solid rgba(245, 124, 0, 0.2);
  border-radius: 8px;
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

.baja-btn {
  width: 100%;
  padding: 12px 0;
  border-radius: 999px;
  border: 1.5px solid #E53935;
  background: transparent;
  color: #E53935;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.18s ease;
}
.baja-btn:hover { background: rgba(229, 57, 53, 0.08); }
.baja-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.baja-confirm-msg {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  color: #546e7a;
  text-align: center;
  line-height: 1.4;
}

.baja-confirm-btns {
  display: flex;
  gap: 8px;
}

.baja-btn--confirmar {
  flex: 1;
}

.baja-btn--cancelar {
  flex: 1;
  border-color: #90a4ae;
  color: #546e7a;
}
.baja-btn--cancelar:hover { background: rgba(144, 164, 174, 0.1); }

.baja-info {
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  background: #FFF3E0;
  color: #E65100;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  line-height: 1.4;
}

.secondary-btn--espera {
  border-color: #FFB74D;
  color: #E65100;
}

.secondary-btn--espera:hover {
  background: rgba(255, 224, 178, 0.5);
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

.date-strip-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.strip-month {
  font-size: 12px;
  font-weight: 600;
  color: #78909c;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.strip-hoy-btn {
  font-size: 11px;
  font-weight: 700;
  color: #00897b;
  background: rgba(0, 137, 123, 0.08);
  border: 1px solid rgba(0, 137, 123, 0.2);
  border-radius: 20px;
  padding: 3px 10px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.strip-hoy-btn:hover {
  background: rgba(0, 137, 123, 0.15);
  border-color: rgba(0, 137, 123, 0.4);
}

/* MOBILE */
@media (max-width: 768px) {
  .header { padding: 0 18px; }
  .header-inner { height: 64px; }
  .main { padding: 20px 18px 50px; }
  h1 { font-size: 1.9rem; }
  .grid { grid-template-columns: 1fr; }
}

/* DATE STRIP */
.date-strip-nav {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 28px;
}

.strip-arrow {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1.5px solid rgba(0, 137, 123, 0.2);
  background: rgba(255, 255, 255, 0.88);
  color: #00897b;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.18s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.strip-arrow:hover {
  background: #00897b;
  color: white;
  border-color: #00897b;
  box-shadow: 0 4px 12px rgba(0,137,123,0.22);
}

.strip-arrow.invisible {
  opacity: 0;
  pointer-events: none;
}

.date-strip {
  display: flex;
  flex: 1;
  gap: 8px;
}

.date-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-width: 0;
  padding: 10px 4px 8px;
  border-radius: 8px;
  border: 1.5px solid rgba(0, 137, 123, 0.13);
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(8px);
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}


.date-card:hover {
  border-color: rgba(0, 137, 123, 0.35);
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 137, 123, 0.13);
}

.date-card.active {
  background: #00897b;
  border-color: #00897b;
  box-shadow: 0 8px 20px rgba(0, 137, 123, 0.28);
  transform: translateY(-3px);
}

.dc-day {
  font-size: 10px;
  font-weight: 600;
  color: #90a4ae;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  line-height: 1;
}

.dc-num {
  font-size: 19px;
  font-weight: 700;
  color: #37474f;
  line-height: 1.15;
}

.dc-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #00897b;
  margin-top: 3px;
}

.date-card.active .dc-day  { color: rgba(255, 255, 255, 0.75); }
.date-card.active .dc-num  { color: white; }
.date-card.active .dc-dot  { background: white; }

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

.error-aviso {
  margin-top: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  background-color: #fff5f5;
  color: #c0392b;
  border: 1px solid #fecaca;
  font-size: 13px;
  font-weight: 500;
}
</style>