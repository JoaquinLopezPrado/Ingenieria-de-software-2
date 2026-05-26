<script setup lang="ts">
/**
 * EditActividadView — Placeholder para HU Modificar Actividad
 * -----------------------------------------------------------
 * Vista pendiente de implementación.
 */
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'

const route  = useRoute()
const router = useRouter()
const id     = route.params.id
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">
      <div class="page-header">
        <div>
          <h1 class="page-title">Editar Actividad</h1>
          <p class="page-subtitle">Actividad #{{ id }}</p>
        </div>
      </div>

      <div class="placeholder-panel">
        <div class="placeholder-icon">🚧</div>
        <h2 class="placeholder-title">Vista en construcción</h2>
        <p class="placeholder-desc">
          La funcionalidad para editar actividades está pendiente de implementación.
        </p>
        <button class="btn-back" @click="router.push({ name: 'lista-actividades' })">
          ← Volver al listado
        </button>
      </div>
    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper { width: 100%; }

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

.placeholder-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.85rem;
  padding: 4rem 2rem;
  border-radius: 12px;
  text-align: center;
  background-color: #f9fafb;
  border: 2px dashed #d1d5db;
}

.placeholder-icon { font-size: 2.8rem; line-height: 1; }

.placeholder-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #374151;
  margin: 0;
}

.placeholder-desc {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
  max-width: 380px;
}

.btn-back {
  margin-top: 0.5rem;
  background-color: #f3f4f6;
  color: #374151;
  font-size: 0.9rem;
  font-weight: 600;
  padding: 0.65rem 1.5rem;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-back:hover { background-color: #e5e7eb; }
</style>
