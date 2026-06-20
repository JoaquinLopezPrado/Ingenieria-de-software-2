import api from './api'

export interface IngresosMesItem  { mes: number; anio: number; total: number }
export interface IngresosResponse {
  items: IngresosMesItem[]
  total_acumulado: number
  promedio_mensual: number
  mejor_mes_label: string | null
  mejor_mes_total: number
}

export interface OcupacionItem    { franja: string; ocupacion_pct: number }
export interface OcupacionResponse {
  items: OcupacionItem[]
  franja_mas_ocupada: string | null
  ocupacion_promedio: number
  turnos_baja_ocupacion: number
}

export interface AusenciaItem     { actividad: string; ausencias: number }
export interface AusenciasResponse {
  items: AusenciaItem[]
  total_ausencias: number
  total_registros: number
  tasa_ausentismo_pct: number
  actividad_mas_afectada: string | null
}

export interface CancelacionItem  { actividad: string; cancelaciones: number }
export interface CancelacionesResponse {
  items: CancelacionItem[]
  total_cancelaciones: number
  actividad_mas_bajas: string | null
}

const params = (desde: string, hasta: string) => ({ desde, hasta })

export const getIngresos      = (desde: string, hasta: string) =>
  api.get<IngresosResponse>('/reports/ingresos', { params: params(desde, hasta) }).then(r => r.data)

export const getOcupacion     = (desde: string, hasta: string) =>
  api.get<OcupacionResponse>('/reports/ocupacion', { params: params(desde, hasta) }).then(r => r.data)

export const getAusencias     = (desde: string, hasta: string) =>
  api.get<AusenciasResponse>('/reports/ausencias', { params: params(desde, hasta) }).then(r => r.data)

export const getCancelaciones = (desde: string, hasta: string) =>
  api.get<CancelacionesResponse>('/reports/cancelaciones', { params: params(desde, hasta) }).then(r => r.data)
