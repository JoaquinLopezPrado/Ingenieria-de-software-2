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
      <div class="date-strip-nav">
        <button
          class="strip-arrow"
          :class="{ invisible: !canScrollLeft }"
          type="button"
          aria-label="Anterior"
          @click="stripPage--"
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
            <span class="dc-label">{{ dateDay(date) }} {{ dateNum(date) }}</span>
          </button>
        </div>

        <button
          class="strip-arrow"
          :class="{ invisible: !canScrollRight }"
          type="button"
          aria-label="Siguiente"
          @click="stripPage++"
        >&#8250;</button>
      </div>

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
          :class="{ inscripto: inscriptos.has(turno.id), 'sin-clases': !turno.hasRemainingClasses }"
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
              <div class="dia">{{ turno.dur }}</div>
              <div class="day-chips">
                <span
                  v-for="day in turno.days"
                  :key="day"
                  class="day-chip"
                >{{ DAY_LABELS[day] ?? day }}</span>
              </div>
            </div>
            <span v-if="turno.hasRemainingClasses && turno.ocup >= turno.total" class="agotado-badge">
              AGOTADO
            </span>
            <span v-else-if="turno.hasRemainingClasses && pct(turno) >= 70" class="ultimos-badge">
              ¡Últimos lugares!
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
              <span class="cap-text" :style="{ color: barColor(turno) }">
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
                Suscripción pendiente
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

            <div v-else-if="turnosConSeniaPagada.has(turno.id)" class="acciones-card">
              <div class="senia-chip">
                <span>Seña abonada · completá el pago antes de la clase</span>
                <button class="btn-completar-pago" type="button" @click="pagarSaldoSenia(turno)">
                  Completar pago (70% restante)
                </button>
              </div>
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

              <div v-if="turnosConClaseSuelta.has(turno.id)" class="clase-suelta-chip">
                Tenés inscripciones a clases individuales
              </div>

              <button
                class="secondary-btn"
                :class="{ 'secondary-btn--espera': turno.ocup >= turno.total }"
                type="button"
                @click="openModal(turno)"
              >
                {{ turno.ocup >= turno.total
                  ? 'Anotarse en lista de espera para clase individual'
                  : 'Ver clases individuales' }}
              </button>
            </div>
          </template>

          <div v-if="avisoLleno === turno.id && errorMensaje" class="error-aviso">
            {{ errorMensaje }}
          </div>

        </div>
      </div>

      <div v-if="!loading && currentTurnos.length === 0" class="no-turnos-msg">
        No hay turnos disponibles para este día.
      </div>

    </div>

    <!-- Modal clases individuales -->
    <div v-if="modalTurno" class="modal-overlay" @click.self="closeModal">
      <div class="modal-drawer">
        <div class="modal-header">
          <div>
            <h2 class="modal-title">Clases individuales</h2>
            <p class="modal-subtitle">{{ modalTurno.actividad }} · {{ modalTurno.dur }}</p>
          </div>
          <button class="modal-close" type="button" @click="closeModal">✕</button>
        </div>

        <div class="modal-body">
          <div v-if="modalClases.length === 0" class="modal-empty">
            No hay clases disponibles para este turno.
          </div>
          <div v-else class="modal-options">
            <button
              v-for="clase in modalClases"
              :key="clase.id"
              class="modal-option"
              :class="{ selected: modalSelectedIds.has(clase.id), enrolled: clase.isEnrolled }"
              :disabled="clase.isEnrolled"
              type="button"
              @click="!clase.isEnrolled && toggleModalClass(clase.id)"
            >
              <div class="mo-header">
                <div>
                  <div class="mo-date">{{ clase.displayDate }}</div>
                  <div class="mo-day">{{ clase.dayLabel }}</div>
                </div>
                <span v-if="clase.isEnrolled" class="mo-badge mo-badge--inscripto">Inscripto</span>
                <span v-else-if="modalSelectedIds.has(clase.id)" class="mo-badge mo-badge--sel">✓ Seleccionado</span>
                <span v-else class="mo-badge mo-badge--ok">Disponible</span>
              </div>
              <div class="mo-cap-row">
                <span class="mo-cap-text" :style="{ color: barColor(clase) }">
                  {{ clase.availableSpots === 0 ? 'Sin lugares' : `${clase.availableSpots} lugar${clase.availableSpots !== 1 ? 'es' : ''}` }}
                </span>
                <span class="mo-cap-num" :style="{ color: barColor(clase) }">{{ clase.occupied }}/{{ clase.total }}</span>
              </div>
              <div class="bar-bg" :style="{ background: barBgColor(clase) }">
                <div class="bar-fill" :style="{ width: pct(clase) + '%', background: barColor(clase) }"></div>
              </div>
            </button>
          </div>
        </div>

        <div v-if="modalSubmitError" class="modal-error">{{ modalSubmitError }}</div>

        <div class="modal-footer">
          <button class="back-btn" type="button" @click="closeModal" :disabled="modalSubmitting">Cancelar</button>
          <button
            class="submit-btn"
            type="button"
            :disabled="modalSelectedIds.size === 0 || modalSubmitting"
            @click="submitModal"
          >
            {{ modalSubmitting
              ? 'Procesando...'
              : modalSelectedIds.size === 0
                ? 'Seleccioná una clase'
                : `Inscribirse a ${modalSelectedIds.size} clase${modalSelectedIds.size !== 1 ? 's' : ''}` }}
          </button>
        </div>
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
const dateNum = (str) => { const d = new Date(`${str}T00:00:00`); return `${d.getDate()}/${d.getMonth() + 1}` }

