<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { useInscripcionStore } from '@/stores/inscripcionStore'
import {
  getTurnosParaInscripcion,
  getAdminWaitlistEntries, quitarDeListaEspera,
  getSubscriptionsByUser, adminCancelSubscription,
} from '@/services/inscripcionService'
import type { AdminWaitlistEntry, SubscriptionEntry } from '@/services/inscripcionService'
import { getFormOptions, extractBackendError, type Turno, type ActivityOption } from '@/services/sessionService'
import { getClienteById } from '@/services/clientesService'
import type { Cliente as ClienteService } from '@/services/clientesService'

const router = useRouter()
const route = useRoute()
const inscripcionStore = useInscripcionStore()

// Flujo cliente-first (/clientes/:clienteId/inscripciones/...) vs flujo viejo (/inscripciones/...)
const isClienteFlow = computed(() => !!route.params.clienteId)
const clienteId = computed(() => isClienteFlow.value ? Number(route.params.clienteId) : null)

const clienteFromRoute = ref<ClienteService | null>(null)
const cliente = computed(() =>
  isClienteFlow.value ? clienteFromRoute.value : inscripcionStore.clienteSeleccionado
)

// ─── Estado principal ──────────────────────────────────────────────────────────

const allTurnos = ref<Turno[]>([])
const allActivities = ref<ActivityOption[]>([])
const activityMap = ref<Map<number, string>>(new Map())
const isLoading = ref(true)
const errorMessage = ref('')

// ─── Constantes ────────────────────────────────────────────────────────────────

const DAY_OPTIONS = [
  { value: 'lunes',     label: 'Lun' },
  { value: 'martes',   label: 'Mar' },
  { value: 'miercoles', label: 'Mié' },
  { value: 'jueves',   label: 'Jue' },
  { value: 'viernes',  label: 'Vie' },
  { value: 'sabado',   label: 'Sáb' },
]

const DAY_LABELS: Record<string, string> = {
  lunes: 'Lun', martes: 'Mar', miercoles: 'Mié',
  jueves: 'Jue', viernes: 'Vie', sabado: 'Sáb',
}

const PAGE_SIZE = 10

// ─── Filtros ──────────────────────────────────────────────────────────────────

const filterActivity = ref<number | ''>('')
const filterDays = ref<string[]>([])
const filterHorario = ref('')

// ─── Paginación ───────────────────────────────────────────────────────────────

const currentPage = ref(1)

// ─── Datos derivados ──────────────────────────────────────────────────────────

// Solo turnos activos (HU: "todos los turnos activos")
const activeTurnos = computed(() => allTurnos.value.filter(t => t.is_active))

const activityFilterOptions = computed(() => {
  const seen = new Set<number>()
  const opts: Array<{ id: number; name: string }> = []
  activeTurnos.value.forEach(t => {
    if (!seen.has(t.activity_id)) {
      seen.add(t.activity_id)
      opts.push({ id: t.activity_id, name: activityMap.value.get(t.activity_id) ?? `Actividad #${t.activity_id}` })
    }
  })
  return opts.sort((a, b) => a.name.localeCompare(b.name))
})

const horarioOptions = computed(() => {
  const seen = new Set<string>()
  const opts: string[] = []
  activeTurnos.value.forEach(t => {
    if (!seen.has(t.start_time)) {
      seen.add(t.start_time)
      opts.push(t.start_time)
    }
  })
  return opts.sort()
})

// ─── Filtrado client-side ─────────────────────────────────────────────────────

const filteredTurnos = computed(() => {
  let result = activeTurnos.value

  if (filterActivity.value !== '') {
    result = result.filter(t => t.activity_id === filterActivity.value)
  }

  if (filterDays.value.length > 0) {
    result = result.filter(t => filterDays.value.some(d => t.days.includes(d)))
  }

  if (filterHorario.value) {
    result = result.filter(t => t.start_time === filterHorario.value)
  }

  return result
})

// ─── Paginación client-side ───────────────────────────────────────────────────

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredTurnos.value.length / PAGE_SIZE))
)

const paginatedTurnos = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredTurnos.value.slice(start, start + PAGE_SIZE)
})

const paginationRange = computed((): (number | '...')[] => {
  const total = totalPages.value
  const cur = currentPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 4)          return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 3)  return [1, '...', total - 4, total - 3, total - 2, total - 1, total]
  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})

