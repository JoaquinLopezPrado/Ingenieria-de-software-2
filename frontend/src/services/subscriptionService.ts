import api from './api'

export interface GenerateChargesResponse {
  charges_created: number
  period_month: number
  period_year: number
}

export interface AdminPendingCharge {
  charge_id: number
  subscription_id: number
  user_id: number
  first_name: string
  last_name: string
  email: string
  activity_name: string
  turno_description: string
  amount: number
  period_month: number
  period_year: number
  due_date: string | null
}

export const adminGenerateNextMonthCharges = async (): Promise<GenerateChargesResponse> => {
  const res = await api.post('/subscriptions/admin/generate-charges')
  return res.data
}

export const adminGetPendingCharges = async (): Promise<AdminPendingCharge[]> => {
  const res = await api.get('/subscriptions/admin/pending-charges')
  return res.data
}

export const adminCashConfirmCharge = async (chargeId: number): Promise<void> => {
  await api.post(`/subscriptions/admin/charges/${chargeId}/cash-confirm`)
}
