import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Cliente } from '@/services/inscripcionService'
import type { Turno } from '@/services/sessionService'
import type { ClaseInscribible } from '@/views/inscripciones/CalendarioClasesInscripcionView.vue'

export interface WaitlistEntry {
  entry_id: number
  turno_id: number
}

export const useInscripcionStore = defineStore('inscripcion', () => {
  const clienteSeleccionado = ref<Cliente | null>(null)
  const turnoSeleccionado = ref<Turno | null>(null)
  const claseSeleccionada = ref<ClaseInscribible | null>(null)
  const waitlistEntries = ref<WaitlistEntry[]>([])

  function setCliente(cliente: Cliente | null) {
    clienteSeleccionado.value = cliente
    waitlistEntries.value = []
  }

  function setTurno(turno: Turno | null) {
    turnoSeleccionado.value = turno
  }

  function setClase(clase: ClaseInscribible | null) {
    claseSeleccionada.value = clase
  }

  function markWaitlisted(entry_id: number, turno_id: number) {
    if (!waitlistEntries.value.some(e => e.turno_id === turno_id)) {
      waitlistEntries.value.push({ entry_id, turno_id })
    }
  }

  function setWaitlistEntries(entries: WaitlistEntry[]) {
    waitlistEntries.value = entries
  }

  function removeWaitlistEntry(entry_id: number) {
    waitlistEntries.value = waitlistEntries.value.filter(e => e.entry_id !== entry_id)
  }

  function getWaitlistEntry(turno_id: number): WaitlistEntry | undefined {
    return waitlistEntries.value.find(e => e.turno_id === turno_id)
  }

  function reset() {
    clienteSeleccionado.value = null
    turnoSeleccionado.value = null
    claseSeleccionada.value = null
    waitlistEntries.value = []
  }

  return {
    clienteSeleccionado, turnoSeleccionado, claseSeleccionada, waitlistEntries,
    setCliente, setTurno, setClase,
    markWaitlisted, setWaitlistEntries, removeWaitlistEntry, getWaitlistEntry,
    reset,
  }
})
