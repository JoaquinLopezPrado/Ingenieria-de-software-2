import axios from 'axios'

export interface CreditInfo {
  id: number
  amount: number
  expires_at: string
  source_clase_date: string | null
}

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
  // --- Suscripciones (abono recurrente) ---
  // Crea la suscripción + el cargo del primer período. Devuelve el cargo (charge_id) para el ticket.
  createSubscription: (turno_id: number) =>
    apiClient.post('/subscriptions', { turno_id }),

  getMySubscription: () =>
    apiClient.get('/subscriptions/me'),

  // Historial de cargos mensuales pagados (para la pantalla de Pagos).
  getMyCharges: () =>
    apiClient.get('/subscriptions/me/charges'),

  cancelSubscription: (subscription_id: number) =>
    apiClient.delete(`/subscriptions/${subscription_id}`),

  // Baja voluntaria de un abonado activo (efectiva al fin del período pagado).
  unsubscribe: (subscription_id: number) =>
    apiClient.post<{ ends_on: string }>(`/subscriptions/${subscription_id}/cancel`),

  // El pago de un cargo de suscripción se hace por charge_id.
  createSubscriptionPreference: (charge_id: number) =>
    apiClient.post('/payments/subscription-preference', { charge_id }),

  freeConfirmSubscription: (charge_id: number) =>
    apiClient.post('/payments/subscription-free-confirm', { charge_id }),

  // --- Clases sueltas (drop-in) ---
  createSingle: (clase_ids: number[], credit_id?: number) =>
    apiClient.post('/single-enrollments', { clase_ids, ...(credit_id !== undefined ? { credit_id } : {}) }),

  getCreditsForTurno: (turno_id: number) =>
    apiClient.get<CreditInfo[]>('/clases/credits', { params: { turno_id } }),

  getMySingle: () =>
    apiClient.get('/single-enrollments/me'),

  cancelSingle: (enrollment_id: number) =>
    apiClient.delete(`/single-enrollments/${enrollment_id}`),

  createSinglePreference: (enrollment_id: number) =>
    apiClient.post('/payments/single-preference', { enrollment_id }),

  createDepositPreference: (enrollment_id: number) =>
    apiClient.post('/payments/single-deposit-preference', { enrollment_id }),

  createBalancePreference: (enrollment_id: number) =>
    apiClient.post('/payments/single-balance-preference', { enrollment_id }),

  cancelDeposit: (enrollment_id: number) =>
    apiClient.post<{ refund: boolean; refund_id: string | null }>('/payments/cancel-deposit', { enrollment_id }),

  // --- Común ---
  getMpStatusDetail: (payment_id: string) =>
    apiClient.get<{ status_detail: string | null }>(`/payments/mp-status`, { params: { payment_id } }),
}
