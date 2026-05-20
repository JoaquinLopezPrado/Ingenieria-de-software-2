<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import {
  getTurnos,
  getAllActivities,
  type Turno,
  type ActivityOption,
} from '@/services/sessionService'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const googleLinked = ref(route.query.google_linked === 'true')
const googleAlreadyInUse = ref(route.query.error === 'google_already_in_use')
const googleLinkError = ref(route.query.error === 'google_link_failed')
const googleUnlinked = ref(route.query.google_unlinked === 'true')
const googleUnlinkError = ref(route.query.error === 'google_unlink_failed')

function normalizeRole(user: any): string {
  const rawRole =
    user?.role?.name ??
    user?.role_name ??
    user?.role ??
    ''
  return rawRole
}

const turnos     = ref<Turno[]>([])
const activities = ref<ActivityOption[]>([])
const isLoading  = ref(true)
const hasError   = ref(false)

// ─── Métricas ─────────────────────────────────────────────────────────────────

const now          = new Date()
const currentMonth = now.getMonth() + 1
const currentYear  = now.getFullYear()

const activeTurnosCount    = computed(() => turnos.value.filter(t => t.is_active).length)
const activeActivitiesCount = computed(() => activities.value.filter(a => a.is_active).length)
const thisMonthTurnos      = computed(() =>
  turnos.value.filter(t => t.is_active && t.month === currentMonth && t.year === currentYear)
)

// Nombre del mes actual
const MONTHS = [
  'Enero','Febrero','Marzo','Abril','Mayo','Junio',
  'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre',
]
const currentMonthName = MONTHS[currentMonth - 1]

// ─── Saludo y usuario ─────────────────────────────────────────────────────────

const greeting = computed(() => {
  const h = now.getHours()
  if (h < 12) return 'Buenos días'
  if (h < 20) return 'Buenas tardes'
  return 'Buenas noches'
})

const userName = computed(() => {
  const u = authStore.user
  return u?.name ?? u?.email?.split('@')[0] ?? 'Administrador'
})

// ─── Mapas auxiliares ─────────────────────────────────────────────────────────

const activityMap = computed(() =>
  new Map(activities.value.map(a => [a.id, a.name]))
)

const DAY_LABELS: Record<string, string> = {
  lunes: 'Lun', martes: 'Mar', miercoles: 'Mié',
  jueves: 'Jue', viernes: 'Vie', sabado: 'Sáb',
}

