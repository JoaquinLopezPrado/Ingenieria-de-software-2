<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import {
  listEmpleados,
  createEmpleado,
  updateEmpleado,
  deactivateEmpleado,
  reactivateEmpleado,
  type Empleado,
} from '@/services/empleadosService'
import { extractBackendError } from '@/services/sessionService'

// ─── Estado principal ─────────────────────────────────────────────────────────

const empleados = ref<Empleado[]>([])
const loading = ref(true)
const pageError = ref<string | null>(null)

// ─── Modal crear/editar ───────────────────────────────────────────────────────

const modalOpen = ref(false)
const editingEmpleado = ref<Empleado | null>(null)

const form = ref({ email: '', first_name: '', last_name: '', phone: '' })
const formError = ref<string | null>(null)
const formLoading = ref(false)

function openCreateModal() {
  editingEmpleado.value = null
  form.value = { email: '', first_name: '', last_name: '', phone: '' }
  formError.value = null
  modalOpen.value = true
}

function openEditModal(emp: Empleado) {
  editingEmpleado.value = emp
  form.value = {
    email: emp.email,
    first_name: emp.first_name,
    last_name: emp.last_name,
    phone: emp.phone ?? '',
  }
  formError.value = null
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
}

async function submitForm() {
  formError.value = null

  const phone = form.value.phone.trim() || undefined
  if (phone && !/^\d+$/.test(phone)) {
    formError.value = 'El teléfono debe contener solo números.'
    return
  }

  formLoading.value = true
  try {
    if (editingEmpleado.value) {
      const updated = await updateEmpleado(editingEmpleado.value.id, {
        first_name: form.value.first_name.trim(),
        last_name: form.value.last_name.trim(),
        phone,
      })
      const idx = empleados.value.findIndex(e => e.id === updated.id)
      if (idx !== -1) empleados.value[idx] = updated
    } else {
      const created = await createEmpleado({
        email: form.value.email.trim(),
        first_name: form.value.first_name.trim(),
        last_name: form.value.last_name.trim(),
        phone,
      })
      empleados.value.push(created)
    }
    closeModal()
  } catch (err) {
    formError.value = extractBackendError(err) ?? 'Ocurrió un error. Intentá de nuevo.'
  } finally {
    formLoading.value = false
  }
}

// ─── Desactivar ───────────────────────────────────────────────────────────────

const confirmingId = ref<number | null>(null)
const deactivateLoading = ref(false)

function askDeactivate(id: number) {
  confirmingId.value = id
}

function cancelDeactivate() {
  confirmingId.value = null
}

async function confirmDeactivate() {
  if (confirmingId.value === null) return
  deactivateLoading.value = true
  try {
    await deactivateEmpleado(confirmingId.value)
    const emp = empleados.value.find(e => e.id === confirmingId.value)
    if (emp) emp.is_active = false
    confirmingId.value = null
  } catch (err) {
    pageError.value = extractBackendError(err) ?? 'No se pudo desactivar el empleado.'
  } finally {
    deactivateLoading.value = false
  }
}

// ─── Reactivar ────────────────────────────────────────────────────────────────

const reactivateLoadingId = ref<number | null>(null)

async function handleReactivate(id: number) {
  reactivateLoadingId.value = id
  try {
    await reactivateEmpleado(id)
    const emp = empleados.value.find(e => e.id === id)
    if (emp) emp.is_active = true
  } catch (err) {
    pageError.value = extractBackendError(err) ?? 'No se pudo reactivar el empleado.'
  } finally {
    reactivateLoadingId.value = null
  }
}