const localDateStr = (d = new Date()) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

const selectedDate = ref(localDateStr())
const classesByTurno = ref(new Map())
const enrolledClaseIds = ref(new Set())

const stripPage = ref(0)
const canScrollLeft = computed(() => stripPage.value > 0)
const canScrollRight = computed(() => (stripPage.value + 1) * 7 < availableDates.value.length)
const visibleDates = computed(() => availableDates.value.slice(stripPage.value * 7, stripPage.value * 7 + 7))


const modalTurno = ref(null)
const modalSelectedIds = ref(new Set())
const modalSubmitting = ref(false)
const modalSubmitError = ref('')

const activities = ref([])
const TODOS_ICON = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`

const tabs = computed(() => ['Todos', ...activities.value.map(a => a.name)])
const currentTab = ref('')
const inscriptos = ref(new Set())
const turnosConClaseSuelta = ref(new Map())
const turnosPendienteMensual = ref(new Map())
const turnosPendienteSingle = ref(new Map())
const turnosConSeniaPagada = ref(new Map())
const avisoLleno = ref(null)
const errorMensaje = ref(null)
const loadingTurno = ref(null)

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
  const [mySubscriptionRes, mySingleRes] = await Promise.all([
    enrollmentService.getMySubscription(),
    enrollmentService.getMySingle(),
  ])

  const now = Date.now()
  const notExpired = (e) => !e.expires_at || new Date(e.expires_at).getTime() > now

  inscriptos.value = new Set(
    mySubscriptionRes.data
      .filter((e) => e.status === 'confirmed')
      .map((e) => e.turno_id)
  )

  turnosPendienteMensual.value = new Map(
    mySubscriptionRes.data
      .filter((e) => e.status === 'pending' && notExpired(e))
      .map((e) => [e.turno_id, e])
  )

  turnosConClaseSuelta.value = new Map(
    mySingleRes.data
      .filter((e) => e.status === 'confirmed' || (e.status === 'pending' && notExpired(e)) || e.status === 'deposit_paid')
      .map((e) => [e.turno_id, e])
  )

  turnosPendienteSingle.value = new Map(
    mySingleRes.data
      .filter((e) => e.status === 'pending' && notExpired(e))
      .map((e) => [e.turno_id, e])
  )

  turnosConSeniaPagada.value = new Map(
    mySingleRes.data
      .filter((e) => e.status === 'deposit_paid')
      .map((e) => [e.turno_id, e])
  )

  enrolledClaseIds.value = new Set(
    mySingleRes.data
      .filter((e) => e.status === 'confirmed' || (e.status === 'pending' && notExpired(e)) || e.status === 'deposit_paid')
      .map((e) => e.clase_id)
      .filter(Boolean)
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
  stripPage.value = 0
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

const modalClases = computed(() => {
  if (!modalTurno.value) return []
  return (classesByTurno.value.get(modalTurno.value.id) || [])
    .filter(c => c.isActive && (enrolledClaseIds.value.has(c.id) || c.availableSpots > 0))
    .map(c => ({ ...c, isEnrolled: enrolledClaseIds.value.has(c.id), total: c.capacity }))
    .sort((a, b) => a.rawDate.localeCompare(b.rawDate))
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
  if (inscriptos.value.has(turno.id)) return

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
        enrollment_id:   data.id,
        actividad:       turno.actividad,
        descripcion:     turno.descripcion,
        dia:             turno.dia,
        hora:            turno.hora,
        duracion:        turno.dur,
        instructor:      turno.inst,
        nivel:           turno.nivel,
        numero:          data.id,
        amount:                data.amount,
        original_amount:       data.original_amount,
        discount_full_classes: data.discount_full_classes,
        expires_at:            data.expires_at,
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

const continuarPago = (turno) => {
  const enrollment = turnosPendienteMensual.value.get(turno.id)
  if (!enrollment) return
  router.push({
    name: 'ticket',
    query: {
      enrollment_id:         enrollment.enrollment_id,
      actividad:             turno.actividad,
      descripcion:           turno.descripcion,
      dia:                   turno.dia,
      hora:                  turno.hora,
      duracion:              turno.dur,
      instructor:            turno.inst,
      nivel:                 turno.nivel,
      numero:                enrollment.enrollment_id,
      amount:                enrollment.amount,
      original_amount:       enrollment.original_amount,
      discount_full_classes: enrollment.discount_full_classes,
      expires_at:            enrollment.expires_at,
    },
  })
}

const continuarPagoSingle = (turno) => {
  const enrollment = turnosPendienteSingle.value.get(turno.id)
  if (!enrollment) return
  const d = new Date(`${enrollment.clase_date}T00:00:00`)
  const dayLabel = new Intl.DateTimeFormat('es-AR', { weekday: 'long' }).format(d)
  const displayDate = new Intl.DateTimeFormat('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(d)
  router.push({
    name: 'ticket',
    query: {
      enrollment_id: enrollment.enrollment_id,
      actividad:     turno.actividad,
      dia:           `${dayLabel.charAt(0).toUpperCase() + dayLabel.slice(1)} ${displayDate}`,
      duracion:      `${enrollment.start_time} - ${enrollment.end_time}`,
      instructor:    enrollment.instructor,
      numero:        enrollment.enrollment_id,
      amount:        enrollment.amount,
      precio_clase:  enrollment.amount,
      expires_at:    enrollment.expires_at,
    },
  })
}

const pagarSaldoSenia = async (turno) => {
  const enrollment = turnosConSeniaPagada.value.get(turno.id)
  if (!enrollment) return
  try {
    const { data } = await enrollmentService.createBalancePreference(enrollment.enrollment_id)
    window.location.href = data.init_point
  } catch {
    alert('No se pudo iniciar el pago del saldo. Intentá de nuevo.')
  }
}

const openModal = (turno) => {
  modalTurno.value = turno
  modalSubmitError.value = ''
  const preselect = selectedDate.value
    ? (classesByTurno.value.get(turno.id) || []).find(c => c.rawDate === selectedDate.value && !enrolledClaseIds.value.has(c.id))
    : null
  modalSelectedIds.value = new Set(preselect ? [preselect.id] : [])
}

const closeModal = () => {
  modalTurno.value = null
  modalSelectedIds.value = new Set()
  modalSubmitError.value = ''
}

const toggleModalClass = (id) => {
  modalSubmitError.value = ''
  const s = new Set(modalSelectedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  modalSelectedIds.value = s
}

const submitModal = async () => {
  if (modalSelectedIds.value.size === 0) return
  const turno = modalTurno.value
  modalSubmitting.value = true
  modalSubmitError.value = ''
  try {
    const clase_ids = [...modalSelectedIds.value]
    const { data } = await enrollmentService.createSingle(clase_ids)
    const count = clase_ids.length
    const selected = modalClases.value.filter(c => modalSelectedIds.value.has(c.id))
    const diaLabel = count === 1
      ? `${selected[0].dayLabel} ${selected[0].displayDate}`
      : `${count} clases`
    closeModal()
    router.push({
      name: 'ticket',
      query: {
        enrollment_id:   data.id,
        enrollment_type: 'single',
        actividad:       turno.actividad,
        dia:             diaLabel,
        duracion:        turno.dur,
        instructor:      turno.inst,
        numero:          data.id,
        amount:          data.amount,
        precio_clase:    data.amount,
        expires_at:      data.expires_at,
      },
    })
  } catch (error) {
    if (error.response?.status === 409) {
      const msg = error.response?.data?.errors?.general || error.response?.data?.detail
      modalSubmitError.value = (msg && !msg.includes('cupo') && !msg.includes('lugar'))
        ? msg
        : 'Una de las clases ya no tiene cupo. El lugar se liberará si no se completa el pago.'
    } else {
      modalSubmitError.value = 'Ocurrió un error al generar la inscripción.'
    }
  } finally {
    modalSubmitting.value = false
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

.card.sin-clases {
  opacity: 0.6;
  filter: grayscale(30%);
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

.ultimos-badge {
  font-size: 10px;
  font-weight: 800;
  padding: 5px 11px;
  border-radius: 999px;
  background: #FFF3E0;
  color: #E65100;
  letter-spacing: 0.06em;
  white-space: nowrap;
  flex-shrink: 0;
  border: 1px solid #FFE0B2;
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

.secondary-btn--espera {
  border-color: #F57C00;
  color: #F57C00;
}

.secondary-btn--espera:hover {
  background: rgba(245, 124, 0, 0.08);
}

.clase-suelta-chip {
  width: 100%;
  padding: 10px 14px;
  border-radius: 10px;
  background: #E8F5E9;
  border: 1px solid #A5D6A7;
  color: #2E7D32;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
}

.senia-chip {
  width: 100%;
  padding: 10px 14px;
  border-radius: 10px;
  background: #FFF8E1;
  border: 1px solid #FFD54F;
  color: #E65100;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
}

.btn-completar-pago {
  padding: 8px 20px;
  border-radius: 99px;
  border: none;
  background: #009EE3;
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-completar-pago:hover {
  background: #0080C0;
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
  padding: 7px 4px;
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

.dc-label {
  font-size: 12px;
  font-weight: 700;
  color: #546e7a;
  white-space: nowrap;
}

.date-card.active .dc-label { color: white; }

/* MODAL */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.modal-drawer {
  width: 100%;
  max-width: 680px;
  max-height: 85vh;
  background: #fff;
  border-radius: 28px 28px 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 -10px 40px rgba(0,0,0,0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px 24px 16px;
  border-bottom: 1px solid rgba(0,137,123,0.08);
  flex-shrink: 0;
}

.modal-title {
  margin: 0 0 4px;
  font-size: 1.3rem;
  font-weight: 900;
  color: #00695c;
}

.modal-subtitle {
  margin: 0;
  font-size: 13px;
  color: #78909c;
  font-weight: 500;
}

.modal-close {
  background: none;
  border: none;
  font-size: 18px;
  color: #90a4ae;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  line-height: 1;
  flex-shrink: 0;
}

.modal-close:hover { background: #f5f5f5; color: #455a64; }

.modal-body {
  overflow-y: auto;
  padding: 16px 24px;
  flex: 1;
}

.modal-empty {
  color: #90a4ae;
  font-size: 14px;
  padding: 20px 0;
  text-align: center;
}

.modal-options {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}

.modal-option {
  border: 1.5px solid rgba(0,137,123,0.1);
  border-radius: 20px;
  background: rgba(255,255,255,0.9);
  padding: 18px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}

.modal-option:hover:not(:disabled) {
  border-color: #18b4a3;
  transform: translateY(-2px);
}

.modal-option.selected {
  border: 2px solid #00897b;
  background: rgba(224,242,241,0.5);
}

.modal-option.enrolled {
  opacity: 0.65;
  cursor: default;
  background: rgba(232,245,233,0.5);
}

.mo-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.mo-date {
  font-size: 1rem;
  font-weight: 800;
  color: #1f2937;
}

.mo-day {
  font-size: 12px;
  color: #78909c;
  margin-top: 2px;
}

.mo-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  white-space: nowrap;
  flex-shrink: 0;
}

.mo-badge--ok       { background: rgba(0,137,123,0.1); color: #00695c; }
.mo-badge--sel      { background: rgba(0,137,123,0.15); color: #00695c; }
.mo-badge--inscripto { background: #e8f5e9; color: #2e7d32; }

.mo-cap-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.mo-cap-text { font-size: 12px; font-weight: 500; }
.mo-cap-num  { font-size: 12px; font-weight: 700; }

.modal-error {
  margin: 0 24px;
  padding: 10px 14px;
  border-radius: 10px;
  background: #fff5f5;
  color: #c0392b;
  border: 1px solid #fecaca;
  font-size: 13px;
  font-weight: 500;
  flex-shrink: 0;
}

.modal-footer {
  display: flex;
  gap: 10px;
  padding: 16px 24px 24px;
  border-top: 1px solid rgba(0,137,123,0.08);
  flex-shrink: 0;
}

.back-btn {
  flex-shrink: 0;
  padding: 12px 20px;
  border-radius: 12px;
  border: 1.5px solid rgba(0,137,123,0.25);
  background: transparent;
  color: #546e7a;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.18s, border-color 0.18s;
}
.back-btn:hover:not(:disabled) {
  background: rgba(0,137,123,0.06);
  border-color: rgba(0,137,123,0.45);
}
.back-btn:disabled { opacity: 0.45; cursor: not-allowed; }

.submit-btn {
  flex: 1;
  padding: 12px 20px;
  border-radius: 12px;
  border: none;
  background: #00897b;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(0,137,123,0.28);
  transition: background 0.18s, box-shadow 0.18s, opacity 0.18s;
}
.submit-btn:hover:not(:disabled) {
  background: #00796b;
  box-shadow: 0 6px 18px rgba(0,137,123,0.38);
}
.submit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  box-shadow: none;
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