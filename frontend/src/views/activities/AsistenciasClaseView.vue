<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import {
  getRoster,
  markAttendance,
  deleteAttendance,
  type RosterEntry,
  type AttendanceStatus,
} from '@/services/asistenciasService'

const route   = useRoute()
const router  = useRouter()
const claseId = Number(route.params.claseId)

const actividadNombre = computed(() => String(route.query.actividad ?? `Clase #${claseId}`))
const fechaLabel      = computed(() => String(route.query.fecha    ?? ''))
const horarioLabel    = computed(() => String(route.query.horario  ?? ''))

// ─── Datos ───────────────────────────────────────────────────────────────────

const roster    = ref<RosterEntry[]>([])
const isLoading = ref(true)
const error     = ref('')
const saving    = ref<Set<number>>(new Set())
const saveError = ref<Record<number, string>>({})

// ─── Carga ───────────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    roster.value = await getRoster(claseId)
  } catch {
    error.value = 'No se pudo cargar la lista de inscriptos.'
  } finally {
    isLoading.value = false
  }
})

// ─── Marcar asistencia ───────────────────────────────────────────────────────

async function marcar(entry: RosterEntry, estado: AttendanceStatus) {
  if (saving.value.has(entry.user_id)) return
  saving.value = new Set(saving.value).add(entry.user_id)
  delete saveError.value[entry.user_id]

  try {
    await markAttendance(entry.user_id, claseId, estado)
    const idx = roster.value.findIndex(r => r.user_id === entry.user_id)
    if (idx !== -1) roster.value[idx] = { ...roster.value[idx]!, estado }
  } catch {
    saveError.value = { ...saveError.value, [entry.user_id]: 'Error al guardar' }
  } finally {
    const next = new Set(saving.value)
    next.delete(entry.user_id)
    saving.value = next
  }
}

async function borrar(entry: RosterEntry) {
  if (saving.value.has(entry.user_id)) return
  saving.value = new Set(saving.value).add(entry.user_id)
  delete saveError.value[entry.user_id]

  try {
    await deleteAttendance(entry.user_id, claseId)
    const idx = roster.value.findIndex(r => r.user_id === entry.user_id)
    if (idx !== -1) roster.value[idx] = { ...roster.value[idx]!, estado: null }
  } catch {
    saveError.value = { ...saveError.value, [entry.user_id]: 'Error al borrar' }
  } finally {
    const next = new Set(saving.value)
    next.delete(entry.user_id)
    saving.value = next
  }
}

// ─── Stats ───────────────────────────────────────────────────────────────────

const totalPresentes = computed(() => roster.value.filter(r => r.estado === 'presente').length)
const totalAusentes  = computed(() => roster.value.filter(r => r.estado === 'ausente').length)
const totalSinMarcar = computed(() => roster.value.filter(r => r.estado === null).length)

