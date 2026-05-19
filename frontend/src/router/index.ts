import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { isAdminUser, isEmployeeUser, isStaffUser } from '@/utils/role'

import ScheduleSessionView from '@/views/activities/ScheduleSessionView.vue'
import GrillaTurnosView from '@/views/activities/GrillaTurnosView.vue'
import CalendarioClasesView from '@/views/activities/CalendarioClasesView.vue'
import EditTurnoView from '@/views/activities/EditTurnoView.vue'
import ListaActividadesView from '@/views/activities/ListaActividadesView.vue'

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
      meta: { requiresAuth: true, requiresAdmin: true },
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
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/activities/turnos',
      name: 'turnos-grilla',
      component: GrillaTurnosView,
      meta: { adminLayout: true },
    },
    {
      path: '/activities/turnos/:id/clases',
      name: 'turno-clases',
      component: CalendarioClasesView,
      meta: { adminLayout: true },
    },
    {
      path: '/activities/schedule',
      name: 'schedule-session',
      component: ScheduleSessionView,
      meta: { requiresAuth: true, requiresAdmin: true, adminLayout: true },
    },
    {
      path: '/activities/turnos/:id/edit',
      name: 'edit-turno',
      component: EditTurnoView,
      meta: { requiresAuth: true, adminLayout: true },
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
      path: '/pagos',
      name: 'pagos',
      component: () => import('../views/PagosView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/empleado',
      name: 'employee-home',
      component: () => import('../views/EmployeeHomeView.vue'),
      meta: { requiresAuth: true, requiresEmployee: true },
    },
    {
      path: '/report',
      name: 'report',
      component: () => import('../views/ReportsView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/clientes',
      name: 'lista-alumnos',
      component: () => import('../views/clientes/ListaAlumnosView.vue'),
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
  ]
})

const publicRouteNames = new Set(['login', 'register', 'forgot-password', 'reset-password', 'auth-callback', 'google-complete'])

router.beforeEach(async (to: RouteLocationNormalized) => {
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

  if (to.meta.requiresStaff && !isStaff) {
    return { name: 'list' }
  }

  if (isAuthenticated && isEmployee && !to.meta.requiresStaff && to.name !== 'employee-home') {
    return { name: 'employee-home' }
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