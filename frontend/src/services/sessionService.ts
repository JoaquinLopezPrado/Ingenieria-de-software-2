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
 * Usan nombres amigables para el formulario (camelCase, días en español con mayúscula).
 */
export interface SessionFormData {
  activity_id: number
  description: string
  days: string[]        // valores de visualización: "Lunes", "Miércoles", etc.
  startTime: string     // "HH:MM"
  endTime: string       // "HH:MM"
  maxCapacity: number
  month: number         // 1–12, seleccionado por el admin
  year: number          // >= 2024, seleccionado por el admin
  // PENDIENTE BACKEND: el campo is_active se envía en el payload pero el backend
  // lo ignora hasta que tu compañero lo agregue a CreateTurnoRequest.
  // Ver docs/integracion-backend.md → "Qué hablar con tu compañero".
  is_active: boolean
}

/**
 * Opción de actividad para el select.
 * Incluye el instructor para mostrarlo en el formulario sin campo extra.
 *
 * PENDIENTE BACKEND: Reemplazar con datos reales cuando exista GET /api/v1/activities.
 * Ver docs/integracion-backend.md → Sección "Pendientes".
 */
export interface ActivityOption {
  id: number
  name: string
  instructor: string
}

// ─── Mapeo de días ────────────────────────────────────────────────────────────

/**
 * Convierte los días del formulario al enum DiaSemana del backend.
 * Backend: app/domain/turno.py → DiaSemana (lowercase, sin tildes)
 */
const DAY_TO_BACKEND: Record<string, string> = {
  'Lunes':     'lunes',
  'Martes':    'martes',
  'Miércoles': 'miercoles',
  'Jueves':    'jueves',
  'Viernes':   'viernes',
  'Sábado':    'sabado',
}

// ─── Funciones ────────────────────────────────────────────────────────────────

/**
 * Carga las opciones del formulario (actividades disponibles).
 *
 * ESTADO ACTUAL: Mock local — el backend no tiene GET /api/v1/activities todavía.
 * MIGRACIÓN: Cuando el backend implemente el endpoint, reemplazar por:
 *
 *   const res = await api.get('/activities')
 *   return { activities: res.data }
 *
 * El array `res.data` tendrá la forma ActivityResponse[]:
 *   { id: number, name: string, instructor: string, is_active: boolean }
 */
export const getFormOptions = async (): Promise<{ activities: ActivityOption[] }> => {
  return {
    activities: [
      { id: 1, name: 'Yoga',      instructor: 'Lic. Valentina Ríos'  },
      { id: 2, name: 'Funcional', instructor: 'Prof. Martina Solís'  },
      { id: 3, name: 'Pilates',   instructor: 'Prof. Lucas Méndez'   },
    ],
  }
}

/**
 * Crea un nuevo turno llamando a POST /api/v1/turnos.
 *
 * Transformaciones aplicadas al payload:
 *   - days:        "Lunes" → "lunes"  (DAY_TO_BACKEND)
 *   - startTime:   camelCase → start_time (snake_case)
 *   - endTime:     camelCase → end_time   (snake_case)
 *   - maxCapacity: → capacity
 *   - month/year:  se auto-completan con la fecha actual
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
    activity_id:  formData.activity_id,
    description:  formData.description,
    start_time:   formData.startTime,
    end_time:     formData.endTime,
    capacity:     formData.maxCapacity,
    month:        formData.month,
    year:         formData.year,
    days:         formData.days.map(d => DAY_TO_BACKEND[d]),
    // El backend ignora is_active hasta que tu compañero lo agregue al schema.
    // Una vez que lo agregue, este campo ya estará llegando con el valor correcto.
    is_active:    formData.is_active,
  }

  // axios lanza una excepción automáticamente para respuestas 4xx/5xx
  await api.post('/turnos', payload)

  return { message: 'Turno programado con éxito' }
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
