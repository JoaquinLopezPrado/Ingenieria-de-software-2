<script setup lang="ts">
/**
 * CalendarioClasesView — HU ACT-10.01: Consultar clases de un turno específico
 * ---------------------------------------------------------------------------
 * Muestra las clases de un turno en un calendario FullCalendar (Mes/Semana/Día).
 *
 * Escenarios cubiertos:
 *   1. Visualización exitosa en vista mes (apertura en mes/año del turno)
 *   2. Cambio a vista semanal
 *   3. Cambio a vista diaria
 *   4. Modal con detalle de clase activa + botón "Suspender clase"
 *   5. Modal con detalle de clase suspendida (sin botón suspender)
 *   6. Acceso denegado por rol no autorizado
 *
 * Endpoint real: GET /api/v1/turnos/:id/clases — ya integrado con el backend.
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import type { CalendarOptions, EventClickArg } from '@fullcalendar/core'
import esLocale from '@fullcalendar/core/locales/es'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import type { Clase } from '@/services/sessionService'
import { useAuthStore } from '@/stores/authStore'

// ─── Ruta y parámetros ────────────────────────────────────────────────────────

const route  = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const turnoId     = Number(route.params.id)
const month       = Number(route.query.month)     || new Date().getMonth() + 1
const year        = Number(route.query.year)      || new Date().getFullYear()
const turnoDesc   = (route.query.desc      as string) || ''
const actividad   = (route.query.actividad as string) || ''
const turnoActive = route.query.turno_active !== '0'   // false solo si se pasó explícitamente '0'
const initialDate = `${year}-${String(month).padStart(2, '0')}-01`

// ─── Guard de rol ─────────────────────────────────────────────────────────────
// Si el store tiene datos de usuario, verificamos que sea admin.
// Si no los tiene (ej: refresh de página), dejamos pasar y el API decidirá.

const isAdmin = computed(() => {
  const u = authStore.user
  if (!u) return true
  return u.role === 'admin' || u.roles?.includes('admin') || u.role === 'Administrador'
})

// ─── Estado ───────────────────────────────────────────────────────────────────

const clases    = ref<Clase[]>([])
const isLoading = ref(true)
const loadError = ref('')

// Modal
const modalOpen    = ref(false)
const selectedClase = ref<Clase | null>(null)

// ─── Helpers de formato ───────────────────────────────────────────────────────

const DIAS_ES = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
const MESES_ES = [
  'Enero','Febrero','Marzo','Abril','Mayo','Junio',
  'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre',
]

// Azul índigo para activas — visualmente distinto del verde teal del sistema
const COLOR_ACTIVA     = '#16a34a'   // verde (mismo familia, distinto del teal #11998e de los botones)
const COLOR_SUSPENDIDA = '#9ca3af'

/**
 * El backend serializa la hora como "H:MM" (sin zero-pad en la hora, ej: "8:00").
 * FullCalendar necesita ISO 8601 estricto: "08:00". Sin esto, new Date("...T8:00:00")
 * devuelve Invalid Date y el evento se descarta silenciosamente.
 */
function padTime(t: string): string {
  const [h, m] = t.split(':')
  return `${String(h).padStart(2, '0')}:${m ?? '00'}`
}

/** "2026-05-04" → "Lunes 4 de Mayo de 2026" */
function formatFechaLarga(fecha: string): string {
  const [y, m, d] = fecha.split('-').map(Number)
  const year = y ?? new Date().getFullYear()
  const month = m ?? 1
  const day = d ?? 1
  const diaSemana  = DIAS_ES[new Date(year, month - 1, day).getDay()]  ?? ''
  const mesNombre  = MESES_ES[month - 1]                   ?? ''
  return `${diaSemana} ${day} de ${mesNombre} de ${year}`
}

/** Mes/año del turno para el encabezado */
const periodoLabel = computed(() =>
  `${MESES_ES[month - 1] ?? ''} ${year}`
)

// ─── Eventos para FullCalendar ────────────────────────────────────────────────

