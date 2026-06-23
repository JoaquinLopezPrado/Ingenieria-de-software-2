from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity as ActivityORM
from app.models.clase import Clase as ClaseORM
from app.models.profile import ClientProfile
from app.models.turno import Turno as TurnoORM
from app.repositories.clase_cancellation_repository import ClaseCancellationRepository, _CREDIT_DAYS
from app.schemas.clases import CancelClaseRequest, CancelPreviewResponse
from app.services.email_service import EmailService


class ClaseCancellationService:

    def __init__(self, session: AsyncSession):
        self._repo = ClaseCancellationRepository(session)
        self._session = session
        self._email = EmailService()

    async def get_preview(self, clase_id: int) -> CancelPreviewResponse:
        return await self._repo.get_cancel_preview(clase_id)

    async def cancel(self, clase_id: int, req: CancelClaseRequest, admin_id: int) -> None:
        afectados = await self._repo.cancel_clase(clase_id, req.reason, admin_id)

        # Recuperar nombres de actividad y turno para los emails
        result = await self._session.execute(
            select(ClaseORM, TurnoORM, ActivityORM)
            .join(TurnoORM, TurnoORM.id == ClaseORM.turno_id)
            .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
            .where(ClaseORM.id == clase_id)
        )
        row = result.first()
        if row is None:
            return
        clase, turno, activity = row

        # Recuperar perfiles para los nombres
        user_ids = [a.user_id for a in afectados]
        profiles_result = await self._session.execute(
            select(ClientProfile).where(ClientProfile.user_id.in_(user_ids))
        )
        profiles = {p.user_id: p for p in profiles_result.scalars()}

        for alumno in afectados:
            profile = profiles.get(alumno.user_id)
            first_name = profile.first_name if profile else alumno.full_name.split()[0]

            if alumno.tipo == "suscripcion":
                self._email.send_clase_cancelada_suscripcion(
                    to=alumno.email,
                    first_name=first_name,
                    activity_name=activity.name,
                    turno_description=turno.description,
                    clase_date=clase.date,
                    expires_days=_CREDIT_DAYS,
                    reason=req.reason,
                )
            elif alumno.tipo == "individual_completo":
                self._email.send_clase_cancelada_individual_completo(
                    to=alumno.email,
                    first_name=first_name,
                    activity_name=activity.name,
                    turno_description=turno.description,
                    clase_date=clase.date,
                    expires_days=_CREDIT_DAYS,
                    reason=req.reason,
                )
            elif alumno.tipo == "individual_senia":
                self._email.send_clase_cancelada_individual_senia(
                    to=alumno.email,
                    first_name=first_name,
                    activity_name=activity.name,
                    turno_description=turno.description,
                    clase_date=clase.date,
                    senia=alumno.amount,
                    reason=req.reason,
                )
