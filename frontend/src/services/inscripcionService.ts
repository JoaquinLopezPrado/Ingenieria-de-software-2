/**
 * inscripcionService.ts — Gestión de Inscripciones (flujo admin/empleado)
 * -------------------------------------------------------------------------
 * Pasos del flujo:
 *   1. buscarClientePorDni        → GET  /api/v1/users/search             (⏳ mock)
 *   2. getTurnosParaInscripcion   → GET  /api/v1/turnos                   (✅)
 *   3. getPreviewInscripcion      → POST /api/v1/admin/enrollments/subscription/preview (✅)
 *   4a. inscribirCliente          → POST /api/v1/admin/enrollments/subscription         (✅)
 *   4b. inscribirClienteClase     → POST /api/v1/admin/enrollments/single               (✅)
 *   5. agregarListaEspera         → POST /api/v1/enrollments/admin/waitlist             (⏳ mock)
 */
import api from './api'
import type { TurnoPageResponse } from './sessionService'

// ─── Interfaces ───────────────────────────────────────────────────────────────

export interface Cliente {
  id: number
  email: string
  first_name: string
  last_name: string
  phone: string
  doc_type_name: 'DNI' | 'PASAPORTE'
  doc_number: string
}

export interface ClasePreviewItem {
  clase_id: number
  fecha: string // "YYYY-MM-DD"
}

export interface PreviewInscripcionResponse {
  turno_id: number
  user_id: number
  precio_por_clase: number
  clases_con_cupo: ClasePreviewItem[]
  clases_sin_cupo: ClasePreviewItem[]
  clases_ya_abonadas: ClasePreviewItem[]
  total: number
}

export interface WaitlistEntry {
  id: number
  user_id: number
  turno_id: number
  position: number
  created_at: string
}

// ─── Mock data ────────────────────────────────────────────────────────────────

// ⏳ Eliminar cuando backend implemente GET /api/v1/users/search (INS-01)
const MOCK_CLIENTES: Record<string, Cliente> = {
  '12345678': {
    id: 1,
    email: 'juan.perez@example.com',
    first_name: 'Juan',
    last_name: 'Pérez',
    phone: '1123456789',
    doc_type_name: 'DNI',
    doc_number: '12345678',
  },
  '23456789': {
    id: 2,
    email: 'maria.garcia@example.com',
    first_name: 'María',
    last_name: 'García',
    phone: '1198765432',
    doc_type_name: 'DNI',
    doc_number: '23456789',
  },
}

// ─── Funciones ────────────────────────────────────────────────────────────────

/**
 * Paso 1 — busca un cliente por tipo y número de documento.
 * ⏳ Mock activo — endpoint GET /api/v1/users/search no implementado aún (INS-01).
 * Ver docs/pendientes-backend.md § 6.
 * Para activar: descomentar llamada real y eliminar bloque mock.
 */
export const buscarClientePorDni = async (
  docNumber: string,
  docType: 'DNI' | 'PASAPORTE' = 'DNI',
): Promise<Cliente> => {
  // const res = await api.get('/users/search', {
  //   params: { doc_number: docNumber, doc_type_name: docType },
  // })
  // return res.data
  await new Promise(resolve => setTimeout(resolve, 500))
  const cliente = MOCK_CLIENTES[docNumber]
  if (!cliente) {
    throw {
      response: {
        status: 404,
        data: { errors: { general: 'No se encontró un cliente registrado con el documento ingresado' } },
      },
    }
  }
  return { ...cliente, doc_type_name: docType }
}

/**
 * Paso 2 — lista los turnos disponibles para mostrar al empleado.
 * ✅ Llama a GET /api/v1/turnos — ya implementado.
 * Se puede filtrar por has_availability para separar con/sin cupo.
 */
export const getTurnosParaInscripcion = async (params?: {
  activity_id?: number
  has_availability?: boolean
}): Promise<TurnoPageResponse> => {
  const res = await api.get('/turnos', { params: { ...params, page_size: 500 } })
  return res.data
}

export const getPreviewInscripcion = async (
  turnoId: number,
  userId: number,
  _classPriceHint = 0,
): Promise<PreviewInscripcionResponse> => {
  const res = await api.post('/admin/enrollments/subscription/preview', {
    turno_id: turnoId,
    user_id: userId,
  })
  return res.data
}

export const inscribirCliente = async (
  turnoId: number,
  userId: number,
): Promise<void> => {
  await api.post('/admin/enrollments/subscription', {
    turno_id: turnoId,
    user_id: userId,
  })
}

export const inscribirClienteClase = async (
  claseId: number,
  userId: number,
): Promise<void> => {
  await api.post('/admin/enrollments/single', {
    clase_ids: [claseId],
    user_id: userId,
  })
}

/**
 * Paso 4 — agrega al cliente a la lista de espera de un turno sin cupo.
 * ⏳ Mock activo — endpoint POST /api/v1/enrollments/admin/waitlist no implementado (INS-04).
 * Ver docs/pendientes-backend.md § 9.
 * Para activar: descomentar llamada real y eliminar bloque mock.
 */
export const getAdminWaitlistTurnoIds = async (userId: number): Promise<number[]> => {
  const res = await api.get(`/admin/enrollments/waitlist/${userId}`)
  return res.data
}

export const agregarListaEspera = async (
  turnoId: number,
  userId: number,
): Promise<WaitlistEntry> => {
  const res = await api.post('/admin/enrollments/waitlist', {
    turno_id: turnoId,
    user_id: userId,
  })
  return res.data
}
