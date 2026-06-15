import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Cliente } from '@/services/inscripcionService'
import type { Turno } from '@/services/sessionService'

export const useInscripcionStore = defineStore('inscripcion', () => {
  const clienteSeleccionado = ref<Cliente | null>(null)
  const turnoSeleccionado = ref<Turno | null>(null)

  function setCliente(cliente: Cliente | null) {
    clienteSeleccionado.value = cliente
  }

  function setTurno(turno: Turno | null) {
    turnoSeleccionado.value = turno
  }

  function reset() {
    clienteSeleccionado.value = null
    turnoSeleccionado.value = null
  }

  return { clienteSeleccionado, turnoSeleccionado, setCliente, setTurno, reset }
})
