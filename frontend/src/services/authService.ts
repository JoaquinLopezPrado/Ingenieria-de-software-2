import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Agregar token a las requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const authService = {
  login: (email: string, password: string) => {
    return apiClient.post('/auth/login', {
      email,
      password,
    })
  },

  register: (email: string, password: string) => {
    return apiClient.post('/auth/register', {
      email,
      password,
    })
  },

  forgotPassword: (email: string) => {
    return apiClient.post('/auth/forgot-password', {
      email,
    })
  },

  logout: () => {
    return apiClient.post('/auth/logout')
  },
}