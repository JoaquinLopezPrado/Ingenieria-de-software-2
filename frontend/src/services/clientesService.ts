import api from './api'

// ─── Interfaces ───────────────────────────────────────────────────────────────

export interface Cliente {
  id: number
  email: string
  first_name: string
  last_name: string
  phone: string
  doc_type_name: string
  doc_number: string
  is_active: boolean
}

export interface ClienteSubscripcion {
  subscription_id: number
  status: string
  start_date: string
  ends_on: string | null
  turno_id: number
  turno_description: string
  start_time: string
  end_time: string
  instructor: string
  activity_name: string
  days: string[]
}

export interface ClienteSingleEnrollment {
  enrollment_id: number
  status: string
  amount: number
  expires_at: string | null
  created_at: string
  turno_id: number
  clase_id: number
  clase_date: string
  start_time: string
  end_time: string
  turno_description: string
  instructor: string
  activity_name: string
}

export interface ListClientesParams {
  q?: string
  page?: number
  page_size?: number
}

export interface ClientesPaginados {
  items: Cliente[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ─── Funciones ────────────────────────────────────────────────────────────────

export const createCliente = async (data: Record<string, unknown>): Promise<void> => {
  await api.post('/users', data)
}

export const listClientes = async (
  params: ListClientesParams = {},
): Promise<ClientesPaginados> => {
  const res = await api.get('/users', { params })
  return res.data
}

export const getClienteById = async (userId: number): Promise<Cliente> => {
  const res = await api.get(`/users/${userId}`)
  return res.data
}

export const getSubscripcionesByCliente = async (userId: number): Promise<ClienteSubscripcion[]> => {
  const res = await api.get(`/subscriptions/user/${userId}`)
  return res.data
}

export const getSingleEnrollmentsByCliente = async (userId: number): Promise<ClienteSingleEnrollment[]> => {
  const res = await api.get(`/single-enrollments/user/${userId}`)
  return res.data
}

export const deactivateCliente = async (userId: number): Promise<void> => {
  await api.patch(`/users/${userId}/deactivate`)
}

export const reactivateCliente = async (userId: number): Promise<void> => {
  await api.patch(`/users/${userId}/reactivate`)
}