// ─── Carga inicial ────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    const [turnosRes, acts] = await Promise.all([
      getTurnos({ page_size: 500 }),
      getAllActivities(),
    ])
    turnos.value     = turnosRes.items
    activities.value = acts
  } catch (e: unknown) {
    const err = e as { response?: { status?: number }; request?: unknown }
    if (err?.response?.status === 401) {
      router.push({ name: 'login' })
      return
    }
    hasError.value = true
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <AdminLayout>
    <div class="dashboard">

      <!-- ── Encabezado ── -->
      <div class="dash-header">
        <div class="dash-welcome">
          <p class="dash-greeting">{{ greeting }}, <strong>{{ userName }}</strong> 👋</p>
          <h1 class="dash-title">Panel de administración</h1>
          <p class="dash-date">{{ currentMonthName }} {{ currentYear }}</p>
        </div>
        <div class="dash-actions">
          <RouterLink to="/activities/schedule" class="btn-primary">
            <span class="btn-icon">+</span> Programar turno
          </RouterLink>
          <RouterLink to="/activities/turnos" class="btn-secondary">
            Ver grilla
          </RouterLink>
        </div>
      </div>

      <!-- ── Skeleton de carga ── -->
      <div v-if="isLoading" class="metrics-grid">
        <div v-for="i in 3" :key="i" class="metric-skeleton"></div>
      </div>

      <!-- ── Error de conexión ── -->
      <div v-else-if="hasError" class="error-panel">
        <span class="error-icon">⚠</span>
        <div>
          <p class="error-title">No se pudieron cargar las métricas</p>
          <p class="error-desc">Verificá la conexión con el servidor e intentá de nuevo.</p>
        </div>
        <button class="btn-secondary" @click="() => router.go(0)">Reintentar</button>
      </div>

      <!-- ── Tarjetas de métricas ── -->
      <div v-else class="metrics-grid">

        <div class="metric-card">
          <div class="metric-icon metric-icon--teal">
            <span>◷</span>
          </div>
          <div class="metric-body">
            <p class="metric-value">{{ activeTurnosCount }}</p>
            <p class="metric-label">Turnos activos</p>
            <p class="metric-sub">en total</p>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon metric-icon--blue">
            <span>◈</span>
          </div>
          <div class="metric-body">
            <p class="metric-value">{{ activeActivitiesCount }}</p>
            <p class="metric-label">Actividades activas</p>
            <p class="metric-sub">disponibles</p>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon metric-icon--amber">
            <span>📅</span>
          </div>
          <div class="metric-body">
            <p class="metric-value">{{ thisMonthTurnos.length }}</p>
            <p class="metric-label">Turnos este mes</p>
            <p class="metric-sub">{{ currentMonthName }} {{ currentYear }}</p>
          </div>
        </div>

      </div>

      <!-- ── Turnos activos del mes ── -->
      <template v-if="!isLoading && !hasError">

        <div v-if="thisMonthTurnos.length > 0" class="section">
          <div class="section-header">
            <h2 class="section-title">
              Turnos activos — {{ currentMonthName }} {{ currentYear }}
            </h2>
            <RouterLink to="/activities/turnos" class="section-link">
              Ver todos →
            </RouterLink>
          </div>

          <div class="turno-list">
            <div
              v-for="t in thisMonthTurnos"
              :key="t.id"
              class="turno-row"
            >
              <div class="turno-row-left">
                <span class="turno-activity">
                  {{ activityMap.get(t.activity_id) ?? `Actividad #${t.activity_id}` }}
                </span>
                <span v-if="t.description" class="turno-desc">{{ t.description }}</span>
              </div>

              <div class="turno-row-center">
                <span
                  v-for="day in t.days"
                  :key="day"
                  class="day-pill"
                >{{ DAY_LABELS[day] ?? day }}</span>
                <span class="turno-time">{{ t.start_time }} – {{ t.end_time }}</span>
              </div>

              <RouterLink
                :to="`/activities/turnos/${t.id}/edit`"
                class="turno-edit-link"
              >
                Editar →
              </RouterLink>
            </div>
          </div>
        </div>

        <!-- Estado vacío para el mes -->
        <div v-else class="empty-panel">
          <div class="empty-icon">📅</div>
          <h2 class="empty-title">Sin turnos para {{ currentMonthName }}</h2>
          <p class="empty-desc">
            No hay turnos activos programados para este mes. Podés crear el primero ahora.
          </p>
          <RouterLink to="/activities/schedule" class="btn-primary">
            Programar turno
          </RouterLink>
        </div>

      </template>

    </div>
  </AdminLayout>
</template>

<style scoped>

.home-page {
  min-height: 100vh;
  background: #d9eeea;
  display: flex;
  flex-direction: column;
  padding-top: 60px;
}

.topbar {
  width: 100%;
  padding: 20px 20px 12px;
}

.dashboard {
  width: 100%;

}

/* ── Encabezado ── */

.dash-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.brand-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.logo {
  margin: 0;
  color: #0d9b8a;
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.role-chip {
  width: fit-content;
  margin: 0;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(13, 155, 138, 0.12);
  color: #0d9b8a;
  font-size: 0.92rem;
  font-weight: 700;
}

.home-content {
  width: 100%;
  max-width: 980px;
  margin: 0 auto;
  padding: 20px 20px 48px;
}

.dash-greeting {
  font-size: 0.95rem;
  color: #6b7280;
  margin: 0 0 0.3rem 0;
}

.dash-greeting strong {
  color: #11998e;
}

.dash-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
}

.dash-date {
  font-size: 0.82rem;
  color: #9ca3af;
  margin: 0;
}

.dash-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

/* ── Botones ── */

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background-color: #11998e;
  color: white;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  text-decoration: none;
  white-space: nowrap;
  transition: background-color 0.15s;
}
.btn-primary:hover { background-color: #0c8a70; }

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background-color: white;
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
.btn-secondary:hover { background-color: #f3f4f6; }

.btn-icon {
  font-size: 1.1rem;
  line-height: 1;
}

/* ── Tarjetas de métricas ── */

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  margin-bottom: 2rem;
}

@media (min-width: 640px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (min-width: 1024px) {
  .metrics-grid { grid-template-columns: repeat(3, 1fr); }
}

.metric-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1.25rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  transition: box-shadow 0.2s, transform 0.2s;
}
.metric-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.09);
  transform: translateY(-1px);
}