const showingFrom = computed(() => (currentPage.value - 1) * PAGE_SIZE + 1)
const showingTo   = computed(() => Math.min(currentPage.value * PAGE_SIZE, filteredTurnos.value.length))

// ─── Flags de UI ──────────────────────────────────────────────────────────────

const hasFilters = computed(() =>
  filterActivity.value !== '' || filterDays.value.length > 0 || filterHorario.value !== ''
)

// Escenario 2: no existen turnos activos en el sistema
const isEmpty = computed(() =>
  !isLoading.value && !errorMessage.value && activeTurnos.value.length === 0
)

// Escenario 5: filtros combinados sin resultados
const noResults = computed(() =>
  !isLoading.value && !errorMessage.value &&
  activeTurnos.value.length > 0 && filteredTurnos.value.length === 0
)

const hasData = computed(() =>
  !isLoading.value && !errorMessage.value && filteredTurnos.value.length > 0
)

// ─── Watches ──────────────────────────────────────────────────────────────────

watch([filterActivity, filterDays, filterHorario], () => {
  currentPage.value = 1
}, { deep: true })

// ─── Helpers ──────────────────────────────────────────────────────────────────

const activityName = (id: number) => activityMap.value.get(id) ?? `Actividad #${id}`

function formatDate(iso: string): string {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

const cupoDisponible = (turno: Turno) =>
  Math.max(0, turno.capacity - turno.enrolled)

function toggleDay(day: string) {
  const idx = filterDays.value.indexOf(day)
  if (idx === -1) filterDays.value.push(day)
  else            filterDays.value.splice(idx, 1)
}

function clearFilters() {
  filterActivity.value = ''
  filterDays.value = []
  filterHorario.value = ''
  currentPage.value = 1
}

function goToPage(page: number | '...') {
  if (typeof page === 'number') currentPage.value = page
}

// ─── Acciones de fila ─────────────────────────────────────────────────────────

function handleInscribir(turno: Turno) {
  inscripcionStore.setTurno(turno)
  if (isClienteFlow.value) {
    router.push({ name: 'clientes-inscripciones-inscribir', params: { clienteId: clienteId.value!, turnoId: turno.id } })
  } else {
    router.push({ name: 'inscripciones-inscribir', params: { turnoId: turno.id } })
  }
}

function handleReinscribir(turno: Turno, endsOn: string) {
  // Calcula el mes siguiente a ends_on como mínimo para la nueva suscripción
  const d = new Date(endsOn + 'T00:00:00')
  const nextMonth = d.getMonth() === 11 ? 1 : d.getMonth() + 2
  const nextYear = d.getMonth() === 11 ? d.getFullYear() + 1 : d.getFullYear()
  inscripcionStore.setTurno(turno)
  router.push({
    name: 'clientes-inscripciones-inscribir',
    params: { clienteId: clienteId.value!, turnoId: turno.id },
    query: { minMonth: nextMonth, minYear: nextYear },
  })
}

function handleListaEspera(turno: Turno) {
  inscripcionStore.setTurno(turno)
  if (isClienteFlow.value) {
    router.push({ name: 'clientes-inscripciones-lista-espera', params: { clienteId: clienteId.value!, turnoId: turno.id } })
  } else {
    router.push({ name: 'inscripciones-lista-espera', params: { turnoId: turno.id } })
  }
}

const removingEsperaId = ref<number | null>(null)
const cancellingSubscriptionId = ref<number | null>(null)
const confirmandoBajaId = ref<number | null>(null)
const bajaError = ref<string | null>(null)

async function handleDarDeBaja(turno: Turno) {
  const entry = inscripcionStore.getSubscriptionEntry(turno.id)
  if (!entry || entry.status !== 'active' || entry.ends_on || cancellingSubscriptionId.value !== null) return
  bajaError.value = null
  cancellingSubscriptionId.value = entry.subscription_id
  try {
    const endsOn = await adminCancelSubscription(entry.subscription_id)
    inscripcionStore.markSubscriptionEndsOn(entry.subscription_id, endsOn)
  } catch (err) {
    bajaError.value = extractBackendError(err)
  } finally {
    cancellingSubscriptionId.value = null
    confirmandoBajaId.value = null
  }
}

async function handleQuitarEspera(turno: Turno) {
  const entry = inscripcionStore.getWaitlistEntry(turno.id)
  if (!entry || removingEsperaId.value !== null) return
  removingEsperaId.value = entry.entry_id
  try {
    await quitarDeListaEspera(entry.entry_id)
    inscripcionStore.removeWaitlistEntry(entry.entry_id)
  } catch {
    // el botón vuelve a habilitarse para reintentar
  } finally {
    removingEsperaId.value = null
  }
}

// ─── Carga inicial ─────────────────────────────────────────────────────────────

onMounted(async () => {
  const userId = isClienteFlow.value ? clienteId.value : inscripcionStore.clienteSeleccionado?.id ?? null

  try {
    const requests = [
      getTurnosParaInscripcion(),
      getFormOptions(),
      userId !== null ? getAdminWaitlistEntries(userId) : Promise.resolve([] as AdminWaitlistEntry[]),
      userId !== null ? getSubscriptionsByUser(userId) : Promise.resolve([] as SubscriptionEntry[]),
    ] as const
    const [turnosRes, formOpts, waitlistEntries, subscriptionEntries] = await Promise.all(requests)
    allTurnos.value = turnosRes.items
    allActivities.value = formOpts.activities
    activityMap.value = new Map(formOpts.activities.map((a: ActivityOption) => [a.id, a.name]))
    inscripcionStore.setWaitlistEntries(waitlistEntries)
    inscripcionStore.setSubscriptionEntries(subscriptionEntries)
  } catch (err) {
    errorMessage.value = extractBackendError(err)
  } finally {
    isLoading.value = false
  }

  // Carga del banner del cliente (no bloquea la tabla de turnos)
  if (isClienteFlow.value && clienteId.value !== null) {
    getClienteById(clienteId.value)
      .then(c => { clienteFromRoute.value = c })
      .catch(() => {})
  }
})
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <!-- ── Encabezado ── -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Inscripciones</h1>
          <p class="page-subtitle">Seleccioná el turno para inscribir al cliente o agregar a la lista de espera</p>
        </div>
        <div class="header-actions">
          <button
            v-if="!isClienteFlow"
            class="btn-secondary btn-accent"
            @click="router.push({ name: 'inscripciones-clases' })"
          >
            Inscribir a clase individual
          </button>
          <button
            v-if="isClienteFlow"
            class="btn-secondary"
            @click="router.push({ name: 'ficha-cliente', params: { clienteId: clienteId } })"
          >
            ← Volver a la ficha
          </button>
          <button
            v-else
            class="btn-secondary"
            @click="router.push({ name: 'inscripciones-buscar-cliente' })"
          >
            ← Cambiar cliente
          </button>
        </div>
      </div>

      <!-- ── Banner cliente seleccionado ── -->
      <div v-if="cliente" class="cliente-banner">
        <div class="cliente-avatar" aria-hidden="true">
          {{ cliente.first_name[0] }}{{ cliente.last_name[0] }}
        </div>
        <div class="cliente-info">
          <span class="cliente-label">Cliente seleccionado</span>
          <span class="cliente-name">{{ cliente.first_name }} {{ cliente.last_name }}</span>
          <span class="cliente-doc">{{ cliente.doc_type_name }} {{ cliente.doc_number }}</span>
        </div>
      </div>

      <!-- ── Error de baja ── -->
      <div v-if="bajaError" class="inline-error" role="alert">
        <span>⚠ {{ bajaError }}</span>
        <button type="button" class="inline-error-close" @click="bajaError = null">✕</button>
      </div>

      <!-- ── Panel de filtros ── -->
      <div v-if="!isLoading && !errorMessage" class="filters-card">
        <div class="filters-grid">

          <div class="filter-group">
            <label class="filter-label">Actividad</label>
            <select v-model="filterActivity" class="filter-select">
              <option value="">Todas las actividades</option>
              <option v-for="a in activityFilterOptions" :key="a.id" :value="a.id">
                {{ a.name }}
              </option>
            </select>
          </div>

          <div class="filter-group">
            <label class="filter-label">Horario</label>
            <select v-model="filterHorario" class="filter-select">
              <option value="">Todos los horarios</option>
              <option v-for="h in horarioOptions" :key="h" :value="h">
                {{ h }}
              </option>
            </select>
          </div>

        </div>

        <div class="filters-days-row">
          <span class="filter-label">Días</span>
          <div class="day-filter-pills">
            <button
              v-for="day in DAY_OPTIONS"
              :key="day.value"
              type="button"
              :class="['day-filter-pill', { 'pill-active': filterDays.includes(day.value) }]"
              @click="toggleDay(day.value)"
            >
              {{ day.label }}
            </button>
          </div>
          <button
            v-if="hasFilters"
            type="button"
            class="btn-clear"
            @click="clearFilters"
          >
            ✕ Limpiar filtros
          </button>
        </div>
      </div>

      <!-- ── Estado: cargando ── -->
      <div v-if="isLoading" class="skeleton-wrapper" aria-label="Cargando turnos...">
        <div v-for="n in 5" :key="n" class="skeleton-row"></div>
      </div>

      <!-- ── Estado: error de carga ── -->
      <div v-else-if="errorMessage" class="state-card state-error">
        <div class="state-icon">⚠</div>
        <h2 class="state-title">Error al cargar los turnos</h2>
        <p class="state-desc">{{ errorMessage }}</p>
        <button class="btn-secondary" @click="router.go(0)">Reintentar</button>
      </div>

      <!-- ── Escenario 2: sin turnos activos en el sistema ── -->
      <div v-else-if="isEmpty" class="state-card state-empty">
        <div class="state-icon">📅</div>
        <h2 class="state-title">No hay turnos activos cargados</h2>
        <p class="state-desc">
          El sistema no tiene turnos activos disponibles. Contactá al administrador para programar turnos.
        </p>
      </div>

      <!-- ── Escenario 5: filtros sin resultados ── -->
      <div v-else-if="noResults" class="state-card state-empty">
        <div class="state-icon">🔍</div>
        <h2 class="state-title">No hay turnos que coincidan con los filtros aplicados</h2>
        <p class="state-desc">Probá con otros criterios o limpiá los filtros.</p>
        <button class="btn-secondary" @click="clearFilters">Limpiar filtros</button>
      </div>

      <!-- ── Tabla de turnos (Escenarios 1, 3, 4, 6, 7) ── -->
      <div v-else-if="hasData" class="table-container">
        <div class="table-scroll">
          <table class="turnos-table">
            <thead>
              <tr>
                <th>Actividad</th>
                <th>Descripción</th>
                <th>Días</th>
                <th>Horario</th>
                <th>Cupo disponible</th>
                <th>Monto por clase</th>
                <th>Disponibilidad</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="turno in paginatedTurnos" :key="turno.id">
                <td class="cell-activity">{{ activityName(turno.activity_id) }}</td>
                <td class="cell-desc">{{ turno.description || '—' }}</td>
                <td class="cell-days">
                  <span
                    v-for="day in turno.days"
                    :key="day"
                    class="day-pill"
                  >
                    {{ DAY_LABELS[day] ?? day }}
                  </span>
                </td>
                <td class="cell-time">{{ turno.start_time }} – {{ turno.end_time }}</td>
                <td class="cell-cupo">
                  <span :class="turno.has_remaining_classes ? 'cupo-num' : 'cupo-num cupo-agotado'">
                    {{ turno.has_remaining_classes ? cupoDisponible(turno) : 0 }}
                    <span class="cupo-total">/ {{ turno.capacity }}</span>
                  </span>
                </td>
                <td class="cell-price">${{ turno.class_price }}</td>
                <td class="cell-disponibilidad">
                  <span
                    :class="['disponibilidad-badge',
                      turno.has_remaining_classes ? 'badge-con-cupo' : 'badge-sin-cupo']"
                  >
                    {{ turno.has_remaining_classes ? 'Con cupo' : 'Sin cupo' }}
                  </span>
                </td>
                <td class="cell-accion">
                  <!-- Ya inscripto (activo, sin baja programada) → Dar de baja (con confirmación inline) -->
                  <template v-if="inscripcionStore.getSubscriptionEntry(turno.id)?.status === 'active' && !inscripcionStore.getSubscriptionEntry(turno.id)?.ends_on">
                    <div
                      v-if="confirmandoBajaId === inscripcionStore.getSubscriptionEntry(turno.id)!.subscription_id"
                      class="baja-confirm-cell"
                    >
                      <p class="baja-confirm-msg">¿Confirmás la baja? El cliente mantiene el lugar hasta el fin del período pagado.</p>
                      <div class="baja-confirm-btns">
                        <button
                          type="button"
                          class="baja-btn baja-btn--confirmar"
                          :disabled="cancellingSubscriptionId === inscripcionStore.getSubscriptionEntry(turno.id)!.subscription_id"
                          @click="handleDarDeBaja(turno)"
                        >
                          {{ cancellingSubscriptionId === inscripcionStore.getSubscriptionEntry(turno.id)!.subscription_id
                            ? 'Procesando...'
                            : 'Sí, dar de baja'
                          }}
                        </button>
                        <button
                          type="button"
                          class="baja-btn baja-btn--cancelar"
                          :disabled="cancellingSubscriptionId === inscripcionStore.getSubscriptionEntry(turno.id)!.subscription_id"
                          @click="confirmandoBajaId = null"
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                    <button
                      v-else
                      type="button"
                      class="btn-dar-baja"
                      @click="confirmandoBajaId = inscripcionStore.getSubscriptionEntry(turno.id)!.subscription_id"
                    >
                      Dar de baja
                    </button>
                  </template>
                  <!-- Baja ya programada (active + ends_on seteado) → badge + botón reinscribir -->
                  <div
                    v-else-if="inscripcionStore.getSubscriptionEntry(turno.id)?.status === 'active' && !!inscripcionStore.getSubscriptionEntry(turno.id)?.ends_on"
                    class="baja-programada-cell"
                  >
                    <span class="badge-baja-programada">
                      Baja programada · hasta el {{ formatDate(inscripcionStore.getSubscriptionEntry(turno.id)!.ends_on!) }}
                    </span>
                    <button
                      v-if="isClienteFlow"
                      type="button"
                      class="btn-reinscribir"
                      @click="handleReinscribir(turno, inscripcionStore.getSubscriptionEntry(turno.id)!.ends_on!)"
                    >
                      Re-inscribir
                    </button>
                  </div>
                  <!-- Con cupo y sin suscripción → Inscribir cliente -->
                  <button
                    v-else-if="turno.has_remaining_classes"
                    type="button"
                    class="btn-inscribir"
                    @click="handleInscribir(turno)"
                  >
                    Inscribir cliente
                  </button>
                  <!-- Sin cupo → Agregar o Quitar de lista de espera -->
                  <button
                    v-else
                    type="button"
                    :class="['btn-espera', { 'btn-espera--en-espera': inscripcionStore.getWaitlistEntry(turno.id) }]"
                    :disabled="removingEsperaId === inscripcionStore.getWaitlistEntry(turno.id)?.entry_id"
                    @click="inscripcionStore.getWaitlistEntry(turno.id) ? handleQuitarEspera(turno) : handleListaEspera(turno)"
                  >
                    {{ inscripcionStore.getWaitlistEntry(turno.id)
                      ? (removingEsperaId === inscripcionStore.getWaitlistEntry(turno.id)!.entry_id ? 'Quitando...' : 'Quitar de lista de espera')
                      : 'Agregar a lista de espera'
                    }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- ── Footer: conteo + paginación ── -->
        <div class="table-footer">
          <span class="table-count">
            Mostrando {{ showingFrom }}–{{ showingTo }} de
            {{ filteredTurnos.length }} turno{{ filteredTurnos.length !== 1 ? 's' : '' }}
          </span>

          <div v-if="totalPages > 1" class="pagination">
            <button
              class="page-btn"
              :disabled="currentPage === 1"
              @click="currentPage--"
              aria-label="Página anterior"
            >
              ←
            </button>
            <button
              v-for="(page, idx) in paginationRange"
              :key="idx"
              :class="['page-btn', {
                'page-btn-active': page === currentPage,
                'page-btn-dots':   page === '...',
              }]"
              :disabled="page === '...'"
              @click="goToPage(page)"
            >
              {{ page }}
            </button>
            <button
              class="page-btn"
              :disabled="currentPage === totalPages"
              @click="currentPage++"
              aria-label="Página siguiente"
            >
              →
            </button>
          </div>
        </div>
      </div>

    </div>
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
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}

