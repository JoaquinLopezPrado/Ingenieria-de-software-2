<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { useInscripcionStore } from '@/stores/inscripcionStore'
import { buscarClientePorDni } from '@/services/inscripcionService'
import { extractBackendError } from '@/services/sessionService'
import type { Cliente } from '@/services/inscripcionService'

const router = useRouter()
const inscripcionStore = useInscripcionStore()

const docNumber = ref('')
const isLoading = ref(false)
const clienteEncontrado = ref<Cliente | null>(null)
const errorMessage = ref<string | null>(null)
const validationError = ref<string | null>(null)

function validate(): boolean {
  const val = docNumber.value.trim()
  if (!val) {
    validationError.value = 'El DNI es requerido'
    return false
  }
  if (!/^\d+$/.test(val)) {
    validationError.value = 'El DNI debe contener solo números'
    return false
  }
  validationError.value = null
  return true
}

async function handleBuscar() {
  if (!validate()) return

  clienteEncontrado.value = null
  errorMessage.value = null
  isLoading.value = true

  try {
    clienteEncontrado.value = await buscarClientePorDni(docNumber.value.trim())
  } catch (err) {
    errorMessage.value = extractBackendError(err)
  } finally {
    isLoading.value = false
  }
}

function handleInput() {
  // Limpiar resultados y errores previos mientras el usuario escribe
  if (validationError.value) validationError.value = null
  if (clienteEncontrado.value) clienteEncontrado.value = null
  if (errorMessage.value) errorMessage.value = null
}

function handleContinuar() {
  if (!clienteEncontrado.value) return
  inscripcionStore.setCliente(clienteEncontrado.value)
  router.push({ name: 'inscripciones-turnos' })
}

function getInitials(cliente: Cliente): string {
  return `${cliente.first_name[0]}${cliente.last_name[0]}`.toUpperCase()
}
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <div class="page-header">
        <div>
          <h1 class="page-title">Inscripciones</h1>
          <p class="page-subtitle">Buscá al cliente por DNI para iniciar el proceso de inscripción</p>
        </div>
      </div>

      <div class="search-card">
        <h2 class="card-title">Buscar cliente</h2>

        <div class="search-row">
          <div class="field-wrapper">
            <label for="dni-input" class="field-label">Número de DNI</label>
            <input
              id="dni-input"
              v-model="docNumber"
              type="text"
              inputmode="numeric"
              placeholder="Ej: 12345678"
              class="dni-input"
              :class="{ 'dni-input--error': validationError }"
              :disabled="isLoading"
              maxlength="20"
              @input="handleInput"
              @keyup.enter="handleBuscar"
            />
            <p v-if="validationError" class="field-error">{{ validationError }}</p>
          </div>

          <button
            type="button"
            class="btn-buscar"
            :disabled="isLoading"
            @click="handleBuscar"
          >
            <span v-if="isLoading" class="spinner" aria-hidden="true"></span>
            {{ isLoading ? 'Buscando...' : 'Buscar' }}
          </button>
        </div>

        <div v-if="errorMessage" class="error-banner" role="alert">
          <span class="error-icon" aria-hidden="true">!</span>
          {{ errorMessage }}
        </div>
      </div>

      <div v-if="clienteEncontrado" class="cliente-card">
        <div class="cliente-header">
          <div class="cliente-avatar" aria-hidden="true">
            {{ getInitials(clienteEncontrado) }}
          </div>
          <div class="cliente-identity">
            <h3 class="cliente-name">
              {{ clienteEncontrado.first_name }} {{ clienteEncontrado.last_name }}
            </h3>
            <p class="cliente-doc">
              {{ clienteEncontrado.doc_type_name }} {{ clienteEncontrado.doc_number }}
            </p>
          </div>
        </div>

        <div class="cliente-fields">
          <div class="cliente-field">
            <span class="field-key">Correo electrónico</span>
            <span class="field-val">{{ clienteEncontrado.email }}</span>
          </div>
          <div class="cliente-field">
            <span class="field-key">Teléfono</span>
            <span class="field-val">{{ clienteEncontrado.phone }}</span>
          </div>
        </div>

        <div class="cliente-actions">
          <button
            type="button"
            class="btn-continuar"
            @click="handleContinuar"
          >
            Continuar al listado de turnos →
          </button>
        </div>
      </div>

    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper {
  width: 100%;
  max-width: 680px;
}