const fcEvents = computed(() =>
  clases.value.map(c => {
    // Si el turno está inactivo, todas sus clases se muestran en gris
    // independientemente del estado individual de cada clase.
    const color = !turnoActive
      ? COLOR_SUSPENDIDA
      : c.is_active ? COLOR_ACTIVA : COLOR_SUSPENDIDA
    return {
      id:               String(c.id),
      title:            `${c.start_time} – ${c.end_time}`,
      start:            `${c.date}T${padTime(c.start_time)}:00`,
      end:              `${c.date}T${padTime(c.end_time)}:00`,
      backgroundColor:  color,
      borderColor:      color,
      textColor:        '#ffffff',
      extendedProps:    { clase: c },
    }
  })
)

// ─── Opciones de FullCalendar ─────────────────────────────────────────────────

const calendarOptions = computed<CalendarOptions>(() => ({
  plugins:     [dayGridPlugin, timeGridPlugin, interactionPlugin],
  locale:      esLocale,
  initialView: 'dayGridMonth',
  initialDate,
  headerToolbar: {
    left:   'prev,next today',
    center: 'title',
    right:  'dayGridMonth,timeGridWeek,timeGridDay',
  },
  buttonText: {
    today:  'Hoy',
    month:  'Mes',
    week:   'Semana',
    day:    'Día',
  },
  events:      fcEvents.value,
  eventClick:  handleEventClick,
  height:      'auto',
  // En vista mes mostrar el título del evento (horario)
  eventDisplay: 'block',
}))

// ─── Click en evento ──────────────────────────────────────────────────────────

function handleEventClick(info: EventClickArg) {
  info.jsEvent.preventDefault()
  selectedClase.value = info.event.extendedProps.clase as Clase
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
  selectedClase.value = null
}

function handleSuspender() {
  if (!selectedClase.value) return
  console.log('[ACT-11.01] Suspender clase id:', selectedClase.value.id)
  // TODO: implementar lógica de suspensión en HU ACT-11.01
}

// ─── Carga inicial ────────────────────────────────────────────────────────────

