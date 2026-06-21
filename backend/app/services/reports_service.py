from datetime import date
from decimal import Decimal

from app.repositories.reports_repository import ReportsRepository
from app.schemas.reports import (
    AusenciaItem,
    AusenciasResponse,
    CancelacionItem,
    CancelacionesResponse,
    IngresosMesItem,
    IngresosResponse,
    OcupacionItem,
    OcupacionResponse,
)

_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


class ReportsService:

    def __init__(self, repo: ReportsRepository):
        self._repo = repo

    async def get_ingresos(self, desde: date, hasta: date) -> IngresosResponse:
        rows = await self._repo.get_ingresos(desde, hasta)

        items = [
            IngresosMesItem(mes=r.month_snapshot, anio=r.year_snapshot, total=r.total)
            for r in rows
        ]

        total_acumulado = sum((i.total for i in items), Decimal(0))
        promedio_mensual = (
            total_acumulado / len(items) if items else Decimal(0)
        )

        mejor = max(items, key=lambda i: i.total) if items else None
        mejor_mes_label = (
            f"{_MESES[mejor.mes - 1]} {mejor.anio}" if mejor else None
        )
        mejor_mes_total = mejor.total if mejor else Decimal(0)

        return IngresosResponse(
            items=items,
            total_acumulado=total_acumulado,
            promedio_mensual=promedio_mensual,
            mejor_mes_label=mejor_mes_label,
            mejor_mes_total=mejor_mes_total,
        )

    async def get_ocupacion(self, desde: date, hasta: date) -> OcupacionResponse:
        rows = await self._repo.get_ocupacion(desde, hasta)

        items = [OcupacionItem(franja=franja, ocupacion_pct=pct) for franja, pct in rows]

        ocupacion_promedio = (
            round(sum(i.ocupacion_pct for i in items) / len(items), 1) if items else 0.0
        )
        franja_mas_ocupada = (
            max(items, key=lambda i: i.ocupacion_pct).franja if items else None
        )
        turnos_baja_ocupacion = sum(1 for i in items if i.ocupacion_pct < 50)

        return OcupacionResponse(
            items=items,
            franja_mas_ocupada=franja_mas_ocupada,
            ocupacion_promedio=ocupacion_promedio,
            turnos_baja_ocupacion=turnos_baja_ocupacion,
        )

    async def get_ausencias(self, desde: date, hasta: date) -> AusenciasResponse:
        items_raw, total_ausencias, total_registros = await self._repo.get_ausencias(desde, hasta)

        items = [AusenciaItem(actividad=name, ausencias=count) for name, count in items_raw]

        tasa = (
            round(total_ausencias / total_registros * 100, 1)
            if total_registros > 0
            else 0.0
        )
        actividad_mas_afectada = items[0].actividad if items else None

        return AusenciasResponse(
            items=items,
            total_ausencias=total_ausencias,
            total_registros=total_registros,
            tasa_ausentismo_pct=tasa,
            actividad_mas_afectada=actividad_mas_afectada,
        )

    async def get_cancelaciones(self, desde: date, hasta: date) -> CancelacionesResponse:
        cliente_raw, cliente_total, centro_raw, centro_total = await self._repo.get_cancelaciones(desde, hasta)

        items = [CancelacionItem(actividad=name, cancelaciones=count) for name, count in cliente_raw]
        centro_items = [CancelacionItem(actividad=name, cancelaciones=count) for name, count in centro_raw]

        return CancelacionesResponse(
            items=items,
            total_cancelaciones=cliente_total,
            actividad_mas_bajas=items[0].actividad if items else None,
            clases_canceladas_centro=centro_items,
            total_clases_canceladas_centro=centro_total,
        )
