from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.clase import ClaseHoy
from app.repositories.clase_repository import ClaseRepository
from app.schemas.clases import UpdateClaseHorarioRequest


class ClaseService:
    """Operaciones sobre clases individuales que no implican cancelación."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._clase_repo = ClaseRepository(session)

    async def change_schedule(
        self, clase_id: int, req: UpdateClaseHorarioRequest, admin_id: int
    ) -> None:
        # No se admiten inscriptos para poder editar (ver update_schedule), así que
        # no hay a quién notificar: el cambio nunca afecta a ningún alumno.
        await self._clase_repo.update_schedule(
            clase_id, req.date, req.start_time, req.end_time, req.capacity
        )

    async def get_clases_hoy(self) -> list[ClaseHoy]:
        return await self._clase_repo.list_hoy(today=date.today())
