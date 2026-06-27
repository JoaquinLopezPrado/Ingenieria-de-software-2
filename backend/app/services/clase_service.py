from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.clase import ClaseHoy
from app.models.activity import Activity as ActivityORM
from app.models.turno import Turno as TurnoORM
from app.repositories.clase_cancellation_repository import ClaseCancellationRepository
from app.repositories.clase_repository import ClaseRepository
from app.schemas.clases import UpdateClaseHorarioRequest
from app.services.email_service import EmailService


class ClaseService:
    """Operaciones sobre clases individuales que no implican cancelación."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._clase_repo = ClaseRepository(session)
        self._cancellation_repo = ClaseCancellationRepository(session)
        self._email = EmailService()

    async def change_schedule(
        self, clase_id: int, req: UpdateClaseHorarioRequest, admin_id: int
    ) -> None:
        # Capturamos los inscriptos ANTES de mover la clase: notificamos a quienes
        # tenían su lugar con el horario anterior.
        afectados = await self._cancellation_repo.get_clase_afectados(clase_id)

        clase = await self._clase_repo.update_schedule(
            clase_id, req.date, req.start_time, req.end_time, req.capacity
        )

        if not afectados:
            return

        row = (await self._session.execute(
            select(ActivityORM.name, TurnoORM.description)
            .join(TurnoORM, TurnoORM.activity_id == ActivityORM.id)
            .where(TurnoORM.id == clase.turno_id)
        )).first()
        activity_name, turno_description = row if row else ("", "")

        horario_str = (
            f"{req.start_time.hour}:{req.start_time.minute:02d} a "
            f"{req.end_time.hour}:{req.end_time.minute:02d}"
        )
        for alumno in afectados:
            first_name = alumno.full_name.split()[0] if alumno.full_name else "cliente"
            self._email.send_cambio_horario_clase(
                to=alumno.email,
                first_name=first_name,
                activity_name=activity_name,
                turno_description=turno_description,
                clase_date=clase.date,
                horario_str=horario_str,
            )

    async def get_clases_hoy(self) -> list[ClaseHoy]:
        return await self._clase_repo.list_hoy(today=date.today())
