<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { getClienteById, type Cliente } from '@/services/clientesService'
import { extractBackendError } from '@/services/sessionService'

const route = useRoute()
const clienteId = Number(route.params.clienteId)

const cliente = ref<Cliente | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    cliente.value = await getClienteById(clienteId)
  } catch (err) {
    error.value = extractBackendError(err) ?? 'No se pudo cargar la ficha del cliente.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AdminLayout>
    <div class="ficha-page">
      <header class="page-header">
        <RouterLink :to="{ name: 'lista-alumnos' }" class="back-link">← Volver</RouterLink>
        <h1 class="page-title">Ficha del cliente</h1>
      </header>

      <div v-if="loading" class="state-box">
        <p class="state-text">Cargando...</p>
      </div>

      <div v-else-if="error" class="state-box error-box">
        <p class="state-text">{{ error }}</p>
      </div>

      <template v-else-if="cliente">
        <div class="ficha-card">
          <div class="avatar">
            {{ cliente.first_name.charAt(0) }}{{ cliente.last_name.charAt(0) }}
          </div>

          <div class="ficha-info">
            <h2 class="cliente-name">{{ cliente.first_name }} {{ cliente.last_name }}</h2>

            <dl class="info-list">
              <div class="info-row">
                <dt class="info-label">Documento</dt>
                <dd class="info-value">{{ cliente.doc_type_name }} {{ cliente.doc_number }}</dd>
              </div>
              <div class="info-row">
                <dt class="info-label">Email</dt>
                <dd class="info-value">{{ cliente.email }}</dd>
              </div>
              <div class="info-row">
                <dt class="info-label">Teléfono</dt>
                <dd class="info-value">{{ cliente.phone }}</dd>
              </div>
            </dl>
          </div>
        </div>

        <div class="actions">
          <RouterLink
            :to="`/clientes/${clienteId}/asistencias`"
            class="action-btn"
          >
            Ver historial de asistencias
          </RouterLink>
          <RouterLink
            :to="`/clientes/${clienteId}/inscripciones`"
            class="action-btn"
          >
            Ver inscripciones activas
          </RouterLink>
        </div>
      </template>
    </div>
  </AdminLayout>
</template>

<style scoped>
.ficha-page {
  max-width: 680px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}

.back-link {
  display: inline-block;
  color: #6b7280;
  text-decoration: none;
  font-size: 0.88rem;
  margin-bottom: 0.75rem;
  transition: color 0.15s;
}

.back-link:hover {
  color: #0d9b8a;
}

.page-title {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 700;
  color: #111827;
}

.state-box {
  background: white;
  border-radius: 16px;
  padding: 2.5rem;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.error-box {
  border: 1px solid #fecaca;
  background: #fff5f5;
}

.state-text {
  margin: 0;
  color: #6b7280;
  font-size: 0.98rem;
}

.error-box .state-text {
  color: #dc2626;
}

.ficha-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  display: flex;
  align-items: flex-start;
  gap: 1.5rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border: 1px solid #f3f4f6;
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #d1fae5;
  color: #065f46;
  font-size: 1.3rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  text-transform: uppercase;
}

.ficha-info {
  flex: 1;
  min-width: 0;
}

.cliente-name {
  margin: 0 0 1rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
}

.info-row {
  display: flex;
  gap: 1rem;
  align-items: baseline;
}

.info-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  width: 90px;
  flex-shrink: 0;
}

.info-value {
  font-size: 0.95rem;
  color: #374151;
  margin: 0;
}

.actions {
  margin-top: 1.5rem;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #0d9b8a;
  color: white;
  text-decoration: none;
  padding: 0.75rem 1.5rem;
  border-radius: 999px;
  font-size: 0.9rem;
  font-weight: 600;
  transition: background-color 0.15s;
}

.action-btn:hover {
  background: #0a8070;
}
</style>
