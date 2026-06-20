import api from './api'

export type AttendanceStatus = 'presente' | 'ausente'

export interface RegistroAsistencia {
  id: number
  actividad: string
  fecha: string
  horario: string
  estado: AttendanceStatus
}

export interface RosterEntry {
  user_id: number
  first_name: string
  last_name: string
  full_name: string
  source: string
  estado: AttendanceStatus | null
}

export const getHistorialAsistencias = async (
  userId: number,
): Promise<RegistroAsistencia[]> => {
  const res = await api.get<RegistroAsistencia[]>(`/users/${userId}/asistencias`)
  return res.data
}

export const getRoster = async (claseId: number): Promise<RosterEntry[]> => {
  const res = await api.get<RosterEntry[]>(`/attendances/roster/${claseId}`)
  return res.data
}

export const markAttendance = async (
  userId: number,
  claseId: number,
  estado: AttendanceStatus,
): Promise<void> => {
  await api.post('/attendances', { user_id: userId, clase_id: claseId, estado })
}

export const deleteAttendance = async (userId: number, claseId: number): Promise<void> => {
  await api.delete('/attendances', { data: { user_id: userId, clase_id: claseId } })
}