.page-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
}

.page-subtitle {
  color: #6b7280;
  font-size: 0.88rem;
  margin: 0;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background-color: #f3f4f6;
  color: #374151;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  cursor: pointer;
  text-decoration: none;
  white-space: nowrap;
  transition: background-color 0.15s;
}

.btn-secondary:hover {
  background-color: #e5e7eb;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.btn-accent {
  background-color: #f0fdf9;
  color: #065f46;
  border-color: #a7f3d0;
}

.btn-accent:hover {
  background-color: #dcfce7;
}

/* ── Banner cliente ── */

.cliente-banner {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
  border: 1.5px solid #a7f3d0;
  border-radius: 12px;
  padding: 0.9rem 1.25rem;
  margin-bottom: 1.25rem;
}

.cliente-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #11998e, #0d9b8a);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  font-weight: 700;
  flex-shrink: 0;
}

.cliente-info {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
  min-width: 0;
}

.cliente-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: #059669;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  white-space: nowrap;
}

.cliente-name {
  font-size: 0.92rem;
  font-weight: 700;
  color: #064e3b;
}

.cliente-doc {
  font-size: 0.82rem;
  color: #065f46;
  font-weight: 500;
}

/* ── Error inline (ej: fallo en dar de baja) ── */

.inline-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #991b1b;
  font-size: 0.88rem;
  font-weight: 500;
  padding: 0.7rem 1rem;
  margin-bottom: 1rem;
}

