import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authService } from '@/services/authService'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<any>(null)
  const isAuthenticated = ref(!!token.value)

  const login = async (email: string, password: string) => {
    const response = await authService.login(email, password)
    token.value = response.access_token
    isAuthenticated.value = true
    localStorage.setItem('token', response.access_token)
    if (response.user) {
      user.value = response.user
    }
  }

  const register = async (email: string, password: string) => {
    const response = await authService.register(email, password)
    return response
  }

  const forgotPassword = async (email: string) => {
    const response = await authService.forgotPassword(email)
    return response
  }

  const logout = () => {
    token.value = null
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    forgotPassword,
    logout,
  }
})