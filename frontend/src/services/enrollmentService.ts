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

export const enrollmentService = {
  createSubscription: (turno_id: number) =>
    apiClient.post('/enrollments/subscription', { turno_id }),

  createSingle: (clase_ids: number[]) =>
    apiClient.post('/enrollments/single', { clase_ids }),

  createPaymentPreference: (enrollment_id: number) =>
    apiClient.post('/payments/preference', { enrollment_id }),

  getMySubscription: () =>
    apiClient.get('/enrollments/my/subscription'),

  getMySingle: () =>
    apiClient.get('/enrollments/my/single'),

  cancelEnrollment: (enrollment_id: number) =>
    apiClient.delete(`/enrollments/${enrollment_id}`),

  getMpStatusDetail: (payment_id: string) =>
    apiClient.get<{ status_detail: string | null }>(`/payments/mp-status`, { params: { payment_id } }),

  freeConfirm: (enrollment_id: number) =>
    apiClient.post('/payments/free-confirm', { enrollment_id }),

  createDepositPreference: (enrollment_id: number) =>
    apiClient.post('/payments/deposit-preference', { enrollment_id }),

  createBalancePreference: (enrollment_id: number) =>
    apiClient.post('/payments/balance-preference', { enrollment_id }),

  cancelDeposit: (enrollment_id: number) =>
    apiClient.post<{ refund: boolean; refund_id: string | null }>('/payments/cancel-deposit', { enrollment_id }),
}