.metric-icon {
  width: 52px;
  height: 52px;
  flex-shrink: 0;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}
.metric-icon--teal  { background: #d1fae5; color: #047857; }
.metric-icon--blue  { background: #dbeafe; color: #1d4ed8; }
.metric-icon--amber { background: #fef3c7; color: #d97706; }

.metric-value {
  font-size: 2rem;
  font-weight: 800;
  color: #111827;
  margin: 0 0 0.1rem 0;
  line-height: 1;
}
.metric-label {
  font-size: 0.88rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 0.1rem 0;
}
.metric-sub {
  font-size: 0.75rem;
  color: #9ca3af;
  margin: 0;
}

/* Skeleton */
.metric-skeleton {
  height: 96px;
  border-radius: 12px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Error ── */

.error-panel {
  background: #fff5f5;
  border: 1px solid #fecaca;
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.error-icon { font-size: 1.5rem; }
.error-title { font-size: 0.9rem; font-weight: 600; color: #991b1b; margin: 0; }
.error-desc  { font-size: 0.82rem; color: #b91c1c; margin: 0.2rem 0 0; }

/* ── Sección de turnos del mes ── */

.section { margin-top: 0.5rem; }

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.85rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.section-link {
  font-size: 0.82rem;
  color: #11998e;
  font-weight: 600;
  text-decoration: none;
}
.section-link:hover { text-decoration: underline; }

/* Lista de turnos */

.turno-list {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.turno-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem 1.25rem;
  border-bottom: 1px solid #f3f4f6;
  flex-wrap: wrap;
  transition: background-color 0.12s;
}
.turno-row:last-child { border-bottom: none; }
.turno-row:hover { background-color: #fafafa; }

.turno-row-left {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 140px;
  flex: 1;
}
.turno-activity {
  font-size: 0.9rem;
  font-weight: 600;
  color: #111827;
}
.turno-desc {
  font-size: 0.78rem;
  color: #6b7280;
}

.turno-row-center {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.day-pill {
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
}
.turno-time {
  font-size: 0.82rem;
  color: #4b5563;
  white-space: nowrap;
  margin-left: 0.25rem;
}

.turno-edit-link {
  font-size: 0.82rem;
  color: #11998e;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  margin-left: auto;
}
.turno-edit-link:hover { text-decoration: underline; }

/* ── Estado vacío ── */

.empty-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 3.5rem 2rem;
  background: #f9fafb;
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  text-align: center;
  margin-top: 0.5rem;
}
.empty-icon  { font-size: 2.5rem; }
.empty-title { font-size: 1rem; font-weight: 700; color: #374151; margin: 0; }
.empty-desc  { font-size: 0.88rem; color: #6b7280; margin: 0; max-width: 380px; }

/* ── Responsive ── */

@media (max-width: 640px) {
  .dash-header { flex-direction: column; }
  .turno-row   { flex-direction: column; align-items: flex-start; }
  .turno-edit-link { margin-left: 0; }
}

.section-header p {
  margin: 0;
  color: #6b7280;
  line-height: 1.45;
}

.actions-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.centered-grid {
  width: 100%;
  display: flex;
  justify-content: center;
}

.action-card {
  width: 100%;
  max-width: 360px;
  background: white;
  border-radius: 24px;
  padding: 24px 20px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.10);
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(24, 180, 163, 0.12);
  font-size: 1.35rem;
  margin-bottom: 14px;
}

.action-card h4 {
  margin: 0 0 8px;
  color: #1f2937;
  font-size: 1.08rem;
}

.action-card p {
  margin: 0 0 14px;
  color: #6b7280;
  line-height: 1.45;
}

.card-link {
  color: #0d9b8a;
  font-weight: 700;
  font-size: 0.95rem;
}

.empty-role-card {
  background: white;
  border-radius: 24px;
  padding: 24px 20px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.06);
}

.banner {
  border-radius: 12px;
  padding: 14px 18px;
  font-size: 14px;
  font-weight: 500;
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

.empty-role-card h3 {
  display: block;
  margin-bottom: 8px;
  color: #1f2937;
  font-size: 1.02rem;
}

.empty-role-card p {
  margin: 0;
  color: #6b7280;
  line-height: 1.45;
}

@media (max-width: 768px) {
  .topbar-inner {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-card {
    padding: 26px 22px;
    border-radius: 22px;
  }

  .hero-text h2 {
    font-size: 1.65rem;
  }
}
</style>
