/**
 * sessionService.ts — Servicio para gestión de turnos (ACT-06.01)
 * ----------------------------------------------------------------
 * Capa de comunicación entre el formulario de programación y la API.
 *
 * Endpoint usado: POST /api/v1/turnos  (requiere rol admin)
 * Schema del backend: app/schemas/turno.py → CreateTurnoRequest
 *
 * Responsabilidades:
 *   - Transformar los datos del formulario al formato que espera el backend
 *   - Mapear los días de visualización ("Lunes") al enum del backend ("lunes")
 *   - Extraer los errores del formato { errors: { general: "..." } } del backend
 */
import api from './api'

// ─── Tipos ────────────────────────────────────────────────────────────────────

/**
 * Datos que el formulario emite al hacer submit.
 */
export interface SessionFormData {
  activity_id: number
  salon_id: number
  description: string
  instructor: string
  days: string[]        // valores de visualización: "Lunes", "Miércoles", etc.
  startTime: string     // "HH:MM"
  endTime: string       // "HH:MM"
  maxCapacity: number
  class_price: number
  start_date: string    // "YYYY-MM-DD"
  is_active: boolean
}

export interface Salon {
  id: number
  name: string
  capacity: number
  is_active: boolean
}

export interface CreateSalonPayload {
  name: string
  capacity: number
}

export interface UpdateSalonPayload {
  name: string
  capacity: number
}

export interface ActivityOption {
  id: number
  name: string
  description: string
  instructor: string
  is_active: boolean
}

export interface CreateActivityPayload {
  name: string
  description: string
}

export interface CreateTurnoPayload {
  activity_id: number
  description: string
  start_time: string
  end_time: string
  capacity: number
  start_date: string   // "YYYY-MM-DD" — reemplaza month/year
  days: string[]
  is_active: boolean
  class_price: number
  instructor: string
}

export interface Turno {
  id: number
  activity_id: number
  salon_id: number | null
  salon_name: string | null
  description: string
  instructor: string
  days: string[]      // valores del backend: "lunes", "martes", etc.
  start_time: string  // "H:MM" (sin zero-pad en la hora, ej: "9:00", "17:30")
  end_time: string
  capacity: number
  class_price: number
  is_active: boolean
  enrolled: number
  has_remaining_classes: boolean
  has_future_classes: boolean
}

