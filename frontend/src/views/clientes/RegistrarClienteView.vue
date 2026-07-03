<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import RegisterForm from '@/components/auth/RegisterForm.vue'
import { createCliente } from '@/services/clientesService'
import { extractBackendError } from '@/services/sessionService'

const router = useRouter()

const loading = ref(false)
const apiError = ref('')
const successMessage = ref('')
const showPasswordRequirements = ref(true)

async function handleRegister(userData: any) {
  loading.value = true
  apiError.value = ''
  successMessage.value = ''

  try {
    await createCliente(userData)

    successMessage.value = 'Cliente registrado correctamente.'

    setTimeout(() => {
      router.push('/clientes')
    }, 800)
  } catch (err) {
    apiError.value =
      extractBackendError(err) ?? 'No se pudo registrar el cliente.'
  } finally {
    loading.value = false
  }
}

function volverAlListado() {
  router.push('/clientes')
}
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">
      <div class="page-header">
        <div>
          <h1 class="page-title">Registrar cliente</h1>
          <p class="page-subtitle">
            Cargá los datos del nuevo cliente para registrarlo en el sistema.
          </p>
        </div>
      </div>

      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>

      <div class="form-card">
        <RegisterForm
          :loading="loading"
          :api-error="apiError"
          :show-password-requirements="showPasswordRequirements"
          :show-google-register="false"
          :allow-minor-with-permission="true"
          submit-label="Registrar cliente"
          @submit="handleRegister"
        />

        <div class="volver-wrapper">
          <button
            type="button"
            class="btn-volver-listado"
            @click="volverAlListado"
          >
            Volver al listado
          </button>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper {
  width: 100%;
  max-width: 760px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 1.5rem;
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

.form-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 1.5rem;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}

.success-message {
  margin-bottom: 1rem;
  padding: 0.8rem 1rem;
  border-radius: 10px;
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
  font-size: 0.9rem;
  font-weight: 600;
}

/* Achica el botón principal del RegisterForm solo en esta pantalla */
:deep(button[type="submit"]) {
  width: 50%;
  margin-left: auto;
  margin-right: auto;
  display: flex;
  justify-content: center;
}

/* Volver al listado justo debajo del botón Registrar cliente */
.volver-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 0.75rem;
}

.btn-volver-listado {
  width: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: #f3f4f6;
  color: #374151;
  font-size: 0.9rem;
  font-weight: 700;
  padding: 0.75rem 1.4rem;
  border-radius: 30px;
  border: 1px solid #d1d5db;
  cursor: pointer;
  text-decoration: none;
  transition: background-color 0.15s, transform 0.12s, box-shadow 0.15s;
}

.btn-volver-listado:hover {
  background-color: #e5e7eb;
  transform: translateY(-1px);
}

.btn-volver-listado:active {
  transform: translateY(0);
}

@media (max-width: 640px) {
  .page-wrapper {
    max-width: 100%;
  }

  .form-card {
    padding: 1rem;
  }

  :deep(button[type="submit"]) {
    width: 100%;
  }

  .btn-volver-listado {
    width: 100%;
  }
}
</style>