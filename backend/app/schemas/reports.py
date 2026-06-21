from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class IngresosMesItem(BaseModel):
    mes: int
    anio: int
    total: Decimal


class IngresosResponse(BaseModel):
    items: List[IngresosMesItem]
    total_acumulado: Decimal
    promedio_mensual: Decimal
    mejor_mes_label: Optional[str]
    mejor_mes_total: Decimal


class OcupacionItem(BaseModel):
    franja: str
    ocupacion_pct: float


class OcupacionResponse(BaseModel):
    items: List[OcupacionItem]
    franja_mas_ocupada: Optional[str]
    ocupacion_promedio: float
    turnos_baja_ocupacion: int


class AusenciaItem(BaseModel):
    actividad: str
    ausencias: int


class AusenciasResponse(BaseModel):
    items: List[AusenciaItem]
    total_ausencias: int
    total_registros: int
    tasa_ausentismo_pct: float
    actividad_mas_afectada: Optional[str]


class CancelacionItem(BaseModel):
    actividad: str
    cancelaciones: int


class CancelacionesResponse(BaseModel):
    items: List[CancelacionItem]
    total_cancelaciones: int
    actividad_mas_bajas: Optional[str]
    clases_canceladas_centro: List[CancelacionItem]
    total_clases_canceladas_centro: int
