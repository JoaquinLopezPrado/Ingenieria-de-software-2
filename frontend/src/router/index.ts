import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { isAdminUser, isEmployeeUser, isStaffUser } from '@/utils/role'
import { useInscripcionStore } from '@/stores/inscripcionStore'


import ScheduleSessionView from '@/views/activities/ScheduleSessionView.vue'
import GrillaTurnosView from '@/views/activities/GrillaTurnosView.vue'
import EditTurnoView from '@/views/activities/EditTurnoView.vue'
import ListaActividadesView from '@/views/activities/ListaActividadesView.vue'
import EditActividadView from '@/views/activities/EditActividadView.vue'
import AlumnoInscripcionesView from '@/views/clientes/AlumnoInscripcionesView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/admin',
      name: 'admin-home',
      component: () => import('../views/AdminHomeView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/configuracion',
      name: 'admin-configuracion',
      component: () => import('../views/AdminSecurityView.vue'),
      meta: { requiresAuth: true, requiresStaff: true },
    },
    {
      path: '/mi-cuenta',
      name: 'mi-cuenta',
      component: () => import('../views/ClientSecurityView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('../views/ForgotPasswordView.vue'),
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: () => import('../views/ResetPasswordView.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/list',
      name: 'list',
      component: () => import('../views/ShowActivitisView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/ticket',
      name: 'ticket',
      component: () => import('../views/TicketView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/payment/success',
      name: 'payment-success',
      component: () => import('../views/PaymentSuccessView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/payment/failure',
      name: 'payment-failure',
      component: () => import('../views/PaymentFailureView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/payment/pending',
      name: 'payment-pending',
      component: () => import('../views/PaymentPendingView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/activities',
      name: 'lista-actividades',
      component: ListaActividadesView,
      meta: { requiresAuth: true, requiresAdmin: true, adminLayout: true },
    },
    {
      path: '/activities/turnos',
      name: 'turnos-grilla',
      component: GrillaTurnosView,
      meta: { requiresAuth: true, requiresAdmin: true, adminLayout: true },
    },
    {
      path: '/activities/schedule',
      name: 'schedule-session',
      component: ScheduleSessionView,
      meta: { requiresAuth: true, requiresAdmin: true, adminLayout: true },
    },
    {
      path: '/activities/:id/edit',
      name: 'editar-actividad',
      component: EditActividadView,
      meta: { requiresAuth: true, requiresAdmin: true, adminLayout: true },
    },
    {
      path: '/activities/turnos/:id/edit',
      name: 'edit-turno',
      component: EditTurnoView,
      meta: { requiresAuth: true, requiresAdmin: true, adminLayout: true },
    },
    {
      path: '/activities/turnos/:id/clases',
      name: 'clases-calendario',
      component: () => import('../views/activities/ClasesCalendarioView.vue'),
      meta: { requiresAuth: true, requiresStaff: true },
    },
    {
      path: '/activities/clases/:claseId/asistencias',
      name: 'clase-asistencias',
      component: () => import('../views/activities/AsistenciasClaseView.vue'),
      meta: { requiresAuth: true, requiresStaff: true },
    },
    {
      path: '/auth/callback',
      name: 'auth-callback',
      component: () => import('../views/GoogleCallbackView.vue'),
    },
    {
      path: '/auth/google-complete',
      name: 'google-complete',
      component: () => import('../views/GoogleCompleteView.vue'),
    },
    {
      path: '/logout',
      name: 'logout',
      component: () => import('../views/LogoutView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/class-selection',
      name: 'class-selection',
      component: () => import('../views/ClassSelectionView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/asistencias',
      name: 'asistencias',
      component: () => import('../views/AsistenciasView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/mi-qr',
      name: 'mi-qr',
      component: () => import('../views/MiQRView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/scanner',
      name: 'scanner',
      component: () => import('../views/ScannerView.vue'),
      meta: { requiresAuth: true, requiresStaff: true }
    },
    {
      path: '/inscripciones',
      name: 'inscripciones',
      component: () => import('../views/InscripcionesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/clientes/:clienteId/pagos',
      name: 'cliente-pagos',
      component: () => import('../views/PagoCliente.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/pagos',
      name: 'pagos',
      component: () => import('../views/PagosView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/empleado',
      name: 'employee-home',
      component: () => import('../views/EmployeeHomeView.vue'),
      meta: { requiresAuth: true, requiresStaff: true },
    },
    {
      path: '/empleado/clases',
      name: 'empleado-clases',
      component: () => import('../views/ClasesHoyView.vue'),
      meta: { requiresAuth: true, requiresStaff: true },
    },
    {
      path: '/report',
      name: 'report',
      component: () => import('../views/ReportsView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/empleados',
      name: 'admin-empleados',
      component: () => import('../views/admin/EmpleadosView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/suscripciones',
      name: 'admin-suscripciones',
      component: () => import('../views/admin/AdminSuscripcionesView.vue'),
      meta: { requiresAuth: true, requiresStaff: true },
    },
    {
      path: '/clientes',
      name: 'lista-alumnos',
      component: () => import('../views/clientes/ListaAlumnosView.vue'),
      meta: { requiresAuth: true, requiresStaff: true },
    },
    {
      path: '/clientes/registrar',
      name: 'registrar-cliente-admin',
      component: () => import('../views/clientes/RegistrarClienteView.vue'),
      meta: { requiresAuth: true, requiresStaff: true },
    },
    {
      path: '/clientes/:clienteId',
      name: 'ficha-cliente',
      component: () => import('../views/clientes/FichaClienteView.vue'),
      meta: { requiresAuth: true, requiresStaff: true },
    },
    {
      path: '/clientes/:clienteId/asistencias',
      name: 'historial-asistencias',
      component: () => import('../views/clientes/HistorialAsistenciasView.vue'),
      meta: { requiresAuth: true, requiresStaff: true },
    },
    {
      path: '/clientes/:clienteId/inscripciones',
      name: 'cliente-inscripciones',
      component: AlumnoInscripcionesView,
      meta: { requiresAuth: true, requiresStaff: true }
    },
    {
      path: '/clientes/:clienteId/inscripciones/turnos',
      name: 'clientes-inscripciones-turnos',
      component: () => import('../views/inscripciones/ListaTurnosView.vue'),
      meta: { requiresAuth: true, requiresStaff: true, clienteInscripcionFlow: true },
    },
    {
      path: '/clientes/:clienteId/inscripciones/turnos/:turnoId/inscribir',
      name: 'clientes-inscripciones-inscribir',
      component: () => import('../views/inscripciones/InscribirView.vue'),
      meta: { requiresAuth: true, requiresStaff: true, clienteInscripcionFlow: true },
    },
    {
      path: '/clientes/:clienteId/inscripciones/turnos/:turnoId/lista-espera',
      name: 'clientes-inscripciones-lista-espera',
      component: () => import('../views/inscripciones/ListaEsperaView.vue'),
      meta: { requiresAuth: true, requiresStaff: true, clienteInscripcionFlow: true },
    },
    {
      path: '/inscripciones',
      component: () => import('../views/inscripciones/InscripcionesLayout.vue'),
      meta: { requiresAuth: true, requiresStaff: true, inscripcionesFlow: true },
      children: [
        {
          path: '',
          name: 'inscripciones-buscar-cliente',
          component: () => import('../views/inscripciones/BuscarClienteView.vue'),
        },
        {
          path: 'turnos',
          name: 'inscripciones-turnos',
          component: () => import('../views/inscripciones/ListaTurnosView.vue'),
        },
        {
          path: 'turnos/:turnoId/inscribir',
          name: 'inscripciones-inscribir',
          component: () => import('../views/inscripciones/InscribirView.vue'),
        },
        {
          path: 'turnos/:turnoId/lista-espera',
          name: 'inscripciones-lista-espera',
          component: () => import('../views/inscripciones/ListaEsperaView.vue'),
        },
      ],
    },
    // Flujo de clase individual — rutas independientes (NO hijas del parent inscripcionesFlow)
    // para que el guard de clienteSeleccionado del flujo de turnos no interfiera.
    {
      path: '/inscripciones/clases',
      name: 'inscripciones-clases',
      component: () => import('../views/inscripciones/CalendarioClasesInscripcionView.vue'),
      meta: { requiresAuth: true, requiresStaff: true, claseFlow: true },
    },
    {
      path: '/inscripciones/clases/:claseId/inscribir',
      name: 'inscripciones-inscribir-clase',
      component: () => import('../views/inscripciones/InscribirClaseView.vue'),
      meta: { requiresAuth: true, requiresStaff: true, claseFlow: true },
    },
    {
      path: '/mis-datos',
      name: 'modificar-datos-personales',
      component: () => import('../views/ModificarDatosPersonalesView.vue'),
      meta: { requiresAuth: true },
    }
  ]
})

const publicRouteNames = new Set(['login', 'register', 'forgot-password', 'reset-password', 'auth-callback', 'google-complete'])

router.beforeEach(async (to: RouteLocationNormalized, from: RouteLocationNormalized) => {
  // Limpiar el flujo de inscripciones al salir del módulo
  // No resetear si se navega hacia el flujo de clase individual (comparte el cliente seleccionado)
  if (from.meta.inscripcionesFlow && !to.meta.inscripcionesFlow && !to.meta.claseFlow) {
    useInscripcionStore().reset()
  }

  // Limpiar el flujo cliente-first al salir del módulo
  if (from.meta.clienteInscripcionFlow && !to.meta.clienteInscripcionFlow) {
    useInscripcionStore().reset()
  }

  // Limpiar el flujo de clase individual al salir
  if (from.meta.claseFlow && !to.meta.claseFlow) {
    useInscripcionStore().reset()
  }

  const authStore = useAuthStore()
  const hasAccessToken = Boolean(localStorage.getItem('access_token'))
  const isPublicRoute = typeof to.name === 'string' && publicRouteNames.has(to.name)

  if (hasAccessToken && !authStore.user) {
    await authStore.fetchUser().catch(() => { })
  }

  const isAuthenticated = Boolean(localStorage.getItem('access_token'))
  const isAdmin = isAdminUser(authStore.user)
  const isEmployee = isEmployeeUser(authStore.user)
  const isStaff = isStaffUser(authStore.user)

  if (!isAuthenticated && !isPublicRoute) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.meta.requiresAdmin && !isAdmin) {
    return { name: isEmployee ? 'employee-home' : 'list' }
  }

  // Rutas marcadas como requiresStaff son accesibles por admin y empleado
  if (to.meta.requiresStaff && !isStaff) {
    return { name: 'list' }
  }

  if (isAuthenticated && isEmployee && !to.meta.requiresStaff && !isPublicRoute && to.name !== 'employee-home') {
    return { name: 'employee-home' }
  }

  // Guard de flujo: redirigir al paso correcto si falta el estado previo
  if (to.meta.inscripcionesFlow && to.name !== 'inscripciones-buscar-cliente') {
    const inscripcionStore = useInscripcionStore()
    if (!inscripcionStore.clienteSeleccionado) {
      return { name: 'inscripciones-buscar-cliente' }
    }
    if (
      (to.name === 'inscripciones-inscribir' || to.name === 'inscripciones-lista-espera') &&
      !inscripcionStore.turnoSeleccionado
    ) {
      return { name: 'inscripciones-turnos' }
    }
  }

  // Guard flujo cliente-first: requiere turnoSeleccionado para confirmar o lista de espera
  if (to.meta.clienteInscripcionFlow) {
    const inscripcionStore = useInscripcionStore()
    if (
      (to.name === 'clientes-inscripciones-inscribir' || to.name === 'clientes-inscripciones-lista-espera') &&
      !inscripcionStore.turnoSeleccionado
    ) {
      return { name: 'clientes-inscripciones-turnos', params: { clienteId: to.params.clienteId } }
    }
  }

  if (isAuthenticated && isPublicRoute) {
    if (isAdmin) return { name: 'admin-home' }
    if (isEmployee) return { name: 'employee-home' }
    return { name: 'list' }
  }
})

// Guard: redirige al login si la ruta requiere auth y no hay token
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !localStorage.getItem('access_token')) {
    return { name: 'login' }
  }
})

export default router