.page-header {
  margin-bottom: 2rem;
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

/* ─── Search card ─────────────────────────────── */

.search-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 700;
  color: #0d3027;
  margin: 0 0 1.5rem 0;
}

.search-row {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
}

.field-wrapper {
  flex: 1;
  min-width: 0;
}

.field-label {
  display: block;
  font-size: 0.82rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.4rem;
  letter-spacing: 0.02em;
}

.dni-input {
  width: 100%;
  box-sizing: border-box;
  padding: 0.7rem 1rem;
  border: 1.5px solid #d1d5db;
  border-radius: 10px;
  font-size: 0.95rem;
  color: #1f2937;
  background: #f9fafb;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.dni-input:focus {
  border-color: #18b4a3;
  box-shadow: 0 0 0 3px rgba(24, 180, 163, 0.12);
  background: white;
}

.dni-input--error {
  border-color: #dc2626;
}

.dni-input--error:focus {
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
}

.dni-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.field-error {
  margin: 0.35rem 0 0;
  font-size: 0.8rem;
  color: #dc2626;
  font-weight: 500;
}

.btn-buscar {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.72rem 1.5rem;
  background-color: #18b4a3;
  color: white;
  font-size: 0.92rem;
  font-weight: 600;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.15s;
  flex-shrink: 0;
  height: 42px;
}

.btn-buscar:hover:not(:disabled) {
  background-color: #0d9b8a;
}

.btn-buscar:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg) }
}

.error-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  margin-top: 1.25rem;
  padding: 0.85rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  color: #991b1b;
  font-size: 0.88rem;
  font-weight: 500;
}

.error-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: #dc2626;
  color: white;
  border-radius: 50%;
  font-size: 0.7rem;
  font-weight: 800;
  flex-shrink: 0;
  margin-top: 1px;
}

/* ─── Cliente card ────────────────────────────── */

.cliente-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1.5px solid #a7f3d0;
  animation: slide-in 0.2s ease;
}

@keyframes slide-in {
  from { opacity: 0; transform: translateY(8px) }
  to   { opacity: 1; transform: translateY(0) }
}

.cliente-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.cliente-avatar {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #11998e, #0d9b8a);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  font-weight: 700;
  flex-shrink: 0;
}

.cliente-identity {
  min-width: 0;
}

.cliente-name {
  margin: 0 0 0.2rem;
  font-size: 1.15rem;
  font-weight: 700;
  color: #0f172a;
}

.cliente-doc {
  margin: 0;
  font-size: 0.85rem;
  color: #6b7280;
  font-weight: 500;
}

.cliente-fields {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.25rem;
  background: #f9fafb;
  border-radius: 10px;
  margin-bottom: 1.5rem;
}

.cliente-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.field-key {
  font-size: 0.82rem;
  color: #6b7280;
  font-weight: 600;
  flex-shrink: 0;
}

.field-val {
  font-size: 0.88rem;
  color: #1f2937;
  font-weight: 500;
  text-align: right;
  word-break: break-all;
}

.cliente-actions {
  display: flex;
  justify-content: flex-end;
}

.btn-continuar {
  padding: 0.75rem 1.75rem;
  background-color: #0d3027;
  color: white;
  font-size: 0.92rem;
  font-weight: 600;
  border: none;
  border-radius: 999px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-continuar:hover {
  background-color: #18b4a3;
}

@media (max-width: 520px) {
  .search-row {
    flex-direction: column;
    align-items: stretch;
  }

  .btn-buscar {
    width: 100%;
    justify-content: center;
  }

  .cliente-field {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.15rem;
  }

  .field-val {
    text-align: left;
  }
}
</style>
