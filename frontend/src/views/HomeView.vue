<template>
  <div class="home-page" :class="{ leaving: isLeaving }">
    <header class="topbar">
      <div class="brand-block">
        <h1 class="logo">SIEMPREGYM</h1>
        <p class="role-chip">
          {{ roleLabel }}
        </p>
      </div>

      <button class="logout-btn" @click="goToLogout" :disabled="isLeaving">
        {{ isLeaving ? 'Saliendo...' : 'Cerrar sesión' }}
      </button>
    </header>

    <main class="home-content">
      <section class="hero-card">
        <div class="hero-text">
          <p class="eyebrow">Panel principal</p>
          <h2>Bienvenido/a{{ displayName ? `, ${displayName}` : '' }}</h2>
          <p class="hero-description">
            Desde acá podés gestionar tus clases y reservas de forma simple.
          </p>
        </div>
      </section>

      <section v-if="isClient" class="section-block">
        <div class="section-header">
          <h3>Acciones rápidas</h3>
          <p>Estas son las funciones principales disponibles para clientes en este sprint.</p>
        </div>

        <div class="actions-grid">
          <article
            v-for="action in clientActions"
            :key="action.title"
            class="action-card"
            @click="goTo(action.path)"
          >
            <div class="card-icon">{{ action.icon }}</div>
            <h4>{{ action.title }}</h4>
            <p>{{ action.description }}</p>
            <span class="card-link">Ir a la sección</span>
          </article>
        </div>
      </section>

      <section v-if="isClient" class="section-block">
        <div class="section-header">
          <h3>Resumen rápido</h3>
          <p>Un acceso simple para que el cliente entienda qué puede hacer dentro del sistema.</p>
        </div>

        <div class="summary-grid">
          <article class="summary-card">
            <span class="summary-label">Turnos</span>
            <strong>Consultar disponibles</strong>
            <p>Visualizá los turnos y elegí el que mejor te convenga.</p>
          </article>

          <article class="summary-card">
            <span class="summary-label">Reserva</span>
            <strong>Inscribite a una actividad</strong>
            <p>Elegí un turno y avanzá con tu inscripción desde la app.</p>
          </article>

          <article class="summary-card">
            <span class="summary-label">Clase individual</span>
            <strong>Reservá una clase</strong>
            <p>Solicitá tu clase individual desde un acceso directo.</p>
          </article>
        </div>
      </section>

      <section v-else class="section-block">
        <div class="empty-role-card">
          <h3>Vista en construcción</h3>
          <p>
            Por ahora esta home está enfocada en la experiencia del cliente. Más adelante
            podés agregar la vista de administrador y empleado en este mismo archivo.
          </p>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const authStore = useAuthStore()
const isLeaving = ref(false)

function normalizeRole(user: any): string {
  const rawRole =
    user?.role?.name ??
    user?.role_name ??
    user?.role ??
    ''

  return String(rawRole).trim().toLowerCase()
}

const roleName = computed(() => normalizeRole(authStore.user))

const isClient = computed(() => {
  return roleName.value === 'cliente' || roleName.value === 'client'
})

const roleLabel = computed(() => {
  if (roleName.value === 'cliente' || roleName.value === 'client') return 'Cliente'
  if (roleName.value === 'admin' || roleName.value === 'administrador') return 'Administrador'
  if (roleName.value === 'empleado' || roleName.value === 'employee') return 'Empleado'
  return 'Usuario'
})

const displayName = computed(() => {
  return (
    authStore.user?.first_name ??
    authStore.user?.name ??
    authStore.user?.email ??
    ''
  )
})

const clientActions = [
  {
    title: 'Ver turnos disponibles',
    description: 'Consultá los turnos de actividad disponibles para inscribirte.',
    icon: '📅',
    path: '/turnos',
  },
  {
    title: 'Inscribirme a un turno',
    description: 'Reservá un turno de actividad desde tu cuenta.',
    icon: '✅',
    path: '/inscripciones/nueva',
  },
  {
    title: 'Reservar clase individual',
    description: 'Solicitá una clase individual de forma rápida.',
    icon: '🎯',
    path: '/clase-individual',
  },
]

function goTo(path: string) {
  router.push(path)
}

function goToLogout() {
  isLeaving.value = true

  setTimeout(() => {
    router.push('/logout')
  }, 180)
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #d9eeea;
  display: flex;
  flex-direction: column;
  transition: opacity 0.18s ease, transform 0.18s ease;
  opacity: 1;
}

.home-page.leaving {
  opacity: 0;
  transform: scale(0.995);
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 24px 20px 12px;
}

.brand-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.logo {
  margin: 0;
  color: #0d9b8a;
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.role-chip {
  width: fit-content;
  margin: 0;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(13, 155, 138, 0.12);
  color: #0d9b8a;
  font-size: 0.9rem;
  font-weight: 700;
}

.logout-btn {
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  background: #20b2a6;
  color: white;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 8px 18px rgba(32, 178, 166, 0.22);
}

.logout-btn:hover {
  background: #189c92;
}

.logout-btn:disabled {
  opacity: 0.8;
  cursor: default;
}

.home-content {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  padding: 12px 20px 32px;
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.hero-card {
  background: white;
  border-radius: 28px;
  padding: 28px 24px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
}

.eyebrow {
  margin: 0 0 8px;
  color: #0d9b8a;
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.hero-text h2 {
  margin: 0 0 10px;
  color: #1f2937;
  font-size: 1.8rem;
}

.hero-description {
  margin: 0;
  color: #6b7280;
  font-size: 1rem;
  line-height: 1.5;
}

.section-block {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.section-header h3 {
  margin: 0 0 6px;
  color: #1f2937;
  font-size: 1.25rem;
}

.section-header p {
  margin: 0;
  color: #6b7280;
  line-height: 1.45;
}

.actions-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.action-card {
  background: white;
  border-radius: 24px;
  padding: 22px 20px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.10);
}

.card-icon {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(24, 180, 163, 0.12);
  font-size: 1.35rem;
  margin-bottom: 14px;
}

.action-card h4 {
  margin: 0 0 8px;
  color: #1f2937;
  font-size: 1.08rem;
}

.action-card p {
  margin: 0 0 14px;
  color: #6b7280;
  line-height: 1.45;
}

.card-link {
  color: #0d9b8a;
  font-weight: 700;
  font-size: 0.95rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.summary-card,
.empty-role-card {
  background: white;
  border-radius: 24px;
  padding: 22px 20px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.06);
}

.summary-label {
  display: inline-block;
  margin-bottom: 8px;
  color: #0d9b8a;
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.summary-card strong,
.empty-role-card h3 {
  display: block;
  margin-bottom: 8px;
  color: #1f2937;
  font-size: 1.02rem;
}

.summary-card p,
.empty-role-card p {
  margin: 0;
  color: #6b7280;
  line-height: 1.45;
}

@media (min-width: 768px) {
  .topbar {
    padding: 28px 32px 16px;
    align-items: center;
  }

  .home-content {
    padding: 16px 32px 40px;
  }

  .actions-grid,
  .summary-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>