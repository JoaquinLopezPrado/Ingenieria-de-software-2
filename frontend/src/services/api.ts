import axios from 'axios'
import { getActivePinia } from 'pinia'
import router from '@/router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// ── Request: adjunta el Bearer token si existe ────────────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Response: redirige al login cuando la sesión expira (401) ─────────────────
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      // Limpiar estado del store sincrónicamente para que el guard no vea datos stale.
      // getActivePinia() evita el import circular (api → authStore → authService → api).
      const pinia = getActivePinia()
      if (pinia?.state.value?.auth) {
        pinia.state.value.auth.user = null
        pinia.state.value.auth.isAuthenticated = false
      }
      if (router.currentRoute.value.name !== 'login') {
        router.push({ name: 'login' })
      }
    }
    return Promise.reject(error)
  }
)

export default api