export interface TurnoPageResponse {
  items: Turno[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface Clase {
  id: number
  turno_id: number
  date: string        // "YYYY-MM-DD" — campo "date" en el backend (ClaseDetalleResponse)
  start_time: string  // "H:MM"
  end_time: string    // "H:MM"
  capacity: number
  enrolled: number    // campo "enrolled" en el backend (inscriptos activos)
  is_active: boolean  // false = suspendida
}

// ─── Mapeo de días ────────────────────────────────────────────────────────────

/**
 * Convierte los días del formulario al enum DiaSemana del backend.
 * Backend: app/domain/turno.py → DiaSemana (lowercase, sin tildes)
 */
const DAY_TO_BACKEND: Record<string, string> = {
  'Lunes': 'lunes',
  'Martes': 'martes',
  'Miércoles': 'miercoles',
  'Jueves': 'jueves',
  'Viernes': 'viernes',
  'Sábado': 'sabado',
}

// ─── Funciones ────────────────────────────────────────────────────────────────

/**
 * Carga las actividades activas desde GET /api/v1/activities.
 * Requiere cualquier rol autenticado (admin | empleado | cliente).
 * Response shape: ActivityResponse[] → { id, name, instructor, is_active }
 * Solo se exponen en el select las actividades con is_active = true.
 */
export const getFormOptions = async (): Promise<{ activities: ActivityOption[] }> => {
  const res = await api.get('/activities')
  return {
    activities: res.data.filter((a: ActivityOption) => a.is_active),
  }
}

/**
 * Carga los salones activos desde GET /api/v1/salones.
 * Requiere rol admin o empleado.
 */
export const getSalones = async (): Promise<Salon[]> => {
  const res = await api.get('/salones')
  return res.data
}

/**
 * Obtiene todos los salones (activos e inactivos) desde GET /api/v1/salones/all.
 * Solo accesible para admins.
 */
export const getSalonesAll = async (): Promise<Salon[]> => {
  const res = await api.get('/salones/all')
  return res.data
}

/**
 * Crea un nuevo salón con POST /api/v1/salones.
 * Requiere rol admin.
 */
export const createSalon = async (payload: CreateSalonPayload): Promise<Salon> => {
  const res = await api.post('/salones', payload)
  return res.data
}

/**
 * Actualiza un salón existente con PATCH /api/v1/salones/{id}.
 * Requiere rol admin.
 */
export const updateSalon = async (salonId: number, payload: UpdateSalonPayload): Promise<Salon> => {
  const res = await api.patch(`/salones/${salonId}`, payload)
  return res.data
}

/**
 * Crea un nuevo turno llamando a POST /api/v1/turnos.
 *
 * Transformaciones aplicadas al payload:
 *   - days:        "Lunes" → "lunes"  (DAY_TO_BACKEND)
 *   - startTime:   camelCase → start_time (snake_case)
 *   - endTime:     camelCase → end_time   (snake_case)
 *   - maxCapacity: → capacity
 *   - start_date:  fecha de inicio del turno (YYYY-MM-DD)
 *
 * Errores del backend:
 *   - 409 Conflict:  { errors: { general: "Ya existe un turno con esa descripción..." } }
 *   - 404 Not Found: { errors: { general: "Actividad no encontrada." } }
 *   - 422 Validation:{ errors: { field: "mensaje" } }
 *   - 401/403:       { errors: { general: "No autenticado." | "Acceso denegado." } }
 *
 * Estos errores se propagan como excepciones para que la vista los capture.
 */
export const createSession = async (formData: SessionFormData): Promise<{ message: string }> => {
  const payload = {
    activity_id: formData.activity_id,
    salon_id: formData.salon_id,
    description: formData.description,
    start_time: formData.startTime,
    end_time: formData.endTime,
    capacity: formData.maxCapacity,
    start_date: formData.start_date,
    days: formData.days.map(d => DAY_TO_BACKEND[d]),
    is_active: formData.is_active,
    class_price: formData.class_price,
    instructor: formData.instructor,
  }

  // axios lanza una excepción automáticamente para respuestas 4xx/5xx
  await api.post('/turnos', payload)

  return { message: 'Turno programado con éxito' }
}

/**
 * Obtiene turnos desde GET /api/v1/turnos.
 * Requiere rol admin, empleado o cliente.
 * Soporta filtros opcionales: activity_id, has_availability, page, page_size.
 */
export const getTurnos = async (params?: {
  activity_id?: number
  has_availability?: boolean
  page?: number
  page_size?: number
}): Promise<TurnoPageResponse> => {
  const res = await api.get('/turnos', { params })
  return res.data
}

/**
 * Obtiene todos los turnos (activos e inactivos) desde GET /api/v1/turnos/all.
 * Solo accesible para admins.
 */
export interface ClaseDetalle {
  id: number
  turno_id: number
  date: string       // "YYYY-MM-DD"
  start_time: string // "H:MM"
  end_time: string
  capacity: number
  enrolled: number
  presentes_count: number
  is_active: boolean
  cancelled_reason: string | null
  cancelled_at: string | null
}

export interface CancelPreviewAlumno {
  user_id: number
  full_name: string
  email: string
  tipo: 'suscripcion' | 'individual_completo' | 'individual_senia'
  amount: number
}

export interface CancelPreviewResponse {
  clase_id: number
  clase_date: string
  turno_description: string
  afectados: CancelPreviewAlumno[]
  total_afectados: number
}

export const getCancelPreview = (claseId: number): Promise<CancelPreviewResponse> =>
  api.get<CancelPreviewResponse>(`/clases/${claseId}/cancel-preview`).then(r => r.data)

export const cancelClase = (claseId: number, reason: string): Promise<{ message: string }> =>
  api.post(`/clases/${claseId}/cancel`, { reason }).then(r => r.data)

export interface UpdateClaseHorarioPayload {
  date: string        // "YYYY-MM-DD"
  start_time: string  // "HH:MM"
  end_time: string    // "HH:MM"
  capacity: number
}

export const updateClaseHorario = (
  claseId: number,
  payload: UpdateClaseHorarioPayload,
): Promise<{ message: string }> =>
  api.patch(`/clases/${claseId}/horario`, payload).then(r => r.data)

export const getClasesByTurno = async (turnoId: number): Promise<ClaseDetalle[]> => {
  const res = await api.get<ClaseDetalle[]>(`/turnos/${turnoId}/clases`)
  return res.data
}

export const getClasesByTurnoAdmin = async (turnoId: number): Promise<ClaseDetalle[]> => {
  const res = await api.get<ClaseDetalle[]>(`/turnos/${turnoId}/clases`, { params: { include_past: true } })
  return res.data
}

export const previewGenerateClasses = async (turnoId: number): Promise<{ date_from: string; date_to: string; count: number }> => {
  const res = await api.get(`/turnos/${turnoId}/generate-classes/preview`)
  return res.data
}

export const generateClasses = async (turnoId: number): Promise<{ generated: number }> => {
  const res = await api.post(`/turnos/${turnoId}/generate-classes`)
  return res.data
}

export const getTurnosAll = async (params?: {
  activity_id?: number
  has_availability?: boolean
  page?: number
  page_size?: number
}): Promise<TurnoPageResponse> => {
  const res = await api.get('/turnos/all', { params })
  return res.data
}

/**
 * Obtiene todas las actividades (activas e inactivas) desde GET /api/v1/activities.
 * Usado para construir los mapas de nombre e instructor en la grilla.
 */
export const getAllActivities = async (): Promise<ActivityOption[]> => {
  const res = await api.get('/activities/all')
  return res.data
}

/**
 * Crea una nueva actividad desde POST /api/v1/activities.
 * Requiere rol admin.
 */
export const createActivity = async (
  payload: CreateActivityPayload
): Promise<{ message?: string }> => {
  const res = await api.post('/activities', payload)
  return res.data
}

export interface UpdateActivityPayload {
  name?:        string
  description?: string
  is_active?:   boolean
}

export interface DeactivationImpact {
  affected_clients: number
}

/**
 * Obtiene una actividad por ID.
 * Como el backend no expone GET /activities/{id}, se usa GET /activities/all
 * (disponible para admins) y se filtra localmente por ID.
 */
export const getActivityById = async (id: number): Promise<ActivityOption> => {
  const res = await api.get('/activities/all')
  const activities: ActivityOption[] = res.data
  const found = activities.find(a => a.id === id)
  if (!found) throw new Error(`Actividad con id ${id} no encontrada.`)
  return found
}

/**
 * Actualiza una actividad con PATCH /api/v1/activities/{id}.
 * Si is_active cambia a false, el backend cancela clases futuras y notifica clientes.
 */
export const updateActivity = async (
  id: number,
  payload: UpdateActivityPayload
): Promise<{ message?: string }> => {
  const res = await api.patch(`/activities/${id}`, payload)
  return res.data
}

/**
 * Consulta cuántos clientes se verían afectados al desactivar una actividad.
 * GET /api/v1/activities/{id}/deactivation-impact
 */
export const getDeactivationImpact = async (id: number): Promise<DeactivationImpact> => {
  const res = await api.get(`/activities/${id}/deactivation-impact`)
  return res.data
}

export interface UpdateTurnoPayload {
  salon_id?:    number
  description?: string
  days?:        string[]
  start_time?:  string
  end_time?:    string
  capacity?:    number
  class_price?: number
  start_date?:  string   // "YYYY-MM-DD"
  is_active?:   boolean
}

/**
 * Actualiza un turno existente con PATCH /api/v1/turnos/{id}.
 * Requiere rol admin y que el turno no tenga inscripciones activas.
 */
export const updateTurno = async (
  turnoId: number,
  payload: UpdateTurnoPayload
): Promise<{ message: string }> => {
  await api.patch(`/turnos/${turnoId}`, payload)
  return { message: 'Turno modificado con éxito' }
}

/** Payload completo para editar un turno (PUT /api/v1/turnos/{id}). */
export interface EditTurnoPayload {
  salon_id:    number
  description: string
  instructor:  string
  start_time:  string
  end_time:    string
  capacity:    number
  class_price: number
  days:        string[]
}

/** Impacto previo a aplicar la edición (POST /api/v1/turnos/{id}/update-preview). */
export interface UpdateTurnoPreview {
  horario_cambia:       boolean
  dias_agregados:       string[]
  dias_quitados:        string[]
  clases_a_cancelar:    number
  clientes_afectados:   number
  creditos_a_generar:   number
  clases_a_generar:     number
  usuarios_a_notificar: number
  cupo_insuficiente:      boolean
  max_inscriptos_futuros: number
}

/**
 * Calcula el impacto de editar un turno sin aplicar cambios.
 * Informa clases a cancelar, créditos a generar y usuarios a notificar.
 */
export const previewTurnoUpdate = async (
  turnoId: number,
  payload: EditTurnoPayload
): Promise<UpdateTurnoPreview> => {
  const res = await api.post(`/turnos/${turnoId}/update-preview`, payload)
  return res.data
}

/**
 * Aplica la edición de un turno con PUT /api/v1/turnos/{id}.
 * El backend propaga el nuevo horario a clases futuras, cancela las de días
 * quitados (generando créditos) y genera las de días agregados.
 */
export const editTurno = async (
  turnoId: number,
  payload: EditTurnoPayload
): Promise<void> => {
  await api.put(`/turnos/${turnoId}`, payload)
}

/** Impacto de dar de baja un turno entero (GET /api/v1/turnos/{id}/deactivation-impact). */
export interface TurnoDeactivationImpact {
  clases_a_cancelar:    number
  creditos_a_generar:   number
  clientes_afectados:   number
  suscripciones_a_baja: number
  usuarios_a_notificar: number
}

export const getTurnoDeactivationImpact = async (
  turnoId: number
): Promise<TurnoDeactivationImpact> => {
  const res = await api.get(`/turnos/${turnoId}/deactivation-impact`)
  return res.data
}

// ─── Inscripción a clase individual (INS-09.01) ───────────────────────────────

export interface SingleEnrollmentResponse {
  id: number
  turno_id: number
  amount: string
  status: 'pending'
  expires_at: string
}

/**
 * Inscribe al usuario autenticado en una o más clases individuales.
 * ⚠ El endpoint actual usa el usuario del JWT — para inscribir on-behalf-of
 *   un cliente, el backend debe agregar soporte a `user_id` y `payment_type`.
 *   Ver docs/pendientes-backend.md § 13.
 */
export const createSingleEnrollment = async (
  claseIds: number[],
): Promise<SingleEnrollmentResponse> => {
  const res = await api.post<SingleEnrollmentResponse>('/single-enrollments', {
    clase_ids: claseIds,
  })
  return res.data
}

/**
 * Extrae el mensaje de error legible del formato de error del backend.
 * El backend siempre retorna: { errors: { general: "..." } } o { errors: { field: "..." } }
 * Ver app/api/exception_handlers.py
 */
export const extractBackendError = (error: unknown): string => {
  const axiosError = error as { response?: { data?: { errors?: Record<string, string> } } }
  const errors = axiosError?.response?.data?.errors

  if (!errors) return 'Ocurrió un error inesperado. Intentá de nuevo.'

  // Priorizar el error general; si no, tomar el primer error de campo
  return errors.general ?? Object.values(errors)[0] ?? 'Ocurrió un error inesperado.'
}
