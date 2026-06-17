/**
 * clientesService.ts — Ficha, listado y búsqueda de clientes (admin/empleado)
 * ---------------------------------------------------------------------------
 * Endpoints pendientes:
 *   GET /api/v1/users            (listado + búsqueda paginada — ⏳ ver pendientes-backend.md §6)
 *   GET /api/v1/users/{userId}   (ficha por id              — ⏳ ver pendientes-backend.md §10)
 */
import api from './api'

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

export interface ListClientesParams {
  q?: string         // texto libre: nombre, apellido o número de documento
  page?: number      // 1-based, default 1
  page_size?: number // default 20
}

export interface ClientesPaginados {
  items: Cliente[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ─── Mock data ────────────────────────────────────────────────────────────────

// ⏳ Eliminar cuando backend implemente los endpoints de clientes
const MOCK_LIST: Cliente[] = [
  { id:  1, email: 'juan.perez@example.com',       first_name: 'Juan',      last_name: 'Pérez',      phone: '1123456789', doc_type_name: 'DNI',       doc_number: '12345678' },
  { id:  2, email: 'maria.garcia@example.com',     first_name: 'María',     last_name: 'García',     phone: '1198765432', doc_type_name: 'DNI',       doc_number: '23456789' },
  { id:  3, email: 'carlos.lopez@example.com',     first_name: 'Carlos',    last_name: 'López',      phone: '1134567890', doc_type_name: 'DNI',       doc_number: '34567890' },
  { id:  4, email: 'ana.martinez@example.com',     first_name: 'Ana',       last_name: 'Martínez',   phone: '1145678901', doc_type_name: 'DNI',       doc_number: '45678901' },
  { id:  5, email: 'roberto.rodriguez@example.com',first_name: 'Roberto',   last_name: 'Rodríguez',  phone: '1156789012', doc_type_name: 'DNI',       doc_number: '56789012' },
  { id:  6, email: 'lucia.fernandez@example.com',  first_name: 'Lucía',     last_name: 'Fernández',  phone: '1167890123', doc_type_name: 'DNI',       doc_number: '67890123' },
  { id:  7, email: 'diego.sanchez@example.com',    first_name: 'Diego',     last_name: 'Sánchez',    phone: '1178901234', doc_type_name: 'DNI',       doc_number: '78901234' },
  { id:  8, email: 'valentina.gomez@example.com',  first_name: 'Valentina', last_name: 'Gómez',      phone: '1189012345', doc_type_name: 'DNI',       doc_number: '89012345' },
  { id:  9, email: 'pablo.diaz@example.com',       first_name: 'Pablo',     last_name: 'Díaz',       phone: '1190123456', doc_type_name: 'PASAPORTE', doc_number: 'AB123456' },
  { id: 10, email: 'laura.torres@example.com',     first_name: 'Laura',     last_name: 'Torres',     phone: '1101234567', doc_type_name: 'DNI',       doc_number: '90123456' },
  { id: 11, email: 'martin.ramirez@example.com',   first_name: 'Martín',    last_name: 'Ramírez',    phone: '1112345678', doc_type_name: 'DNI',       doc_number: '01234567' },
  { id: 12, email: 'sofia.vargas@example.com',     first_name: 'Sofía',     last_name: 'Vargas',     phone: '1123456780', doc_type_name: 'DNI',       doc_number: '11234567' },
]

const MOCK_MAP = new Map<number, Cliente>(MOCK_LIST.map(c => [c.id, c]))

// ─── Funciones ────────────────────────────────────────────────────────────────

/**
 * Devuelve el listado paginado de alumnos, con búsqueda opcional por nombre,
 * apellido o número de documento.
 *
 * Usos:
 *  - Vista "Alumnos":  listClientes({ q: texto, page, page_size })
 *  - Inscripciones:    listClientes({ q: docNumber, page_size: 1 }) → tomar items[0]
 *    y verificar doc_number exacto en el frontend.
 *
 * ⏳ Mock activo — endpoint GET /api/v1/users no implementado.
 * Ver docs/pendientes-backend.md §6.
 * Para activar: descomentar llamada real y eliminar bloque mock.
 */
export const listClientes = async (
  params: ListClientesParams = {},
): Promise<ClientesPaginados> => {
  // const res = await api.get('/users', { params })
  // return res.data
  void api
  await new Promise(resolve => setTimeout(resolve, 400))

  const q = params.q?.trim().toLowerCase() ?? ''
  const page = Math.max(1, params.page ?? 1)
  const page_size = Math.min(100, Math.max(1, params.page_size ?? 20))

  const filtered = q
    ? MOCK_LIST.filter(c =>
        c.first_name.toLowerCase().includes(q) ||
        c.last_name.toLowerCase().includes(q) ||
        c.doc_number.toLowerCase().includes(q),
      )
    : [...MOCK_LIST]

  const total = filtered.length
  const total_pages = Math.max(1, Math.ceil(total / page_size))
  const start = (page - 1) * page_size
  const items = filtered.slice(start, start + page_size)

  return { items, total, page, page_size, total_pages }
}

/**
 * Obtiene los datos de un cliente por su user_id.
 * ⏳ Mock activo — endpoint GET /api/v1/users/{userId} no implementado.
 * Ver docs/pendientes-backend.md §10.
 * Para activar: descomentar llamada real y eliminar bloque mock.
 */
export const getClienteById = async (userId: number): Promise<Cliente> => {
  // const res = await api.get(`/users/${userId}`)
  // return res.data
  await new Promise(resolve => setTimeout(resolve, 300))
  const cliente = MOCK_MAP.get(userId)
  if (!cliente) {
    throw {
      response: {
        status: 404,
        data: { errors: { general: 'Alumno no encontrado.' } },
      },
    }
  }
  return { ...cliente }
}
