// Usa el cliente axios compartido (baseURL + interceptor de token centralizados)
import api from './api'

const apiClient = api

export const authService = {
  login: (credentials: any) =>
    apiClient.post('/auth/login', credentials),

  register: (userData: any) =>
    apiClient.post('/auth/register', userData),

  forgotPassword: (email: string) =>
    apiClient.post('/auth/forgot-password', { email }),

  resetPassword: (token: string, newPassword: string) =>
    apiClient.post('/auth/reset-password', { token, new_password: newPassword }),

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

  setup2FA: () =>
    apiClient.post('/auth/2fa/setup'),

  confirm2FA: (secret: string, code: string) =>
    apiClient.post('/auth/2fa/confirm', { secret, code }),

  disable2FA: (code: string) =>
    apiClient.post('/auth/2fa/disable', { code }),

  verify2FA: (preAuthToken: string, code: string) =>
    apiClient.post('/auth/2fa/verify', { pre_auth_token: preAuthToken, code }),
}