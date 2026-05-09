// Definimos la estructura de los datos para tener autocompletado y evitar errores
export interface SessionData {
  activity: string;
  instructor: string;
  days: string[];
  startTime: string;
  endTime: string;
  maxCapacity: number | null;
  room: string;
}

export const getFormOptions = async () => {
  return {
    activities: ['Yoga', 'Functional', 'Pilates'],
    instructors: ['Lic. Valentina Ríos', 'Prof. Martina Solís', 'Prof. Lucas Méndez'],
    rooms: ['Salon 1', 'Salon 2', 'Salon Principal']
  }
}

export const createSession = async (sessionData: SessionData) => {
  console.log("Sending to backend (mocked):", sessionData)
  
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ status: 201, message: 'Session successfully scheduled' })
    }, 1000)
  })
}