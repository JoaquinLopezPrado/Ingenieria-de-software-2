<script setup lang="ts">
/**
 * HomeDispatcherView — Redirige al home según el rol del usuario.
 * ---------------------------------------------------------------
 * Montado en la ruta raíz "/". No renderiza nada visual; solo
 * evalúa el rol en el auth store y hace push a la ruta correcta.
 *
 * admin / Admin / Administrador → /admin  (admin-home)
 * cualquier otro rol             → /cliente (cliente-home)
 *
 * Nota: la redirección se hace en setup (síncronamente) para evitar
 * el parpadeo que ocurriría si se hiciera en onMounted.
 */
import { onMounted }    from 'vue'
import { useRouter }    from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router    = useRouter()
const authStore = useAuthStore()

onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchUser()
  }
  const role    = authStore.user?.role ?? ''
  const isAdmin = ['admin', 'Admin', 'Administrador'].includes(role)
  router.replace({ name: isAdmin ? 'admin-home' : 'cliente-home' })
})
</script>

<template>
  <!-- Pantalla en blanco mínima mientras se resuelve la redirección -->
  <div></div>
</template>
