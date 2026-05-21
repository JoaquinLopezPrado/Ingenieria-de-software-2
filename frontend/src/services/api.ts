import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Adjunta el Bearer token en cada request si el usuario está autenticado
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// INTERCEPTOR DE RESPUESTA: Captura la expiración por tiempo (401)
api.interceptors.response.use(
  (response) => response, // Si la respuesta es exitosa, pasa de largo
  (error) => {
    if (error.response && error.response.status === 401) {
      // Si el backend dice 401, el token caducó por tiempo
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      
      // Forzamos la redirección limpiando estados residuales en memoria
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export default api