const sourceLabel: Record<string, string> = {
  subscription: 'Mensual',
  single:       'Clase',
}
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <!-- Encabezado -->
      <div class="page-header">
        <div class="header-left">
          <button class="btn-back" type="button" @click="router.go(-1)">← Volver</button>
          <div>
            <h1 class="page-title">{{ actividadNombre }}</h1>
            <p class="page-subtitle">
              <span v-if="fechaLabel">{{ fechaLabel }}</span>
              <span v-if="fechaLabel && horarioLabel"> · </span>
              <span v-if="horarioLabel">{{ horarioLabel }}</span>
            </p>
          </div>
        </div>
      </div>

      <!-- Skeleton -->
      <div v-if="isLoading" class="skeleton-wrapper">
        <div v-for="n in 6" :key="n" class="skeleton-row"></div>
      </div>

      <!-- Error de carga -->
      <div v-else-if="error" class="state-card state-error">
        <div class="state-icon">⚠</div>
        <p class="state-desc">{{ error }}</p>
        <button class="btn-secondary" type="button" @click="router.go(0)">Reintentar</button>
      </div>

      <!-- Sin inscriptos -->
      <div v-else-if="roster.length === 0" class="state-card state-empty">
        <div class="state-icon">📋</div>
        <h2 class="state-title">Sin inscriptos</h2>
        <p class="state-desc">No hay alumnos inscriptos en esta clase.</p>
      </div>

      <!-- Contenido -->
      <template v-else>

        <!-- Resumen -->
        <div class="summary-bar">
          <div class="summary-chip chip-total">
            <span class="chip-num">{{ roster.length }}</span>
            <span class="chip-label">Inscriptos</span>
          </div>
          <div class="summary-chip chip-presente">
            <span class="chip-num">{{ totalPresentes }}</span>
            <span class="chip-label">Presentes</span>
          </div>
          <div class="summary-chip chip-ausente">
            <span class="chip-num">{{ totalAusentes }}</span>
            <span class="chip-label">Ausentes</span>
          </div>
          <div class="summary-chip chip-sinmarcar">
            <span class="chip-num">{{ totalSinMarcar }}</span>
            <span class="chip-label">Sin marcar</span>
          </div>
        </div>

        <!-- Tabla -->
        <div class="table-container">
          <table class="roster-table">
            <thead>
              <tr>
                <th>Alumno</th>
                <th>T. Suscripción</th>
                <th>Estado</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="entry in roster" :key="entry.user_id">
                <td class="cell-name">{{ entry.full_name }}</td>
                <td class="cell-source">
                  <span class="source-badge">
                    {{ sourceLabel[entry.source] ?? entry.source }}
                  </span>
                </td>
                <td class="cell-estado">
                  <span
                    v-if="entry.estado"
                    :class="['estado-badge', `badge-${entry.estado}`]"
                  >
                    {{ entry.estado === 'presente' ? 'Presente' : 'Ausente' }}
                  </span>
                  <span v-else class="estado-badge badge-sinmarcar">Sin marcar</span>
                </td>
                <td class="cell-actions">
                  <div v-if="saving.has(entry.user_id)" class="saving-indicator">
                    Guardando...
                  </div>
                  <template v-else>
                    <button
                      type="button"
                      :class="['btn-mark', 'btn-presente', { active: entry.estado === 'presente' }]"
                      @click="marcar(entry, 'presente')"
                    >
                      ✓ Presente
                    </button>
                    <button
                      type="button"
                      :class="['btn-mark', 'btn-ausente', { active: entry.estado === 'ausente' }]"
                      @click="marcar(entry, 'ausente')"
                    >
                      ✗ Ausente
                    </button>
                    <button
                      v-if="entry.estado !== null"
                      type="button"
                      class="btn-borrar"
                      @click="borrar(entry)"
                    >
                      ✕
                    </button>
                  </template>
                  <span v-if="saveError[entry.user_id]" class="save-error">
                    {{ saveError[entry.user_id] }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

      </template>
    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper { width: 100%; }

/* ── Encabezado ── */

.page-header { margin-bottom: 1.5rem; }

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-back {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 7px;
  color: #374151;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.45rem 0.9rem;
  transition: background-color 0.12s;
  white-space: nowrap;
}
.btn-back:hover { background: #e5e7eb; }

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.2rem;
}

.page-subtitle {
  color: #6b7280;
  font-size: 0.88rem;
  margin: 0;
}

.btn-secondary {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 7px;
  color: #374151;
  cursor: pointer;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
}
.btn-secondary:hover { background: #e5e7eb; }

/* ── Skeleton ── */

.skeleton-wrapper { display: flex; flex-direction: column; gap: 0.75rem; }

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
  gap: 0.75rem;
  padding: 3.5rem 2rem;
  border-radius: 12px;
  text-align: center;
}

.state-empty { background: #f9fafb; border: 2px dashed #d1d5db; }
.state-error { background: #fff5f5; border: 1px solid #fecaca; }

.state-icon  { font-size: 2.2rem; }
.state-title { font-size: 1.05rem; font-weight: 700; color: #1f2937; margin: 0; }
.state-desc  { font-size: 0.9rem; color: #6b7280; margin: 0; }
.state-error .state-desc { color: #991b1b; }

/* ── Resumen ── */

.summary-bar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}

.summary-chip {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 0.6rem 1rem;
}

.chip-num {
  font-size: 1.3rem;
  font-weight: 700;
  color: #1f2937;
}

.chip-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.chip-presente { border-color: #bbf7d0; }
.chip-presente .chip-num { color: #15803d; }

.chip-ausente { border-color: #fecaca; }
.chip-ausente .chip-num { color: #dc2626; }

.chip-sinmarcar { border-color: #e5e7eb; }

/* ── Tabla ── */

.table-container {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.roster-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.roster-table thead {
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.roster-table th {
  padding: 0.85rem 1rem;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  color: #6b7280;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
}

.roster-table td {
  padding: 0.85rem 1rem;
  color: #374151;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}

.roster-table tbody tr:last-child td { border-bottom: none; }
.roster-table tbody tr:hover { background: #fafafa; }

.cell-name { font-weight: 600; color: #111827; }

/* ── Badges ── */

.source-badge {
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 5px;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  white-space: nowrap;
}

.estado-badge {
  display: inline-block;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.2rem 0.65rem;
  white-space: nowrap;
}

.badge-presente  { background: #dcfce7; color: #15803d; }
.badge-ausente   { background: #fee2e2; color: #dc2626; }
.badge-sinmarcar { background: #f3f4f6; color: #9ca3af; }

/* ── Botones de acción ── */

.cell-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn-mark {
  border-radius: 6px;
  border: 1.5px solid transparent;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.3rem 0.75rem;
  transition: background-color 0.12s, border-color 0.12s, color 0.12s;
  white-space: nowrap;
}

.btn-presente {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #15803d;
}
.btn-presente:hover         { background: #dcfce7; border-color: #86efac; }
.btn-presente.active        { background: #15803d; border-color: #15803d; color: white; }
.btn-presente.active:hover  { background: #166534; }

.btn-ausente {
  background: #fff5f5;
  border-color: #fecaca;
  color: #dc2626;
}
.btn-ausente:hover        { background: #fee2e2; border-color: #fca5a5; }
.btn-ausente.active       { background: #dc2626; border-color: #dc2626; color: white; }
.btn-ausente.active:hover { background: #b91c1c; }

.btn-borrar {
  background: transparent;
  border: 1.5px solid #d1d5db;
  border-radius: 6px;
  color: #9ca3af;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 700;
  padding: 0.3rem 0.6rem;
  transition: background-color 0.12s, border-color 0.12s, color 0.12s;
}
.btn-borrar:hover { background: #fee2e2; border-color: #fca5a5; color: #dc2626; }

.saving-indicator {
  color: #9ca3af;
  font-size: 0.8rem;
  font-style: italic;
}

.save-error {
  color: #dc2626;
  font-size: 0.75rem;
}
</style>
