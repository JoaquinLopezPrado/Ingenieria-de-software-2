/**
 * inscripcionService.ts — Gestión de Inscripciones (flujo admin/empleado)
 * -------------------------------------------------------------------------
 * Pasos del flujo:
 *   1. buscarClientePorDni     → GET  /api/v1/users/search          (⏳ ver pendientes-backend.md § 6)
 *   2. getTurnosParaInscripcion → GET /api/v1/turnos                 (✅ implementado)
 *   3. getPreviewInscripcion   → GET  /api/v1/enrollments/admin/preview (⏳ ver pendientes-backend.md § 7)
 *   3. inscribirCliente        → POST /api/v1/enrollments/admin/subscription (⏳ ver pendientes-backend.md § 8)
 *   4. agregarListaEspera      → POST /api/v1/enrollments/admin/waitlist     (⏳ ver pendientes-backend.md § 9)
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

export interface InscripcionAdminResponse {
  id: number
  user_id: number
  turno_id: number
  type: 'subscription'
  status: string
  created_at: string
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

// ⏳ Eliminar cuando backend implemente INS-02, INS-03 e INS-04
const MOCK_ENROLLED = new Set<string>()  // clave: `${userId}-${turnoId}`
const MOCK_WAITLIST = new Set<string>()  // clave: `${userId}-${turnoId}`

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

/**
 * Paso 3 (preview) — calcula el importe sin persistir ni descontar cupos.
 * ⏳ Mock activo — endpoint GET /api/v1/enrollments/admin/preview no implementado (INS-02).
 * Ver docs/pendientes-backend.md § 7.
 * Para activar: descomentar llamada real y eliminar bloque mock.
 */
export const getPreviewInscripcion = async (
  turnoId: number,
  userId: number,
  classPriceHint = 0,
): Promise<PreviewInscripcionResponse> => {
  // const res = await api.get('/enrollments/admin/preview', {
  //   params: { turno_id: turnoId, user_id: userId },
  // })
  // return res.data
  await new Promise(resolve => setTimeout(resolve, 600))
  const makeDate = (weeksAhead: number) => {
    const d = new Date()
    d.setDate(d.getDate() + weeksAhead * 7)
    return d.toISOString().split('T')[0]
  }
  return {
    turno_id: turnoId,
    user_id: userId,
    precio_por_clase: classPriceHint,
    clases_con_cupo: [
      { clase_id: 101, fecha: makeDate(1) },
      { clase_id: 102, fecha: makeDate(2) },
      { clase_id: 103, fecha: makeDate(3) },
    ],
    clases_sin_cupo: [],
    clases_ya_abonadas: [],
    total: 3 * classPriceHint,
  }
}

/**
 * Paso 3 (confirmar) — registra la inscripción con pago presencial en efectivo.
 * ⏳ Mock activo — endpoint POST /api/v1/enrollments/admin/subscription no implementado (INS-03).
 * Ver docs/pendientes-backend.md § 8.
 * Para activar: descomentar llamada real y eliminar bloque mock.
 */
export const inscribirCliente = async (
  turnoId: number,
  userId: number,
): Promise<InscripcionAdminResponse> => {
  // const res = await api.post('/enrollments/admin/subscription', {
  //   turno_id: turnoId,
  //   user_id: userId,
  // })
  // return res.data
  await new Promise(resolve => setTimeout(resolve, 800))
  const key = `${userId}-${turnoId}`
  if (MOCK_ENROLLED.has(key)) {
    throw {
      response: {
        status: 409,
        data: { errors: { general: 'El cliente ya se encuentra inscripto a este turno' } },
      },
    }
  }
  MOCK_ENROLLED.add(key)
  return {
    id: Date.now(),
    user_id: userId,
    turno_id: turnoId,
    type: 'subscription',
    status: 'active',
    created_at: new Date().toISOString(),
  }
}

/**
 * Paso 4 — agrega al cliente a la lista de espera de un turno sin cupo.
 * ⏳ Mock activo — endpoint POST /api/v1/enrollments/admin/waitlist no implementado (INS-04).
 * Ver docs/pendientes-backend.md § 9.
 * Para activar: descomentar llamada real y eliminar bloque mock.
 */
export const agregarListaEspera = async (
  turnoId: number,
  userId: number,
): Promise<WaitlistEntry> => {
  // const res = await api.post('/enrollments/admin/waitlist', {
  //   turno_id: turnoId,
  //   user_id: userId,
  // })
  // return res.data
  await new Promise(resolve => setTimeout(resolve, 700))
  const key = `${userId}-${turnoId}`
  if (MOCK_ENROLLED.has(key)) {
    throw {
      response: {
        status: 409,
        data: { errors: { general: 'El cliente ya se encuentra inscripto a este turno' } },
      },
    }
  }
  if (MOCK_WAITLIST.has(key)) {
    throw {
      response: {
        status: 409,
        data: { errors: { general: 'El cliente ya se encuentra en la lista de espera de este turno' } },
      },
    }
  }
  MOCK_WAITLIST.add(key)
  return {
    id: Date.now(),
    user_id: userId,
    turno_id: turnoId,
    position: MOCK_WAITLIST.size,
    created_at: new Date().toISOString(),
  }
}
