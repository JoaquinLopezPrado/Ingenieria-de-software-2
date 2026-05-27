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
  createMonthly: (turno_id: number) =>
    apiClient.post('/enrollments/monthly', { turno_id }),

  createSingle: (clase_id: number) =>
    apiClient.post('/enrollments/single', { clase_id }),

  createPaymentPreference: (enrollment_id: number) =>
    apiClient.post('/payments/preference', { enrollment_id }),

  getMyMonthly: () =>
    apiClient.get('/enrollments/my/monthly'),

  getMySingle: () =>
    apiClient.get('/enrollments/my/single'),

  cancelEnrollment: (enrollment_id: number) =>
    apiClient.delete(`/enrollments/${enrollment_id}`),
}
