import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Cliente } from '@/services/inscripcionService'
import type { Turno } from '@/services/sessionService'
import type { ClaseInscribible } from '@/views/inscripciones/CalendarioClasesInscripcionView.vue'

export const useInscripcionStore = defineStore('inscripcion', () => {
  const clienteSeleccionado = ref<Cliente | null>(null)
  const turnoSeleccionado = ref<Turno | null>(null)
  const claseSeleccionada = ref<ClaseInscribible | null>(null)

  function setCliente(cliente: Cliente | null) {
    clienteSeleccionado.value = cliente
  }

  function setTurno(turno: Turno | null) {
    turnoSeleccionado.value = turno
  }

  function setClase(clase: ClaseInscribible | null) {
    claseSeleccionada.value = clase
  }

  function reset() {
    clienteSeleccionado.value = null
    turnoSeleccionado.value = null
    claseSeleccionada.value = null
  }

  return { clienteSeleccionado, turnoSeleccionado, claseSeleccionada, setCliente, setTurno, setClase, reset }
})
