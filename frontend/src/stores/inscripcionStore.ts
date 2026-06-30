import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Cliente } from '@/services/inscripcionService'
import type { Turno } from '@/services/sessionService'
import type { ClaseInscribible } from '@/views/inscripciones/CalendarioClasesInscripcionView.vue'

export const useInscripcionStore = defineStore('inscripcion', () => {
  const clienteSeleccionado = ref<Cliente | null>(null)
  const turnoSeleccionado = ref<Turno | null>(null)
  const claseSeleccionada = ref<ClaseInscribible | null>(null)
  const waitlistedTurnoIds = ref<number[]>([])

  function setCliente(cliente: Cliente | null) {
    clienteSeleccionado.value = cliente
    waitlistedTurnoIds.value = []
  }

  function setTurno(turno: Turno | null) {
    turnoSeleccionado.value = turno
  }

  function setClase(clase: ClaseInscribible | null) {
    claseSeleccionada.value = clase
  }

  function markWaitlisted(turnoId: number) {
    if (!waitlistedTurnoIds.value.includes(turnoId)) {
      waitlistedTurnoIds.value.push(turnoId)
    }
  }

  function setWaitlistedTurnoIds(ids: number[]) {
    waitlistedTurnoIds.value = ids
  }

  function reset() {
    clienteSeleccionado.value = null
    turnoSeleccionado.value = null
    claseSeleccionada.value = null
    waitlistedTurnoIds.value = []
  }

  return { clienteSeleccionado, turnoSeleccionado, claseSeleccionada, waitlistedTurnoIds, setCliente, setTurno, setClase, markWaitlisted, setWaitlistedTurnoIds, reset }
})
