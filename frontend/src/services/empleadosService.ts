import api from './api'

export interface Empleado {
  id: number
  email: string
  first_name: string
  last_name: string
  phone: string | null
  is_active: boolean
}

export interface CreateEmpleadoPayload {
  email: string
  first_name: string
  last_name: string
  phone?: string
}

export interface UpdateEmpleadoPayload {
  first_name: string
  last_name: string
  phone?: string
}

export const listEmpleados = async (): Promise<Empleado[]> => {
  const res = await api.get('/employees')
  return res.data
}

export const createEmpleado = async (payload: CreateEmpleadoPayload): Promise<Empleado> => {
  const res = await api.post('/employees', payload)
  return res.data
}

export const updateEmpleado = async (id: number, payload: UpdateEmpleadoPayload): Promise<Empleado> => {
  const res = await api.put(`/employees/${id}`, payload)
  return res.data
}

export const deactivateEmpleado = async (id: number): Promise<void> => {
  await api.patch(`/employees/${id}/deactivate`)
}
