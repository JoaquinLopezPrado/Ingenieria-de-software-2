<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import {
  getActivityById,
  updateActivity,
  extractBackendError,
} from '@/services/sessionService'

const route  = useRoute()
const router = useRouter()
const id     = Number(route.params.id)

const isLoading   = ref(true)
const isSaving    = ref(false)
const loadError   = ref('')
const serverError = ref('')
const successMsg  = ref('')

const form = ref({ name: '', description: '' })
const errors = ref<Record<string, string>>({})

onMounted(async () => {
  try {
    const activity = await getActivityById(id)
    form.value = {
      name:        activity.name,
      description: activity.description ?? '',
    }
  } catch (e: unknown) {
    loadError.value = extractBackendError(e)
  } finally {
    isLoading.value = false
  }
})

function validate(): boolean {
  errors.value = {}
  if (!form.value.name.trim())
    errors.value.name = 'El nombre es un campo requerido.'
  return Object.keys(errors.value).length === 0
}

async function handleSubmit() {
  serverError.value = ''
  if (!validate()) return

  isSaving.value = true
  try {
    await updateActivity(id, {
      name:        form.value.name.trim(),
      description: form.value.description.trim(),
    })
    successMsg.value = 'Actividad actualizada con éxito.'
    setTimeout(() => router.push({ name: 'lista-actividades' }), 1500)
  } catch (e: unknown) {
    serverError.value = extractBackendError(e)
  } finally {
    isSaving.value = false
  }
}

function cancelEdit() {
  router.push({ name: 'lista-actividades' })
}
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <!-- ── Encabezado ── -->
      <div class="page-header">
        <div class="header-left">
          <button class="btn-back" @click="cancelEdit">← Volver</button>
          <div>
            <h1 class="page-title">Editar actividad</h1>
            <p class="page-subtitle">Modificá los datos de la actividad y guardá los cambios</p>
          </div>
        </div>
      </div>

      <!-- ── Cargando ── -->
      <div v-if="isLoading" class="skeleton-wrapper">
        <div class="skeleton-row" style="width: 220px; height: 32px;"></div>
        <div class="skeleton-row" style="height: 260px; margin-top: 0.5rem;"></div>
      </div>

      <!-- ── Error de carga ── -->
      <div v-else-if="loadError" class="state-panel state-error">
        <div class="state-icon">⚠</div>
        <h2 class="state-title">No se pudo cargar la actividad</h2>
        <p class="state-desc">{{ loadError }}</p>
        <button class="btn-secondary" @click="router.go(0)">Reintentar</button>
      </div>

      <!-- ── Formulario ── -->
      <template v-else>

        <Transition name="fade">
          <div v-if="successMsg" class="alert alert-success">
            <span class="alert-icon success-icon">✓</span>
            <span>{{ successMsg }}</span>
          </div>
        </Transition>

        <Transition name="fade">
          <div v-if="serverError" class="alert alert-error">
            <span class="alert-icon error-icon">!</span>
            <span>{{ serverError }}</span>
            <button class="alert-close" @click="serverError = ''">×</button>
          </div>
        </Transition>

        <div class="form-card">
          <form @submit.prevent="handleSubmit" novalidate>

            <div class="input-group">
              <label for="nombre">Nombre</label>
              <input
                id="nombre"
                type="text"
                v-model="form.name"
                maxlength="120"
                placeholder="Nombre de la actividad"
                :class="{ 'input-error': errors.name }"
              />
              <span v-if="errors.name" class="field-error">{{ errors.name }}</span>
            </div>

            <div class="input-group">
              <label for="descripcion">Descripción</label>
              <textarea
                id="descripcion"
                v-model="form.description"
                maxlength="500"
                rows="4"
                placeholder="Descripción de la actividad (opcional)"
              ></textarea>
            </div>

            <div class="form-actions">
              <button
                type="button"
                class="btn-cancel"
                :disabled="isSaving"
                @click="cancelEdit"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="btn-submit"
                :disabled="isSaving"
              >
                {{ isSaving ? 'Guardando...' : 'Aceptar' }}
              </button>
            </div>

          </form>
        </div>

      </template>

    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper { width: 100%; }

