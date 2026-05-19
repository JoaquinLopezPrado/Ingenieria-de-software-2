import api from './api'

const apiClient = api


export const turnoService = {
  getTurnos: (params?: {
    activity_id?: number
    has_availability?: boolean
    page?: number
  }) => {
    return apiClient.get('/turnos', {
      params,
    })
  },

  getClasesByActividad: (activityId: string | number) => {
    return apiClient.get(`/activities/${activityId}/clases`)
  },
}