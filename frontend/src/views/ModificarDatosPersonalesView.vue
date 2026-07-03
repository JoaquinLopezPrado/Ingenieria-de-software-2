<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { extractBackendError } from '@/services/sessionService'

const router = useRouter()
const authStore = useAuthStore()

const phone = ref('')
const isSaving = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const user = computed(() => authStore.user)

const profile = computed(() => {
  return user.value?.client_profile ?? user.value?.profile ?? null
})

const firstName = computed(() => {
  return profile.value?.first_name ?? ''
})

const lastName = computed(() => {
  return profile.value?.last_name ?? ''
})

const email = computed(() => {
  return user.value?.email ?? ''
})

const fullName = computed(() => {
  const name = `${firstName.value} ${lastName.value}`.trim()
  return name || 'Cliente'
})

onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchUser()
  }

  phone.value = profile.value?.phone ?? ''
})

async function guardarCambios() {
  const cleanPhone = phone.value.trim()

  successMessage.value = ''
  errorMessage.value = ''

  if (!cleanPhone) {
    errorMessage.value = 'El teléfono es obligatorio.'
    return
  }

  if (!/^\d+$/.test(cleanPhone)) {
    errorMessage.value = 'El teléfono debe contener solo números.'
    return
  }

  isSaving.value = true

  try {
    await authStore.updateMyPhone(cleanPhone)
    phone.value = profile.value?.phone ?? cleanPhone
    successMessage.value = 'Tus datos fueron actualizados correctamente.'
  } catch (err) {
    errorMessage.value =
      extractBackendError(err) ?? 'No se pudo actualizar el teléfono.'
  } finally {
    isSaving.value = false
  }
}

function volver() {
  router.push('/')
}
</script>

<template>
  <main class="page">
    <section class="card">
      <div class="header">
        <div>
          <h1 class="title">Modificar datos personales</h1>
          <p class="subtitle">
            Podés consultar tus datos personales y modificar únicamente tu teléfono.
          </p>
        </div>

        <button
          type="button"
          class="btn-secondary"
          @click="volver"
        >
          Volver
        </button>
      </div>

      <div v-if="successMessage" class="message success-message">
        {{ successMessage }}
      </div>

      <div v-if="errorMessage" class="message error-message">
        {{ errorMessage }}
      </div>

      <form class="form" @submit.prevent="guardarCambios">
        <div class="form-grid">
          <div class="form-group">
            <label class="form-label" for="first_name">Nombre</label>
            <input
              id="first_name"
              class="form-input disabled-input"
              type="text"
              :value="firstName"
              disabled
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="last_name">Apellido</label>
            <input
              id="last_name"
              class="form-input disabled-input"
              type="text"
              :value="lastName"
              disabled
            />
          </div>

          <div class="form-group full-width">
            <label class="form-label" for="email">Email</label>
            <input
              id="email"
              class="form-input disabled-input"
              type="email"
              :value="email"
              disabled
            />
          </div>

          <div class="form-group full-width">
            <label class="form-label" for="phone">Teléfono</label>
            <input
              id="phone"
              v-model="phone"
              class="form-input"
              type="text"
              inputmode="numeric"
              placeholder="Ingresá tu teléfono"
              autocomplete="tel"
            />
          </div>
        </div>

        <div class="actions">
          <button
            type="button"
            class="btn-secondary"
            :disabled="isSaving"
            @click="volver"
          >
            Cancelar
          </button>

          <button
            type="submit"
            class="btn-primary"
            :disabled="isSaving"
          >
            {{ isSaving ? 'Guardando...' : 'Guardar cambios' }}
          </button>
        </div>
      </form>
    </section>
  </main>
</template>

<style scoped>
.page {
  min-height: calc(100vh - 70px);
  background: #f8fafc;
  padding: 2rem;
  box-sizing: border-box;

  display: flex;
  align-items: center;
  justify-content: center;
}

.card {
  width: 100%;
  max-width: 980px;
  margin: 0 auto;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
  box-sizing: border-box;
}

.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.6rem;
}

.title {
  margin: 0 0 0.35rem 0;
  color: #111827;
  font-size: 1.45rem;
  font-weight: 800;
}

.subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 0.92rem;
  line-height: 1.45;
}

.message {
  margin-bottom: 1rem;
  padding: 0.8rem 1rem;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
}

.success-message {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.error-message {
  background: #fff5f5;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.form {
  margin-top: 1rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 1.5rem;
  row-gap: 1.2rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  min-width: 0;
}

.full-width {
  grid-column: 1 / -1;
}

.form-label {
  color: #374151;
  font-size: 0.85rem;
  font-weight: 700;
}

.form-input {
  width: 100%;
  box-sizing: border-box;
  height: 46px;
  border: 1px solid #d1d5db;
  border-radius: 9px;
  padding: 0 0.85rem;
  color: #374151;
  background: white;
  font-size: 0.92rem;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.form-input:focus {
  border-color: #11998e;
  box-shadow: 0 0 0 3px rgba(17, 153, 142, 0.12);
}

.disabled-input {
  background: #f3f4f6;
  color: #6b7280;
  cursor: not-allowed;
}

.field-help {
  margin: 0.15rem 0 0 0;
  color: #6b7280;
  font-size: 0.78rem;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.8rem;
}

.btn-primary,
.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  padding: 0.65rem 1.1rem;
  border-radius: 9px;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.15s, transform 0.12s, opacity 0.12s;
  box-sizing: border-box;
}

.btn-primary {
  background: #11998e;
  color: white;
  border: 1px solid #11998e;
}

.btn-primary:hover:not(:disabled) {
  background: #0c8a70;
  transform: translateY(-1px);
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .page {
    padding: 1rem;
  }

  .card {
    padding: 1.2rem;
  }

  .header {
    flex-direction: column;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .actions {
    flex-direction: column-reverse;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
  }
}
</style>