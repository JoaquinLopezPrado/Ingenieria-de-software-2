<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import EmployeeLayout from '@/components/layout/EmployeeLayout.vue'

const router = useRouter()
const authStore = useAuthStore()

const firstName = computed(() => {
  const p = authStore.user?.employee_profile ?? authStore.user?.client_profile
  return p?.first_name ?? authStore.user?.email ?? 'empleado'
})

const accesos = [
  {
    title: 'Asistencias de hoy',
    description: 'Ver las clases del día y marcar la asistencia de los alumnos.',
    icon: '✓',
    path: '/empleado/clases',
  },
  {
    title: 'Escáner QR',
    description: 'Escanear el QR del alumno para registrar su ingreso automáticamente.',
    icon: '▣',
    path: '/scanner',
  },
  {
    title: 'Alumnos',
    description: 'Buscar clientes y ver su perfil, inscripciones y asistencias.',
    icon: '◎',
    path: '/clientes',
  },
  {
    title: 'Seguridad',
    description: 'Cambiar tu contraseña.',
    icon: '⚙',
    path: '/admin/configuracion',
  },
]
</script>

<template>
  <EmployeeLayout>
    <div class="home-content">
      <div class="welcome-card">
        <p class="eyebrow">Panel del empleado</p>
        <h1 class="welcome-title">Bienvenido/a, {{ firstName }}</h1>
        <p class="welcome-sub">Desde acá podés gestionar asistencias y alumnos.</p>
      </div>

      <div class="accesos-grid">
        <div
          v-for="acceso in accesos"
          :key="acceso.path"
          class="acceso-card"
          @click="router.push(acceso.path)"
        >
          <div class="acceso-icon">{{ acceso.icon }}</div>
          <h3 class="acceso-title">{{ acceso.title }}</h3>
          <p class="acceso-desc">{{ acceso.description }}</p>
          <span class="acceso-link">Ir →</span>
        </div>
      </div>
    </div>
  </EmployeeLayout>
</template>

<style scoped>
.home-content {
  display: flex;
  flex-direction: column;
  gap: 28px;
  max-width: 860px;
}

.welcome-card {
  background: white;
  border-radius: 20px;
  padding: 28px 32px;
  box-shadow: 0 4px 18px rgba(0,0,0,0.06);
}
.eyebrow {
  margin: 0 0 6px;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #0d9b8a;
}
.welcome-title { margin: 0 0 8px; font-size: 1.8rem; font-weight: 800; color: #1f2937; }
.welcome-sub { margin: 0; color: #6b7280; font-size: 0.95rem; }

.accesos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.acceso-card {
  background: white;
  border-radius: 18px;
  padding: 22px 20px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.acceso-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 22px rgba(0,0,0,0.1);
}
.acceso-icon {
  width: 44px;
  height: 44px;
  background: rgba(13,155,138,0.1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  color: #0d9b8a;
  margin-bottom: 4px;
}
.acceso-title { margin: 0; font-size: 1rem; font-weight: 700; color: #1f2937; }
.acceso-desc { margin: 0; font-size: 0.85rem; color: #6b7280; line-height: 1.45; flex-grow: 1; }
.acceso-link { font-size: 0.85rem; font-weight: 700; color: #0d9b8a; }
</style>
