import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const authService = {
  login: (credentials: any) => apiClient.post('/auth/login', credentials),

  register: (userData: any) => apiClient.post('/auth/register', userData),

  forgotPassword: (email: string) => {
    return apiClient.post('/auth/forgot-password', {
      email,
    })
  },

  logout: (refreshToken: string) => apiClient.post('/auth/logout', { refresh_token: refreshToken }),

  getMe: () => apiClient.get('/users/me'),

  refresh: (refreshToken: string) => apiClient.post('/auth/refresh', { refresh_token: refreshToken })
  
}