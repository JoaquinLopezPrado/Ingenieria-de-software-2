<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'

const route  = useRoute()
const router = useRouter()
const turnoId = route.params.id
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <div class="page-header">
        <div>
          <h1 class="page-title">Modificar Turno #{{ turnoId }}</h1>
          <p class="page-subtitle">Editá los datos del turno seleccionado</p>
        </div>
        <button class="btn-secondary" @click="router.push({ name: 'turnos-grilla' })">
          ← Volver a la grilla
        </button>
      </div>

      <div class="placeholder-card">
        <div class="placeholder-icon">🚧</div>
        <h2 class="placeholder-title">Funcionalidad en desarrollo</h2>
        <p class="placeholder-desc">
          La edición de turnos aún no está implementada.<br>
          Este botón ya está conectado — cuando el formulario de edición esté listo,
          se cargará acá con los datos del turno <strong>#{{ turnoId }}</strong>.
        </p>
      </div>

    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper {
  width: 100%;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 2rem;
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
  transition: background-color 0.15s;
}

.btn-secondary:hover {
  background-color: #e5e7eb;
}

.placeholder-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 4rem 2rem;
  background: #fefce8;
  border: 2px dashed #fbbf24;
  border-radius: 12px;
  text-align: center;
}

.placeholder-icon {
  font-size: 2.5rem;
  line-height: 1;
}

.placeholder-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #92400e;
  margin: 0;
}

.placeholder-desc {
  font-size: 0.9rem;
  color: #78350f;
  margin: 0;
  max-width: 440px;
  line-height: 1.6;
}
</style>