.inline-error-close {
  background: none;
  border: none;
  color: #991b1b;
  cursor: pointer;
  font-size: 0.85rem;
  flex-shrink: 0;
  padding: 0;
}

/* ── Panel de filtros ── */

.filters-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.filter-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: #6b7280;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.filter-select {
  appearance: none;
  background: white url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 8L1 3h10z'/%3E%3C/svg%3E") no-repeat right 0.7rem center;
  border: 1px solid #d1d5db;
  border-radius: 7px;
  color: #374151;
  font-size: 0.875rem;
  padding: 0.45rem 2rem 0.45rem 0.7rem;
  cursor: pointer;
  transition: border-color 0.15s;
  width: 100%;
}

.filter-select:focus {
  outline: none;
  border-color: #11998e;
  box-shadow: 0 0 0 3px rgba(17, 153, 142, 0.12);
}

.filters-days-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.day-filter-pills {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.day-filter-pill {
  background: white;
  border: 1.5px solid #d1d5db;
  border-radius: 99px;
  color: #374151;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.65rem;
  transition: background-color 0.12s, border-color 0.12s, color 0.12s;
  white-space: nowrap;
}

.day-filter-pill:hover {
  border-color: #11998e;
  color: #11998e;
}

.day-filter-pill.pill-active {
  background-color: #11998e;
  border-color: #11998e;
  color: white;
}

.btn-clear {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  margin-left: auto;
  padding: 0.25rem 0.5rem;
  transition: color 0.12s;
  white-space: nowrap;
}

.btn-clear:hover {
  color: #dc2626;
}

/* ── Skeleton ── */

.skeleton-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.skeleton-row {
  height: 52px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  border-radius: 8px;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
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

.state-empty {
  background-color: #f9fafb;
  border: 2px dashed #d1d5db;
}

.state-error {
  background-color: #fff5f5;
  border: 1px solid #fecaca;
}

.state-icon {
  font-size: 2.5rem;
  line-height: 1;
}

.state-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.state-desc {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
  max-width: 420px;
}

.state-error .state-title,
.state-error .state-desc {
  color: #991b1b;
}

/* ── Tabla ── */

.table-container {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.table-scroll {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.turnos-table {
  width: 100%;
  min-width: 820px;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.turnos-table thead {
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.turnos-table th {
  padding: 0.85rem 1rem;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  color: #6b7280;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
}

.turnos-table td {
  padding: 0.9rem 1rem;
  color: #374151;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}

.turnos-table tbody tr:last-child td {
  border-bottom: none;
}

.turnos-table tbody tr:hover {
  background-color: #fafafa;
}

.cell-activity {
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
}

.cell-desc {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #6b7280;
}

.cell-days {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.day-pill {
  background-color: #eff6ff;
  color: #1d4ed8;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  white-space: nowrap;
}

.cell-time {
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.cell-cupo {
  text-align: center;
}

.cupo-num {
  font-weight: 700;
  color: #15803d;
  font-size: 0.92rem;
}

.cupo-num.cupo-agotado {
  color: #9ca3af;
}

.cupo-total {
  font-weight: 400;
  color: #9ca3af;
  font-size: 0.82rem;
}

.cell-price {
  white-space: nowrap;
  font-weight: 600;
}

.cell-disponibilidad {
  white-space: nowrap;
}

.disponibilidad-badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.2rem 0.65rem;
  border-radius: 99px;
  white-space: nowrap;
}

.badge-con-cupo {
  background-color: #dcfce7;
  color: #15803d;
}

.badge-sin-cupo {
  background-color: #fff7ed;
  color: #c2410c;
}

.cell-accion {
  white-space: nowrap;
}

/* Escenario 6 — turno con cupo */
.btn-inscribir {
  display: inline-flex;
  align-items: center;
  background-color: #18b4a3;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.35rem 0.85rem;
  cursor: pointer;
  transition: background-color 0.12s;
  white-space: nowrap;
}

.btn-inscribir:hover {
  background-color: #0d9b8a;
}

/* Suscripto activo → Dar de baja */
.btn-dar-baja {
  display: inline-flex;
  align-items: center;
  background-color: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.35rem 0.85rem;
  cursor: pointer;
  transition: background-color 0.12s, border-color 0.12s;
  white-space: nowrap;
}

.btn-dar-baja:hover:not(:disabled) {
  background-color: #fee2e2;
  border-color: #fca5a5;
}

.btn-dar-baja:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* Confirmación inline antes de dar de baja */
.baja-confirm-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.4rem;
  max-width: 220px;
  margin-left: auto;
}

.baja-confirm-msg {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 600;
  color: #6b7280;
  text-align: right;
  line-height: 1.4;
}

.baja-confirm-btns {
  display: flex;
  gap: 0.4rem;
}

.baja-btn {
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.3rem 0.65rem;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.12s, border-color 0.12s;
}

.baja-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.baja-btn--confirmar {
  background-color: #b91c1c;
  color: white;
  border: 1px solid #b91c1c;
}

.baja-btn--confirmar:hover:not(:disabled) {
  background-color: #991b1b;
}

.baja-btn--cancelar {
  background: none;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.baja-btn--cancelar:hover:not(:disabled) {
  background-color: #f3f4f6;
}

/* Baja ya programada → badge informativo */
.baja-programada-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.35rem;
}

.badge-baja-programada {
  display: inline-flex;
  align-items: center;
  background-color: #f3f4f6;
  color: #6b7280;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.35rem 0.75rem;
  white-space: nowrap;
}

.btn-reinscribir {
  font-size: 0.75rem;
  font-weight: 600;
  color: #11a691;
  background: none;
  border: 1px solid #11a691;
  border-radius: 6px;
  padding: 0.3rem 0.65rem;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s, color 0.15s;
}

.btn-reinscribir:hover {
  background: #11a691;
  color: #fff;
}

/* Escenario 7 — turno sin cupo */
.btn-espera {
  display: inline-flex;
  align-items: center;
  background-color: #fff7ed;
  color: #c2410c;
  border: 1px solid #fed7aa;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.35rem 0.85rem;
  cursor: pointer;
  transition: background-color 0.12s, border-color 0.12s;
  white-space: nowrap;
}

.btn-espera:hover {
  background-color: #ffedd5;
  border-color: #fdba74;
}

/* Lista de espera: en espera → botón destructivo */
.btn-espera--en-espera {
  background-color: #fef2f2;
  color: #b91c1c;
  border-color: #fecaca;
}

.btn-espera--en-espera:hover {
  background-color: #fee2e2;
  border-color: #fca5a5;
}

.btn-espera--en-espera:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* ── Footer tabla ── */

.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid #f3f4f6;
  flex-wrap: wrap;
}

.table-count {
  font-size: 0.8rem;
  color: #9ca3af;
}

/* ── Paginación ── */

.pagination {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.page-btn {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #374151;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 500;
  min-width: 2rem;
  padding: 0.3rem 0.5rem;
  transition: background-color 0.12s, border-color 0.12s, color 0.12s;
}

.page-btn:hover:not(:disabled) {
  background-color: #f3f4f6;
  border-color: #d1d5db;
}

.page-btn:disabled {
  cursor: default;
  opacity: 0.4;
}

.page-btn-active {
  background-color: #11998e;
  border-color: #11998e;
  color: white;
  font-weight: 700;
}

.page-btn-active:hover:not(:disabled) {
  background-color: #0c8a70;
}

.page-btn-dots {
  border-color: transparent;
  cursor: default;
}

/* ── Responsive ── */

@media (max-width: 1024px) {
  .filters-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .table-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}
</style>
