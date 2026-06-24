from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.single_enrollment import SingleEnrollmentStatus
from app.domain.subscription import ChargeStatus, OCCUPYING_SUBSCRIPTION_STATUSES
from app.models.auth import User as UserORM
from app.models.class_credit import ClassCredit as ClassCreditORM
from app.models.clase import Clase as ClaseORM
from app.models.profile import ClientProfile
from app.models.single_enrollment import SingleEnrollment as SingleEnrollmentORM, SingleEnrollmentSlot as SingleSlotORM
from app.models.subscription import Subscription as SubscriptionORM, SubscriptionCharge as SubscriptionChargeORM
from app.models.turno import Turno as TurnoORM
from app.repositories.capacity import ACTIVE_SINGLE_STATUSES
from app.schemas.clases import CancelPreviewAlumno, CancelPreviewResponse

_CREDIT_DAYS = 30

# Statuses that mean the class was fully paid
_FULL_PAID_STATUSES = {SingleEnrollmentStatus.CONFIRMED}
_DEPOSIT_STATUSES = {SingleEnrollmentStatus.DEPOSIT_PAID}


class ClaseCancellationRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_cancel_preview(self, clase_id: int) -> CancelPreviewResponse:
        clase, turno = await self._get_clase_and_turno(clase_id)
        afectados = await self._build_afectados(clase_id, turno)
        return CancelPreviewResponse(
            clase_id=clase_id,
            clase_date=str(clase.date),
            turno_description=turno.description,
            afectados=afectados,
            total_afectados=len(afectados),
        )

    async def cancel_clase(
        self, clase_id: int, reason: str, cancelled_by_id: int
    ) -> List[CancelPreviewAlumno]:
        clase, turno = await self._get_clase_and_turno(clase_id)
        afectados = await self._build_afectados(clase_id, turno)

        now = datetime.now(timezone.utc)
        clase.cancelled_reason = reason
        clase.cancelled_at = now
        clase.cancelled_by_id = cancelled_by_id
        clase.is_active = False

        for alumno in afectados:
            # Abonados y sueltas completas reciben el mismo crédito de clase
            # (canjeable en cualquier actividad). Las señas solo reciben email.
            if alumno.tipo in ("suscripcion", "individual_completo"):
                await self._create_credit(alumno.user_id, turno.id, clase_id, alumno.amount, now)

        await self._session.flush()
        return afectados

    async def _get_clase_and_turno(self, clase_id: int):
        result = await self._session.execute(
            select(ClaseORM, TurnoORM)
            .join(TurnoORM, TurnoORM.id == ClaseORM.turno_id)
            .where(ClaseORM.id == clase_id)
        )
        row = result.first()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clase no encontrada.")
        clase, turno = row
        if clase.cancelled_at is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La clase ya fue cancelada.")
        today = datetime.now(timezone.utc).date()
        if clase.date <= today:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Solo se pueden cancelar clases futuras.")
        return clase, turno

    async def _build_afectados(self, clase_id: int, turno: TurnoORM) -> List[CancelPreviewAlumno]:
        afectados: List[CancelPreviewAlumno] = []
        seen: set[int] = set()

        # ── Suscriptores activos en la fecha de la clase ──────────────────
        clase_result = await self._session.execute(
            select(ClaseORM.date).where(ClaseORM.id == clase_id)
        )
        clase_date = clase_result.scalar_one()

        subs_result = await self._session.execute(
            select(SubscriptionORM, UserORM, ClientProfile)
            .join(UserORM, UserORM.id == SubscriptionORM.user_id)
            .outerjoin(ClientProfile, ClientProfile.user_id == UserORM.id)
            .where(
                SubscriptionORM.turno_id == turno.id,
                SubscriptionORM.status.in_(OCCUPYING_SUBSCRIPTION_STATUSES),
                SubscriptionORM.start_date <= clase_date,
                (SubscriptionORM.ends_on.is_(None)) | (clase_date <= SubscriptionORM.ends_on),
            )
        )
        for sub, user, profile in subs_result:
            if user.id in seen:
                continue
            seen.add(user.id)
            name = f"{profile.first_name} {profile.last_name}" if profile else user.email
            # Solo se devuelve crédito por clases de períodos efectivamente abonados.
            pagado = await self._period_paid(sub.id, clase_date)
            afectados.append(CancelPreviewAlumno(
                user_id=user.id,
                full_name=name,
                email=user.email,
                tipo="suscripcion" if pagado else "suscripcion_impago",
                amount=Decimal(turno.class_price),
            ))

        # ── Inscriptos a clase individual ─────────────────────────────────
        singles_result = await self._session.execute(
            select(SingleEnrollmentORM, UserORM, ClientProfile)
            .join(SingleSlotORM, SingleSlotORM.enrollment_id == SingleEnrollmentORM.id)
            .join(UserORM, UserORM.id == SingleEnrollmentORM.user_id)
            .outerjoin(ClientProfile, ClientProfile.user_id == UserORM.id)
            .where(
                SingleSlotORM.clase_id == clase_id,
                SingleEnrollmentORM.status.in_([
                    SingleEnrollmentStatus.CONFIRMED,
                    SingleEnrollmentStatus.DEPOSIT_PAID,
                ]),
            )
        )
        for enrollment, user, profile in singles_result:
            if user.id in seen:
                continue
            seen.add(user.id)
            name = f"{profile.first_name} {profile.last_name}" if profile else user.email
            if enrollment.status == SingleEnrollmentStatus.CONFIRMED:
                tipo = "individual_completo"
                amount = Decimal(turno.class_price)
            else:
                tipo = "individual_senia"
                amount = Decimal(enrollment.deposit_amount or 0)
            afectados.append(CancelPreviewAlumno(
                user_id=user.id,
                full_name=name,
                email=user.email,
                tipo=tipo,
                amount=amount,
            ))

        return afectados

    async def _period_paid(self, subscription_id: int, clase_date: date) -> bool:
        """¿El período (mes/año) de la clase tiene un cargo PAID en esa suscripción?"""
        result = await self._session.execute(
            select(SubscriptionChargeORM.id).where(
                SubscriptionChargeORM.subscription_id == subscription_id,
                SubscriptionChargeORM.period_month == clase_date.month,
                SubscriptionChargeORM.period_year == clase_date.year,
                SubscriptionChargeORM.status == ChargeStatus.PAID,
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def _create_credit(
        self, user_id: int, turno_id: int, clase_id: int, amount: Decimal, now: datetime
    ) -> None:
        expires_at = now + timedelta(days=_CREDIT_DAYS)
        self._session.add(ClassCreditORM(
            user_id=user_id,
            turno_id=turno_id,
            source_clase_id=clase_id,
            amount=amount,
            expires_at=expires_at,
        ))

    async def get_credits_for_user(self, user_id: int) -> list[ClassCreditORM]:
        # Los créditos son cross-actividad: el usuario los canjea en cualquier turno,
        # por eso no se filtran por turno de origen.
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            select(ClassCreditORM)
            .options(selectinload(ClassCreditORM.source_clase))
            .where(
                ClassCreditORM.user_id == user_id,
                ClassCreditORM.used_at.is_(None),
                ClassCreditORM.expires_at > now,
            )
        )
        return list(result.scalars())

    async def get_credit_by_id(self, credit_id: int, user_id: int) -> ClassCreditORM | None:
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            select(ClassCreditORM).where(
                ClassCreditORM.id == credit_id,
                ClassCreditORM.user_id == user_id,
                ClassCreditORM.used_at.is_(None),
                ClassCreditORM.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def mark_credit_used(self, credit_id: int, used_for_clase_id: int) -> None:
        now = datetime.now(timezone.utc)
        await self._session.execute(
            update(ClassCreditORM)
            .where(ClassCreditORM.id == credit_id)
            .values(used_at=now, used_for_clase_id=used_for_clase_id)
        )

    async def get_schedule_change_recipients(self, turno_id: int, from_date: date) -> list[tuple]:
        """Usuarios a notificar ante un cambio de horario/días: abonados que ocupan
        asiento futuro + sueltas con clase futura en el turno. Devuelve (user_id,
        email, first_name) sin repetir usuarios."""
        subs = await self._session.execute(
            select(UserORM.id, UserORM.email, ClientProfile.first_name)
            .join(SubscriptionORM, SubscriptionORM.user_id == UserORM.id)
            .outerjoin(ClientProfile, ClientProfile.user_id == UserORM.id)
            .where(
                SubscriptionORM.turno_id == turno_id,
                SubscriptionORM.status.in_(OCCUPYING_SUBSCRIPTION_STATUSES),
                (SubscriptionORM.ends_on.is_(None)) | (SubscriptionORM.ends_on > from_date),
            )
        )
        singles = await self._session.execute(
            select(UserORM.id, UserORM.email, ClientProfile.first_name)
            .join(SingleEnrollmentORM, SingleEnrollmentORM.user_id == UserORM.id)
            .join(SingleSlotORM, SingleSlotORM.enrollment_id == SingleEnrollmentORM.id)
            .join(ClaseORM, ClaseORM.id == SingleSlotORM.clase_id)
            .outerjoin(ClientProfile, ClientProfile.user_id == UserORM.id)
            .where(
                ClaseORM.turno_id == turno_id,
                ClaseORM.is_active == True,
                ClaseORM.date > from_date,
                SingleEnrollmentORM.status.in_(list(ACTIVE_SINGLE_STATUSES)),
            )
        )
        recipients: dict[int, tuple] = {}
        for uid, email, first_name in list(subs) + list(singles):
            recipients[uid] = (uid, email, first_name)
        return list(recipients.values())
