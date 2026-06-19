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
