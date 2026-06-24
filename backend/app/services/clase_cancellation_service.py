from decimal import Decimal

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

    async def cancel_turno_baja(
        self, turno_id: int, clase_ids: list[int], reason: str, admin_id: int
    ) -> None:
        """Baja total del turno: cancela todas las clases (créditos solo por lo pagado) y
        manda UN mail-resumen por afectado, en lugar de uno por clase."""
        if not clase_ids:
            return

        row = (await self._session.execute(
            select(ActivityORM.name, TurnoORM.description)
            .join(TurnoORM, TurnoORM.activity_id == ActivityORM.id)
            .where(TurnoORM.id == turno_id)
        )).first()
        activity_name, turno_description = row if row else ("", "")

        # Acumular por usuario a lo largo de todas las clases canceladas.
        resumen: dict[int, dict] = {}
        for clase_id in clase_ids:
            for a in await self._repo.cancel_clase(clase_id, reason, admin_id):
                acc = resumen.setdefault(a.user_id, {
                    "email": a.email,
                    "first_name": a.full_name.split()[0] if a.full_name else "cliente",
                    "clases": 0,
                    "creditos": 0,
                    "senia": Decimal("0"),
                })
                acc["clases"] += 1
                if a.tipo in ("suscripcion", "individual_completo"):
                    acc["creditos"] += 1
                elif a.tipo == "individual_senia":
                    acc["senia"] += a.amount

        for acc in resumen.values():
            self._email.send_turno_baja(
                to=acc["email"],
                first_name=acc["first_name"],
                activity_name=activity_name,
                turno_description=turno_description,
                clases_canceladas=acc["clases"],
                creditos=acc["creditos"],
                senia=acc["senia"],
                expires_days=_CREDIT_DAYS,
                reason=reason,
            )

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
