import api from './api'

export interface GenerateChargesResponse {
  charges_created: number
  period_month: number
  period_year: number
}

export const adminGenerateNextMonthCharges = async (): Promise<GenerateChargesResponse> => {
  const res = await api.post('/subscriptions/admin/generate-charges')
  return res.data
}