onMounted(async () => {
  if (!isAdmin.value) {
    isLoading.value = false
    return
  }
  try {
    clases.value = await getClasesByTurno(turnoId)
  } catch (e: unknown) {
    const status = (e as { response?: { status?: number } })?.response?.status
    if (status === 403) {
      // El API confirmó que no hay permisos — forzamos la pantalla de acceso denegado
      // Reutilizamos el flag isAdmin a través de loadError especial
      loadError.value = '__forbidden__'
    } else {
      loadError.value = 'No se pudieron cargar las clases. Verificá que el servidor esté corriendo.'
    }
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <!-- ── Encabezado ── -->
      <div class="page-header">
        <div class="header-left">
          <button class="btn-back" @click="router.push({ name: 'turnos-grilla' })" title="Volver a la grilla">
            ← Volver
          </button>
          <div>
            <p class="page-actividad" v-if="actividad">{{ actividad }}</p>
            <h1 class="page-title">
              Clases del turno
              <span v-if="turnoDesc" class="title-desc">— {{ turnoDesc }}</span>
            </h1>
            <p class="page-subtitle">Calendario de clases · {{ periodoLabel }}</p>
          </div>
        </div>

        <!-- Leyenda de colores -->
        <div class="legend">
          <template v-if="turnoActive">
            <span class="legend-item">
              <span class="legend-dot" style="background:#16a34a"></span> Activa
            </span>
            <span class="legend-item">
              <span class="legend-dot" style="background:#9ca3af"></span> Suspendida
            </span>
          </template>
          <template v-else>
            <span class="legend-item">
              <span class="legend-dot" style="background:#9ca3af"></span> Turno inactivo
            </span>
          </template>
        </div>
      </div>

      <!-- ── Escenario 6: Sin permisos ── -->
      <div v-if="!isAdmin || loadError === '__forbidden__'" class="state-card state-forbidden">
        <div class="state-icon">⛔</div>
        <h2 class="state-title">No tiene permisos para acceder a esta sección</h2>
        <p class="state-desc">Esta sección es exclusiva para administradores.</p>
        <button class="btn-secondary" @click="router.push({ name: 'home' })">
          Volver al inicio
        </button>
      </div>

      <!-- ── Error de carga genérico ── -->
      <div v-else-if="loadError" class="state-card state-error">
        <div class="state-icon">⚠</div>
        <h2 class="state-title">Error al cargar las clases</h2>
        <p class="state-desc">{{ loadError }}</p>
        <button class="btn-secondary" @click="router.go(0)">Reintentar</button>
      </div>

      <!-- ── Skeleton mientras carga ── -->
      <div v-else-if="isLoading" class="skeleton-wrapper" aria-label="Cargando clases...">
        <div class="skeleton-header"></div>
        <div class="skeleton-calendar"></div>
      </div>

      <!-- ── Calendario ── -->
      <div v-else class="calendar-container">
        <FullCalendar :options="calendarOptions" />
      </div>

    </div>

    <!-- ══════════════════════════════════════════
         MODAL DE DETALLE DE CLASE
         Escenario 4 (activa) y 5 (suspendida)
    ══════════════════════════════════════════ -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="modalOpen && selectedClase" class="modal-overlay" @click.self="closeModal">
          <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">

            <!-- Encabezado del modal -->
            <div class="modal-header" :class="selectedClase.is_active ? 'modal-header--active' : 'modal-header--suspended'">
              <h2 id="modal-title" class="modal-title">Detalle de clase</h2>
              <button class="modal-close" @click="closeModal" aria-label="Cerrar modal">×</button>
            </div>

            <!-- Cuerpo del modal -->
            <div class="modal-body">
              <dl class="detail-list">

                <div class="detail-row">
                  <dt>Fecha</dt>
                  <dd>{{ formatFechaLarga(selectedClase.date) }}</dd>
                </div>

                <div class="detail-row">
                  <dt>Horario</dt>
                  <dd>{{ selectedClase.start_time }} a {{ selectedClase.end_time }}</dd>
                </div>

                <div class="detail-row">
                  <dt>Capacidad</dt>
                  <dd>{{ selectedClase.capacity }} lugares</dd>
                </div>

                <div class="detail-row">
                  <dt>Inscriptos</dt>
                  <dd>
                    {{ selectedClase.enrolled }}
                    <span class="inscriptos-bar">
                      <span
                        class="inscriptos-fill"
                        :style="{ width: Math.min(100, (selectedClase.enrolled / selectedClase.capacity) * 100) + '%' }"
                      ></span>
                    </span>
                  </dd>
                </div>

                <div class="detail-row">
                  <dt>Estado</dt>
                  <dd>
                    <span :class="['status-badge', selectedClase.is_active ? 'badge-active' : 'badge-suspended']">
                      {{ selectedClase.is_active ? 'Activa' : 'Suspendida' }}
                    </span>
                  </dd>
                </div>

              </dl>
            </div>

            <!-- Pie del modal -->
            <div class="modal-footer">
              <button class="btn-close-modal" @click="closeModal">Cerrar</button>
              <!-- Escenario 4: solo para clases activas -->
              <button
                v-if="selectedClase.is_active"
                class="btn-suspender"
                @click="handleSuspender"
              >
                Suspender clase
              </button>
            </div>

          </div>
        </div>
      </Transition>
    </Teleport>

  </AdminLayout>
</template>

<style scoped>
.page-wrapper {
  width: 100%;
}

/* ── Encabezado ── */

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.75rem;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.btn-back {
  margin-top: 4px;
  background: none;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0.4rem 0.9rem;
  font-size: 0.82rem;
  color: #6b7280;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.15s, color 0.15s;
}

.btn-back:hover {
  background-color: #f3f4f6;
  color: #374151;
}

.page-actividad {
  margin: 0 0 0.2rem 0;
  font-size: 1.5rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: #11998e;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 500;
  color: #1f2937;
  margin: 0 0 0.2rem 0;
}

.title-desc {
  font-weight: 400;
  color: #6b7280;
  font-size: 1.1rem;
}

.page-subtitle {
  color: #6b7280;
  font-size: 0.88rem;
  margin: 0;
}

/* ── Leyenda ── */

.legend {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding: 0.5rem 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  font-size: 0.82rem;
  color: #374151;
  align-self: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

/* ── Estados ── */

.state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 4rem 2rem;
  border-radius: 12px;
  text-align: center;
}

.state-forbidden {
  background-color: #fff7ed;
  border: 1px solid #fed7aa;
}

.state-error {
  background-color: #fff5f5;
  border: 1px solid #fecaca;
}

.state-icon { font-size: 2.5rem; line-height: 1; }

.state-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #9a3412;
  margin: 0;
}

.state-error .state-title { color: #991b1b; }

.state-desc {
  font-size: 0.9rem;
  color: #7c2d12;
  margin: 0;
  max-width: 400px;
}

.state-error .state-desc { color: #7f1d1d; }

.btn-secondary {
  margin-top: 0.25rem;
  background-color: #f3f4f6;
  color: #374151;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.6rem 1.4rem;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-secondary:hover { background-color: #e5e7eb; }

/* ── Skeleton ── */

.skeleton-wrapper { display: flex; flex-direction: column; gap: 0.75rem; }

.skeleton-header {
  height: 48px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  border-radius: 8px;
  animation: shimmer 1.4s infinite;
}

.skeleton-calendar {
  height: 540px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  border-radius: 12px;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Contenedor del calendario ── */

.calendar-container {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 1.5rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

/* Override de estilos de FullCalendar para que coincida con la paleta */
:deep(.fc-button-primary) {
  background-color: #11998e !important;
  border-color: #11998e !important;
  font-size: 0.82rem !important;
  padding: 0.35rem 0.8rem !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
  text-transform: none !important;
}

:deep(.fc-button-primary:hover) {
  background-color: #0c8a70 !important;
  border-color: #0c8a70 !important;
}

:deep(.fc-button-primary:disabled) {
  background-color: #6b7280 !important;
  border-color: #6b7280 !important;
}

:deep(.fc-button-active) {
  background-color: #0a6b63 !important;
  border-color: #0a6b63 !important;
}

:deep(.fc-toolbar-title) {
  font-size: 1.05rem !important;
  font-weight: 700 !important;
  color: #1f2937 !important;
  text-transform: capitalize;
}

:deep(.fc-daygrid-day-number),
:deep(.fc-col-header-cell-cushion) {
  color: #374151;
  text-decoration: none;
}

:deep(.fc-day-today) {
  background-color: #fef9c3 !important;  /* amarillo suave */
}

:deep(.fc-day-today .fc-daygrid-day-number) {
  background-color: #f59e0b;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.82rem;
}

/* En vista semana/día el encabezado de hoy */
:deep(.fc-col-header-cell.fc-day-today) {
  background-color: #fef3c7;
}

:deep(.fc-col-header-cell.fc-day-today .fc-col-header-cell-cushion) {
  color: #92400e;
  font-weight: 700;
}

:deep(.fc-event) {
  border-radius: 5px !important;
  font-size: 0.78rem !important;
  font-weight: 600 !important;
  cursor: pointer !important;
  padding: 1px 4px !important;
}

:deep(.fc-event:hover) {
  opacity: 0.88;
}

/* ══════════════════════════════════════
   MODAL
══════════════════════════════════════ */

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.modal {
  background: white;
  border-radius: 14px;
  width: 100%;
  max-width: 440px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header--active    { background-color: #f0fdf4; }
.modal-header--suspended { background-color: #f9fafb; }

.modal-title {
  font-size: 1rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  transition: color 0.15s;
}

.modal-close:hover { color: #374151; }

.modal-body {
  padding: 1.5rem;
}

.detail-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 0;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.detail-row dt {
  flex-shrink: 0;
  width: 90px;
  font-size: 0.75rem;
  font-weight: 700;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-row dd {
  flex: 1;
  font-size: 0.92rem;
  color: #1f2937;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

/* Barra de ocupación */
.inscriptos-bar {
  flex: 1;
  height: 6px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
  max-width: 120px;
}

.inscriptos-fill {
  display: block;
  height: 100%;
  background-color: #11998e;
  border-radius: 999px;
  transition: width 0.3s;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
}

.badge-active    { background-color: #dcfce7; color: #105e3a; }
.badge-suspended { background-color: #f3f4f6; color: #6b7280; }

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #f3f4f6;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-close-modal {
  background-color: #f3f4f6;
  color: #374151;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.55rem 1.2rem;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-close-modal:hover { background-color: #e5e7eb; }

.btn-suspender {
  background-color: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.55rem 1.2rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-suspender:hover { background-color: #fee2e2; }

/* ── Transición del modal ── */

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-active .modal,
.modal-fade-leave-active .modal {
  transition: transform 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .modal,
.modal-fade-leave-to .modal {
  transform: scale(0.95) translateY(-8px);
}

@media (max-width: 640px) {
  .page-header { flex-direction: column; }
  .legend { align-self: flex-start; }
  .calendar-container { padding: 0.75rem; }
  .modal { margin: 0.5rem; }
}
</style>
