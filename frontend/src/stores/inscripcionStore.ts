import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Cliente } from '@/services/inscripcionService'
import type { Turno } from '@/services/sessionService'
import type { ClaseInscribible } from '@/views/inscripciones/CalendarioClasesInscripcionView.vue'

export interface WaitlistEntry {
  entry_id: number
  turno_id: number
}

export interface SubscriptionEntry {
  subscription_id: number
  turno_id: number
  status: string  // 'ACTIVE' | 'PENDING_CANCEL' | etc.
}

export const useInscripcionStore = defineStore('inscripcion', () => {
  const clienteSeleccionado = ref<Cliente | null>(null)
  const turnoSeleccionado = ref<Turno | null>(null)
  const claseSeleccionada = ref<ClaseInscribible | null>(null)
  const waitlistEntries = ref<WaitlistEntry[]>([])
  const enrolledClaseIds = ref<number[]>([])
  const subscriptionEntries = ref<SubscriptionEntry[]>([])

  function setCliente(cliente: Cliente | null) {
    clienteSeleccionado.value = cliente
    waitlistEntries.value = []
    enrolledClaseIds.value = []
    subscriptionEntries.value = []
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

  function setEnrolledClaseIds(ids: number[]) {
    enrolledClaseIds.value = ids
  }

  function markClaseEnrolled(claseId: number) {
    if (!enrolledClaseIds.value.includes(claseId)) {
      enrolledClaseIds.value.push(claseId)
    }
  }

  function setSubscriptionEntries(entries: SubscriptionEntry[]) {
    subscriptionEntries.value = entries
  }

  function getSubscriptionEntry(turnoId: number): SubscriptionEntry | undefined {
    return subscriptionEntries.value.find(e => e.turno_id === turnoId)
  }

  function markSubscriptionPendingCancel(subscriptionId: number) {
    subscriptionEntries.value = subscriptionEntries.value.map(e =>
      e.subscription_id === subscriptionId ? { ...e, status: 'PENDING_CANCEL' } : e
    )
  }

  function reset() {
    clienteSeleccionado.value = null
    turnoSeleccionado.value = null
    claseSeleccionada.value = null
    waitlistEntries.value = []
    enrolledClaseIds.value = []
    subscriptionEntries.value = []
  }

  return {
    clienteSeleccionado, turnoSeleccionado, claseSeleccionada,
    waitlistEntries, enrolledClaseIds, subscriptionEntries,
    setCliente, setTurno, setClase,
    markWaitlisted, setWaitlistEntries, removeWaitlistEntry, getWaitlistEntry,
    setEnrolledClaseIds, markClaseEnrolled,
    setSubscriptionEntries, getSubscriptionEntry, markSubscriptionPendingCancel,
    reset,
  }
})
