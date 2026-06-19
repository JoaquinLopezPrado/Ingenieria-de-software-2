/**
 * asistenciasService.ts — Historial de asistencias de un cliente (ASIS-02.01)
 * --------------------------------------------------------------------------
 * Endpoint pendiente:
 *   GET /api/v1/users/{userId}/asistencias  (⏳ ver pendientes-backend.md)
 */
import api from './api'

// ─── Interfaces ───────────────────────────────────────────────────────────────

export interface RegistroAsistencia {
  id: number
  actividad: string      // nombre de la actividad
  fecha: string          // "YYYY-MM-DD"
  horario: string        // "H:MM – H:MM"
  estado: 'presente' | 'ausente'
}

// ─── Funciones ────────────────────────────────────────────────────────────────

/**
 * Devuelve el historial de asistencias de un cliente ordenado de más reciente a más antiguo.
 * Endpoint: GET /api/v1/users/{userId}/asistencias (admin/empleado).
 */
export const getHistorialAsistencias = async (
  userId: number,
): Promise<RegistroAsistencia[]> => {
  const res = await api.get<RegistroAsistencia[]>(`/users/${userId}/asistencias`)
  return res.data
}
