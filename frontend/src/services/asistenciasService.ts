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

// ─── Mock data ────────────────────────────────────────────────────────────────

// ⏳ Eliminar cuando backend implemente GET /api/v1/users/{userId}/asistencias
// Datos diseñados para cubrir los 5 escenarios de ASIS-02.01:
//   user 1 — 15 registros (12 presente, 3 ausente)
//             Yoga: 8 registros (6 presente)   → filtro actividad da 75%
//             Pilates: 7 registros (6 presente)
//             Mayo 2026: 5 registros (4 presente) → filtro rango da 80%
//   user 2 — sin registros → mensaje "El cliente no tiene asistencias registradas"
const MOCK_HISTORIAL: Record<number, RegistroAsistencia[]> = {
  1: [
    { id:  1, actividad: 'Yoga',    fecha: '2026-05-26', horario: '9:00 – 10:00',  estado: 'presente' },
    { id:  2, actividad: 'Yoga',    fecha: '2026-05-19', horario: '9:00 – 10:00',  estado: 'presente' },
    { id:  3, actividad: 'Pilates', fecha: '2026-05-15', horario: '17:00 – 18:00', estado: 'ausente'  },
    { id:  4, actividad: 'Yoga',    fecha: '2026-05-12', horario: '9:00 – 10:00',  estado: 'presente' },
    { id:  5, actividad: 'Pilates', fecha: '2026-05-08', horario: '17:00 – 18:00', estado: 'presente' },
    { id:  6, actividad: 'Yoga',    fecha: '2026-04-28', horario: '9:00 – 10:00',  estado: 'ausente'  },
    { id:  7, actividad: 'Pilates', fecha: '2026-04-24', horario: '17:00 – 18:00', estado: 'presente' },
    { id:  8, actividad: 'Yoga',    fecha: '2026-04-21', horario: '9:00 – 10:00',  estado: 'presente' },
    { id:  9, actividad: 'Pilates', fecha: '2026-04-17', horario: '17:00 – 18:00', estado: 'presente' },
    { id: 10, actividad: 'Yoga',    fecha: '2026-04-14', horario: '9:00 – 10:00',  estado: 'presente' },
    { id: 11, actividad: 'Pilates', fecha: '2026-04-10', horario: '17:00 – 18:00', estado: 'presente' },
    { id: 12, actividad: 'Yoga',    fecha: '2026-04-07', horario: '9:00 – 10:00',  estado: 'presente' },
    { id: 13, actividad: 'Pilates', fecha: '2026-04-03', horario: '17:00 – 18:00', estado: 'presente' },
    { id: 14, actividad: 'Yoga',    fecha: '2026-03-31', horario: '9:00 – 10:00',  estado: 'ausente'  },
    { id: 15, actividad: 'Pilates', fecha: '2026-03-27', horario: '17:00 – 18:00', estado: 'presente' },
  ],
  2: [],
}

// ─── Funciones ────────────────────────────────────────────────────────────────

/**
 * Devuelve el historial de asistencias de un cliente ordenado de más reciente a más antiguo.
 * ⏳ Mock activo — endpoint GET /api/v1/users/{userId}/asistencias no implementado.
 * Ver docs/pendientes-backend.md.
 * Para activar: descomentar llamada real y eliminar bloque mock.
 */
export const getHistorialAsistencias = async (
  userId: number,
): Promise<RegistroAsistencia[]> => {
  // const res = await api.get(`/users/${userId}/asistencias`)
  // return res.data
  void api // evita error de import no utilizado mientras el mock esté activo
  await new Promise(resolve => setTimeout(resolve, 500))
  return MOCK_HISTORIAL[userId] ?? []
}
