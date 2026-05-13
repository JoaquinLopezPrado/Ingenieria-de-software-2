/**
 * api.ts — Cliente HTTP compartido
 * ---------------------------------
 * Instancia de axios preconfigurada con:
 *   - baseURL leída desde la variable de entorno VITE_API_URL
 *   - Interceptor que inyecta el JWT de localStorage en cada request
 *
 * Todos los servicios del frontend deben importar este cliente
 * en lugar de crear sus propias instancias de axios.
 *
 * El token se guarda bajo la clave "token" (ver authService.ts → login).
 */
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Adjunta el Bearer token en cada request si el usuario está autenticado
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api
