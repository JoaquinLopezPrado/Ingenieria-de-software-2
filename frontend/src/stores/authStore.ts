import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authService } from '@/services/authService'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<any>(null)
  const isAuthenticated = ref(!!localStorage.getItem('access_token'))
  const forgotPassword = async (email: string) => {
  
  return new Promise((resolve) => setTimeout(resolve, 1000))
}

  const fetchUser = async () => {
    try {
      const response = await authService.getMe()
      user.value = response.data
    } catch (error) {
      logout()
    }
  }

  const login = async (credentials: any) => {
    const response = await authService.login(credentials)
    const { access_token, refresh_token } = response.data
    
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    isAuthenticated.value = true
    
    await fetchUser() // Cargamos los datos del perfil (nombre, rol, etc.)
  }

  const register = async (userData: any) => {
    return await authService.register(userData)
  }

  const logout = async () => {
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      try { await authService.logout(refreshToken) } catch (e) {}
    }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    user.value = null
    isAuthenticated.value = false
  }

  return { user, isAuthenticated, login, register, logout, fetchUser,forgotPassword }
})