<template>
  <div class="home-page">
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand-block">
          <h1 class="logo">SIEMPREGYM</h1>
          <p class="role-chip">
            {{ roleLabel }}
          </p>
        </div>
      </div>
    </header>

    <main class="home-content">
      <div v-if="googleLinked" class="banner banner-success">
        Tu cuenta de Google fue vinculada correctamente.
      </div>
      <div v-if="googleAlreadyInUse" class="banner banner-error">
        Esta cuenta de Google ya está asociada a otro usuario. Por favor, utilizá una cuenta diferente.
      </div>
      <div v-if="googleUnlinked" class="banner banner-success">
        Tu cuenta de Google fue desvinculada correctamente.
      </div>
      <div v-if="googleLinkError" class="banner banner-error">
        No se pudo vincular la cuenta de Google. Intentá de nuevo.
      </div>
      <div v-if="googleUnlinkError" class="banner banner-error">
        No se pudo desvincular la cuenta de Google. Intentá de nuevo.
      </div>
      <section class="hero-card">
        <div class="hero-text">
          <p class="eyebrow">Panel principal</p>

          <h2>
            Bienvenido/a{{ displayName ? `, ${displayName}` : '' }}
          </h2>

          <p class="hero-description">
            Desde acá podés consultar los turnos disponibles para tus actividades.
          </p>
        </div>
      </section>

      <section v-if="isClient" class="section-block centered-section">

        <div class="actions-grid centered-grid">
          <article
            v-for="action in clientActions"
            :key="action.title"
            class="action-card"
            @click="goTo(action.path)"
          >
            <div class="card-icon">
              {{ action.icon }}
            </div>

            <h4>{{ action.title }}</h4>

            <p>{{ action.description }}</p>

            <span class="card-link">Ir a la sección</span>
          </article>
        </div>
      </section>

      <section v-else class="section-block">
        <div class="empty-role-card">
          <h3>Vista en construcción</h3>

          <p>
            Por ahora esta home está enfocada en la experiencia del cliente.
            Más adelante podés agregar la vista de administrador y empleado
            en este mismo archivo.
          </p>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const googleLinked = ref(route.query.google_linked === 'true')
const googleAlreadyInUse = ref(route.query.error === 'google_already_in_use')
const googleLinkError = ref(route.query.error === 'google_link_failed')
const googleUnlinked = ref(route.query.google_unlinked === 'true')
const googleUnlinkError = ref(route.query.error === 'google_unlink_failed')

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
  if (roleName.value === 'cliente' || roleName.value === 'client') {
    return 'Cliente'
  }

  if (roleName.value === 'admin' || roleName.value === 'administrador') {
    return 'Administrador'
  }

  if (roleName.value === 'empleado' || roleName.value === 'employee') {
    return 'Empleado'
  }

  return 'Usuario'
})

const displayName = computed(() => {
  const firstName = authStore.user?.first_name ?? ''
  const lastName = authStore.user?.last_name ?? ''

  const fullName = `${firstName} ${lastName}`.trim()

  return (
    fullName ||
    firstName ||
    authStore.user?.name ||
    authStore.user?.username ||
    authStore.user?.email ||
    ''
  )
})

const clientActions = [
  {
    title: 'Ver turnos disponibles',
    description:
      'Consultá los turnos de actividad disponibles para inscribirte.',
    icon: '🗓️',
    path: '/list',
  },
]

function goTo(path: string) {
  router.push(path)
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #d9eeea;
  display: flex;
  flex-direction: column;
  padding-top: 60px;
}

.topbar {
  width: 100%;
  padding: 20px 20px 12px;
}

.topbar-inner {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.brand-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.logo {
  margin: 0;
  color: #0d9b8a;
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.role-chip {
  width: fit-content;
  margin: 0;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(13, 155, 138, 0.12);
  color: #0d9b8a;
  font-size: 0.92rem;
  font-weight: 700;
}

.home-content {
  width: 100%;
  max-width: 980px;
  margin: 0 auto;
  padding: 20px 20px 48px;
  display: flex;
  flex-direction: column;
  gap: 36px;
}

.hero-card {
  width: 100%;
  max-width: 760px;
  margin: 0 auto;
  background: white;
  border-radius: 28px;
  padding: 32px 36px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
}

.hero-text {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.eyebrow {
  margin: 0;
  color: #0d9b8a;
  font-size: 0.9rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.hero-text h2 {
  margin: 0;
  color: #1f2937;
  font-size: 2rem;
  line-height: 1.15;
}

.hero-description {
  margin: 0;
  color: #6b7280;
  font-size: 1rem;
  line-height: 1.5;
  max-width: 540px;
}

.section-block {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.centered-section {
  align-items: center;
}

.centered-header {
  text-align: center;
  max-width: 700px;
}

.section-header h3 {
  margin: 0 0 6px;
  color: #1f2937;
  font-size: 1.35rem;
}

.section-header p {
  margin: 0;
  color: #6b7280;
  line-height: 1.45;
}

.actions-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.centered-grid {
  width: 100%;
  display: flex;
  justify-content: center;
}

.action-card {
  width: 100%;
  max-width: 360px;
  background: white;
  border-radius: 24px;
  padding: 24px 20px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.10);
}

.card-icon {
  width: 48px;
  height: 48px;
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

.empty-role-card {
  background: white;
  border-radius: 24px;
  padding: 24px 20px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.06);
}

.banner {
  border-radius: 12px;
  padding: 14px 18px;
  font-size: 14px;
  font-weight: 500;
}

.banner-success {
  background-color: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

.banner-error {
  background-color: #fff5f5;
  color: #c0392b;
  border: 1px solid #fecaca;
}

.empty-role-card h3 {
  display: block;
  margin-bottom: 8px;
  color: #1f2937;
  font-size: 1.02rem;
}

.empty-role-card p {
  margin: 0;
  color: #6b7280;
  line-height: 1.45;
}

@media (max-width: 768px) {
  .topbar-inner {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-card {
    padding: 26px 22px;
    border-radius: 22px;
  }

  .hero-text h2 {
    font-size: 1.65rem;
  }
}
</style>