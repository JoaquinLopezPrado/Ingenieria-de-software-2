// Usa el cliente axios compartido (baseURL + interceptor de token centralizados)
import api from './api'

const apiClient = api

export const authService = {
  login: (credentials: any) =>
    apiClient.post('/auth/login', credentials),

  register: (userData: any) =>
    apiClient.post('/auth/register', userData),

  forgotPassword: (email: string) => {
    return apiClient.post('/auth/forgot-password', {
      email,
    })
  },

  logout: (refreshToken: string) =>
    apiClient.post('/auth/logout', {
      refresh_token: refreshToken,
    }),

  getMe: () =>
    apiClient.get('/users/me'),

  refresh: (refreshToken: string) =>
    apiClient.post('/auth/refresh', {
      refresh_token: refreshToken,
    }),

  googleComplete: (data: {
    pending_token: string
    phone: string
    birth_date: string
    gender: string
    doc_type_name: string
    doc_number: string
  }) => apiClient.post('/auth/google/complete', data),

  getGoogleLinkUrl: () =>
    apiClient.get<{ url: string }>('/auth/google/link'),

  unlinkGoogle: () =>
    apiClient.delete('/auth/google/link'),
}