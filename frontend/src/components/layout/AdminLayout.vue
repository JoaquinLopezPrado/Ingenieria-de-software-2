<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { isAdminUser } from '@/utils/role'

const authStore = useAuthStore()
const isAdmin = computed(() => isAdminUser(authStore.user))
</script>

<template>
  <div class="admin-wrapper">

    <!-- =========================================================
         SIDEBAR
         Barra lateral fija con navegación principal.
         Los RouterLink detectan la ruta activa automáticamente
         y aplican la clase CSS "active" sin lógica extra.
    ========================================================= -->
    <aside class="sidebar">

      <!-- Logo y nombre del centro -->
      <div class="brand-header">
        <div class="logo-circle">A</div>
        <div class="brand-text">
          <h2 class="brand-title">Centro Activo</h2>
          <p class="brand-subtitle">Tu bienestar, nuestra meta</p>
        </div>
      </div>

      <!-- Menú de navegación -->
      <nav class="sidebar-nav">

        <div class="nav-group">
          <p class="nav-label">PRINCIPAL</p>
          <!-- RouterLink aplica "active" cuando la ruta coincide exactamente -->
          <RouterLink to="/admin" class="nav-item" active-class="active" exact>
            <span class="nav-icon">⊞</span> Inicio
          </RouterLink>
          <a href="#" class="nav-item">
            <span class="nav-icon">☰</span> Inscripciones
          </a>
          <a href="#" class="nav-item">
            <span class="nav-icon">◎</span> Alumnos
          </a>
          <RouterLink to="/activities" class="nav-item" active-class="active">
            <span class="nav-icon">◈</span> Actividades
          </RouterLink>
        </div>

        <div class="nav-group">
          <p class="nav-label">ADMINISTRACIÓN</p>
          <a href="#" class="nav-item">
            <span class="nav-icon">▦</span> Reportes
          </a>
          <RouterLink to="/activities/turnos" class="nav-item" active-class="active">
            <span class="nav-icon">◷</span> Grilla de Turnos
          </RouterLink>
          <a href="#" class="nav-item">
            <span class="nav-icon">✓</span> Asistencia
          </a>
          <a href="#" class="nav-item">
            <span class="nav-icon">⚙</span> Configuración
          </a>
        </div>

      </nav>

      <!-- Usuario autenticado -->
      <div class="user-footer">
        <div class="logo-circle small">AG</div>
        <div class="brand-text">
          <p class="user-name">Administrador</p>
          <p class="user-email">admin@centroactivo.ar</p>
        </div>
      </div>

    </aside>

    <!-- =========================================================
         CONTENIDO PRINCIPAL
         El slot recibe el contenido de cada vista.
         El padding horizontal se adapta al tamaño de pantalla.
    ========================================================= -->
    <main class="main-content">
      <slot></slot>
    </main>

  </div>
</template>

<style scoped>
/* Layout raíz: sidebar fijo + contenido fluido */
.admin-wrapper {
  display: flex;
  min-height: 100vh;
  background-color: #f3f4f6;
}

/* ───────────── SIDEBAR ───────────── */

.sidebar {
  width: 260px;
  flex-shrink: 0;
  background-color: #0d3027;
  color: white;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: calc(100vh - 60px);
  left: 0;
  top: 60px;
  overflow-y: auto;
}

.brand-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 2rem 1.5rem;
}

.logo-circle {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 50%;
  border: 2px solid #11998e;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.1rem;
  color: #11998e;
}

.logo-circle.small {
  width: 34px;
  height: 34px;
  font-size: 0.85rem;
}

.brand-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  white-space: nowrap;
}

.brand-subtitle {
  margin: 0;
  font-size: 0.72rem;
  color: #8fa8a2;
  white-space: nowrap;
}

.sidebar-nav {
  flex-grow: 1;
  padding: 0.5rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  overflow-y: auto;
}

.nav-label {
  font-size: 0.68rem;
  font-weight: 700;
  color: #8fa8a2;
  letter-spacing: 1.2px;
  margin: 0 0 0.6rem 0;
  padding-left: 0.75rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  color: #d1dadd;
  text-decoration: none;
  padding: 0.7rem 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
  margin-bottom: 0.15rem;
  transition: background-color 0.15s, color 0.15s;
}

.nav-item:hover {
  background-color: rgba(17, 153, 142, 0.15);
  color: white;
}

/* Clase aplicada por RouterLink cuando la ruta está activa */
.nav-item.active {
  background-color: #11998e;
  color: white;
  font-weight: 600;
}

.nav-icon {
  font-size: 0.95rem;
  width: 1.2rem;
  text-align: center;
  flex-shrink: 0;
}

.user-footer {
  padding: 1.25rem 1.5rem;
  background-color: #0a251e;
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.user-name {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 600;
}

.user-email {
  margin: 0;
  font-size: 0.72rem;
  color: #8fa8a2;
}

/* ───────────── MAIN CONTENT ───────────── */

.main-content {
  flex-grow: 1;
  margin-left: 260px; /* Deja el espacio exacto del sidebar fijo */
  padding: 60px 2.5rem 2rem 2.5rem;
  min-width: 0; /* Evita que el contenido desborde en pantallas chicas */
}

/* En tablets (sidebar colapsado via scroll) */
@media (max-width: 768px) {
  .sidebar {
    width: 220px;
  }
  .main-content {
    margin-left: 220px;
    padding: 60px 1.5rem 1.5rem 1.5rem;
  }
}
</style>
