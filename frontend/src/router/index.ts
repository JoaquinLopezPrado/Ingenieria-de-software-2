import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

import ScheduleSessionView from '@/views/activities/ScheduleSessionView.vue'
import GrillaTurnosView from '@/views/activities/GrillaTurnosView.vue'
import EditTurnoView from '@/views/activities/EditTurnoView.vue'
import ListaActividadesView from '@/views/activities/ListaActividadesView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/home',
      name: 'home',
      component: HomeView,
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
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/list',
      name: 'list',
      component: () => import('../views/ShowActivitisView.vue'),
    },
    {
      path: '/ticket',
      name: 'ticket',
      component: () => import('../views/TicketView.vue'),
    },
    {
      path: '/payment/success',
      name: 'payment-success',
      component: () => import('../views/PaymentSuccessView.vue'),
    },
    {
      path: '/payment/failure',
      name: 'payment-failure',
      component: () => import('../views/PaymentFailureView.vue'),
    },
    {
      path: '/payment/pending',
      name: 'payment-pending',
      component: () => import('../views/PaymentPendingView.vue'),
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
    },
    {
      path: '/activities/schedule',
      name: 'schedule-session',
      component: ScheduleSessionView,
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/activities/turnos/:id/edit',
      name: 'edit-turno',
      component: EditTurnoView,
      meta: { requiresAuth: true },
    },
    {
      path: '/logout',
      name: 'logout',
      component: () => import('../views/LogoutView.vue'),
    },
    {
      path: '/class-selection',
      name: 'class-selection',
      component: () => import('../views/ClassSelectionView.vue'),
    },
    {
      path: '/list',
      name: 'list',
      component: () => import('../views/ShowActivitisView.vue'),
    }
  ],
})

const publicRouteNames = new Set(['login', 'register', 'forgot-password'])

router.beforeEach((to) => {
  const hasAccessToken = Boolean(localStorage.getItem('access_token'))
  const isPublicRoute = typeof to.name === 'string' && publicRouteNames.has(to.name)

  if (!hasAccessToken && !isPublicRoute) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  if (hasAccessToken && isPublicRoute) {
    return { name: 'home' }
  }
})

export default router