// ─── Carga inicial ────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    empleados.value = await listEmpleados()
  } catch (err) {
    pageError.value = extractBackendError(err) ?? 'No se pudo cargar la lista de empleados.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AdminLayout>
    <div class="emp-page">
      <header class="page-header">
        <h1 class="page-title">Empleados</h1>
        <button class="create-btn" @click="openCreateModal">+ Nuevo empleado</button>
      </header>

      <div v-if="pageError" class="state-box error-box">
        <p class="state-text">{{ pageError }}</p>
      </div>

      <div v-if="loading" class="state-box">
        <p class="state-text">Cargando...</p>
      </div>

      <template v-else-if="!pageError">
        <div v-if="empleados.length === 0" class="state-box">
          <p class="state-text">No hay empleados registrados.</p>
        </div>

        <div v-else class="table-wrapper">
          <table class="emp-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Email</th>
                <th>Teléfono</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="emp in empleados" :key="emp.id" :class="{ inactive: !emp.is_active }">
                <td class="name-cell">{{ emp.first_name }} {{ emp.last_name }}</td>
                <td class="email-cell">{{ emp.email }}</td>
                <td class="phone-cell">{{ emp.phone ?? '—' }}</td>
                <td>
                  <span :class="['status-badge', emp.is_active ? 'badge-active' : 'badge-inactive']">
                    {{ emp.is_active ? 'Activo' : 'Inactivo' }}
                  </span>
                </td>
                <td class="actions-cell">
                  <button class="action-btn edit-btn" @click="openEditModal(emp)">Editar</button>
                  <button
                    v-if="emp.is_active"
                    class="action-btn deact-btn"
                    @click="askDeactivate(emp.id)"
                  >
                    Desactivar
                  </button>
                  <button
                    v-else
                    class="action-btn react-btn"
                    :disabled="reactivateLoadingId === emp.id"
                    @click="handleReactivate(emp.id)"
                  >
                    {{ reactivateLoadingId === emp.id ? 'Reactivando...' : 'Reactivar' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>

    <!-- ─── Modal crear / editar ─────────────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal">
        <div class="modal">
          <h2 class="modal-title">{{ editingEmpleado ? 'Editar empleado' : 'Nuevo empleado' }}</h2>

          <form class="modal-form" @submit.prevent="submitForm">
            <div v-if="!editingEmpleado" class="field">
              <label class="field-label">Email</label>
              <input
                v-model="form.email"
                type="email"
                class="field-input"
                placeholder="empleado@centro.com"
                required
              />
            </div>

            <div v-if="editingEmpleado" class="field">
              <label class="field-label">Email</label>
              <p class="field-readonly">{{ form.email }}</p>
            </div>

            <div class="field-row">
              <div class="field">
                <label class="field-label">Nombre</label>
                <input v-model="form.first_name" type="text" class="field-input" required />
              </div>
              <div class="field">
                <label class="field-label">Apellido</label>
                <input v-model="form.last_name" type="text" class="field-input" required />
              </div>
            </div>

            <div class="field">
              <label class="field-label">Teléfono <span class="optional">(opcional)</span></label>
              <input v-model="form.phone" type="text" inputmode="numeric" class="field-input" placeholder="1123456789" />
            </div>

            <div v-if="formError" class="form-error">{{ formError }}</div>

            <p v-if="!editingEmpleado" class="welcome-note">
              Se enviará un mail al empleado con un link para que establezca su contraseña.
            </p>

            <div class="modal-actions">
              <button type="button" class="cancel-btn" @click="closeModal">Cancelar</button>
              <button type="submit" class="submit-btn" :disabled="formLoading">
                {{ formLoading ? 'Guardando...' : editingEmpleado ? 'Guardar cambios' : 'Crear empleado' }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- ─── Confirm desactivar ───────────────────────────────────────── -->
      <div v-if="confirmingId !== null" class="modal-backdrop" @click.self="cancelDeactivate">
        <div class="modal modal-sm">
          <h2 class="modal-title">Desactivar empleado</h2>
          <p class="confirm-text">
            El empleado ya no podrá ingresar al sistema. Sus datos se conservan y podés reactivarlo cuando quieras desde esta misma pantalla.
          </p>
          <div class="modal-actions">
            <button type="button" class="cancel-btn" @click="cancelDeactivate">Cancelar</button>
            <button
              type="button"
              class="submit-btn danger-btn"
              :disabled="deactivateLoading"
              @click="confirmDeactivate"
            >
              {{ deactivateLoading ? 'Desactivando...' : 'Confirmar' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </AdminLayout>
</template>

<style scoped>
.emp-page { max-width: 900px; margin: 0 auto; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.75rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-title { margin: 0; font-size: 1.6rem; font-weight: 700; color: #111827; }

.create-btn {
  background: #0d9b8a;
  color: white;
  border: none;
  padding: 0.65rem 1.25rem;
  border-radius: 999px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s;
}
.create-btn:hover { background: #0a8070; }

.state-box {
  background: white;
  border-radius: 16px;
  padding: 2.5rem;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
  border: 1px solid #f3f4f6;
}
.error-box { border-color: #fecaca; background: #fff5f5; }
.state-text { margin: 0; color: #6b7280; font-size: 0.98rem; }
.error-box .state-text { color: #dc2626; }

.table-wrapper {
  background: white;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
  border: 1px solid #f3f4f6;
}
.emp-table { width: 100%; border-collapse: collapse; }
.emp-table th {
  background: #f9fafb;
  padding: 0.85rem 1.25rem;
  text-align: left;
  font-size: 0.78rem;
  font-weight: 700;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  border-bottom: 1px solid #f3f4f6;
}
.emp-table td {
  padding: 0.9rem 1.25rem;
  font-size: 0.92rem;
  color: #374151;
  border-bottom: 1px solid #f9fafb;
  vertical-align: middle;
}
.emp-table tbody tr:last-child td { border-bottom: none; }
.emp-table tbody tr:hover td { background: #f9fafb; }
.emp-table tbody tr.inactive td { opacity: 0.55; }
.emp-table tbody tr.inactive td.actions-cell { opacity: 1; }

.name-cell { font-weight: 600; color: #111827; }
.email-cell { color: #6b7280; font-size: 0.88rem; }
.phone-cell { color: #6b7280; }
.actions-cell { white-space: nowrap; }

.status-badge {
  display: inline-block;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}
.badge-active { background: #d1fae5; color: #065f46; }
.badge-inactive { background: #f3f4f6; color: #6b7280; }

.action-btn {
  border: none;
  padding: 0.35rem 0.8rem;
  border-radius: 6px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  margin-left: 0.4rem;
  transition: opacity 0.15s;
}
.edit-btn { background: #e0f2fe; color: #0369a1; }
.edit-btn:hover { opacity: 0.8; }
.deact-btn { background: #fee2e2; color: #dc2626; }
.deact-btn:hover { opacity: 0.8; }
.react-btn { background: #dcfce7; color: #15803d; }
.react-btn:hover:not(:disabled) { opacity: 0.8; }
.react-btn:disabled { cursor: not-allowed; }

/* ─── Modal ─────────────────────────────────────────────────────────────── */

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 1rem;
}

.modal {
  background: white;
  border-radius: 20px;
  padding: 2rem;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
}
.modal-sm { max-width: 380px; }

.modal-title {
  margin: 0 0 1.5rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
}

.modal-form { display: flex; flex-direction: column; gap: 1rem; }

.field { display: flex; flex-direction: column; gap: 0.4rem; }
.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }

.field-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.optional { font-weight: 400; text-transform: none; color: #9ca3af; }

.field-input {
  height: 40px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0 0.85rem;
  font-size: 0.92rem;
  color: #111827;
  outline: none;
  transition: border-color 0.15s;
}
.field-input:focus { border-color: #0d9b8a; }

.field-readonly {
  margin: 0;
  padding: 0.6rem 0.85rem;
  background: #f9fafb;
  border: 1px solid #f3f4f6;
  border-radius: 8px;
  font-size: 0.92rem;
  color: #6b7280;
}

.form-error {
  background: #fff5f5;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 0.65rem 0.9rem;
  color: #dc2626;
  font-size: 0.88rem;
}

.welcome-note {
  margin: 0;
  font-size: 0.83rem;
  color: #6b7280;
  background: #f0fdf9;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
  padding: 0.65rem 0.9rem;
}

.confirm-text { color: #374151; font-size: 0.95rem; line-height: 1.6; margin: 0 0 1.5rem; }

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.cancel-btn {
  height: 38px;
  padding: 0 1.1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  color: #6b7280;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}
.cancel-btn:hover { border-color: #0d9b8a; color: #0d9b8a; }

.submit-btn {
  height: 38px;
  padding: 0 1.25rem;
  border: none;
  border-radius: 8px;
  background: #0d9b8a;
  color: white;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s;
}
.submit-btn:hover:not(:disabled) { background: #0a8070; }
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.danger-btn { background: #dc2626; }
.danger-btn:hover:not(:disabled) { background: #b91c1c; }
</style>