.page-header { display: flex; align-items: flex-start; margin-bottom: 1.75rem; }
.header-left { display: flex; align-items: flex-start; gap: 1rem; }

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
.btn-back:hover { background-color: #f3f4f6; color: #374151; }

.page-title    { font-size: 1.5rem; font-weight: 700; color: #1f2937; margin: 0 0 0.2rem 0; }
.page-subtitle { color: #6b7280; font-size: 0.88rem; margin: 0; }

.skeleton-wrapper { display: flex; flex-direction: column; gap: 0.75rem; }

.skeleton-row {
  border-radius: 8px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.state-panel {
  display: flex; flex-direction: column; align-items: center;
  gap: 0.75rem; padding: 4rem 2rem; border-radius: 12px; text-align: center;
}
.state-error   { background: #fff5f5; border: 1px solid #fecaca; }
.state-icon    { font-size: 2.5rem; line-height: 1; }
.state-title   { font-size: 1.05rem; font-weight: 700; margin: 0; color: #991b1b; }
.state-desc    { font-size: 0.9rem; color: #7f1d1d; margin: 0; max-width: 420px; }

.alert {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.9rem 1.25rem; border-radius: 10px;
  font-size: 0.9rem; font-weight: 500; margin-bottom: 1.25rem;
}
.alert-success { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
.alert-error   { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }

.alert-icon {
  width: 1.4rem; height: 1.4rem; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.78rem; font-weight: 700; flex-shrink: 0;
}
.success-icon { background: #16a34a; color: white; }
.error-icon   { background: #dc2626; color: white; }

.alert-close {
  margin-left: auto; background: none; border: none; font-size: 1.4rem;
  cursor: pointer; color: inherit; opacity: 0.5; transition: opacity 0.15s;
}
.alert-close:hover { opacity: 1; }

.form-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 2rem 2.5rem;
  max-width: 680px;
}

.input-group { margin-bottom: 1.5rem; }

label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 0.45rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

input[type="text"],
textarea {
  width: 100%;
  padding: 0.7rem 0.9rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #fafafa;
  font-size: 0.95rem;
  color: #1f2937;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s, background-color 0.2s;
  font-family: inherit;
  resize: vertical;
}

input:focus, textarea:focus {
  border-color: #11998e;
  background-color: #fff;
  box-shadow: 0 0 0 3px rgba(17, 153, 142, 0.15);
}

.input-error {
  border-color: #ef4444 !important;
  background-color: #fff5f5 !important;
}

.field-error {
  display: block; margin-top: 0.35rem;
  font-size: 0.78rem; color: #dc2626; font-weight: 500;
}

.form-actions {
  display: flex; justify-content: flex-end; gap: 0.75rem;
  padding-top: 1.5rem; margin-top: 0.5rem;
  border-top: 1px solid #f3f4f6;
}

.btn-cancel {
  background: #f3f4f6; color: #374151; font-size: 0.9rem; font-weight: 600;
  padding: 0.7rem 1.5rem; border-radius: 8px; border: 1px solid #d1d5db;
  cursor: pointer; transition: background-color 0.15s;
}
.btn-cancel:hover:not(:disabled) { background: #e5e7eb; }
.btn-cancel:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-submit {
  background: #11998e; color: white; font-weight: 600; font-size: 0.95rem;
  padding: 0.7rem 2rem; border-radius: 8px; border: none; cursor: pointer;
  min-width: 120px; transition: background-color 0.2s;
}
.btn-submit:hover:not(:disabled) { background: #0c8a70; }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-secondary {
  background: #f3f4f6; color: #374151; font-size: 0.88rem; font-weight: 600;
  padding: 0.6rem 1.4rem; border-radius: 8px; border: 1px solid #d1d5db;
  cursor: pointer; transition: background-color 0.15s;
}
.btn-secondary:hover { background: #e5e7eb; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.25s, transform 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-6px); }

@media (max-width: 480px) {
  .form-card { padding: 1.5rem 1.25rem; }
  .form-actions { flex-direction: column-reverse; }
  .btn-submit, .btn-cancel { width: 100%; }
}
</style>
