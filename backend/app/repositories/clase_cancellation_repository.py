from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.single_enrollment import SingleEnrollmentStatus
from app.domain.subscription import ChargeStatus, SubscriptionStatus, OCCUPYING_SUBSCRIPTION_STATUSES
from app.models.auth import User as UserORM
from app.models.class_credit import ClassCredit as ClassCreditORM
from app.models.clase import Clase as ClaseORM
from app.models.profile import ClientProfile
from app.models.single_enrollment import SingleEnrollment as SingleEnrollmentORM, SingleEnrollmentSlot as SingleSlotORM
from app.models.subscription import Subscription as SubscriptionORM, SubscriptionCharge as SubscriptionChargeORM
from app.models.subscription_class_discount import SubscriptionClassDiscount as DiscountORM
from app.models.turno import Turno as TurnoORM
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
            if alumno.tipo == "suscripcion":
                await self._apply_subscription_discount(alumno.user_id, turno.id, clase_id, alumno.amount, now)
            elif alumno.tipo == "individual_completo":
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
            afectados.append(CancelPreviewAlumno(
                user_id=user.id,
                full_name=name,
                email=user.email,
                tipo="suscripcion",
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

    async def _apply_subscription_discount(
        self, user_id: int, turno_id: int, clase_id: int, amount: Decimal, now: datetime
    ) -> None:
        # Buscar suscripción activa del usuario para este turno
        sub_result = await self._session.execute(
            select(SubscriptionORM).where(
                SubscriptionORM.user_id == user_id,
                SubscriptionORM.turno_id == turno_id,
                SubscriptionORM.status.in_(OCCUPYING_SUBSCRIPTION_STATUSES),
            )
        )
        sub = sub_result.scalar_one_or_none()
        if sub is None:
            return

        # Intentar aplicar al próximo cargo pendiente
        charge_result = await self._session.execute(
            select(SubscriptionChargeORM).where(
                SubscriptionChargeORM.subscription_id == sub.id,
                SubscriptionChargeORM.status.in_([ChargeStatus.PENDING, ChargeStatus.OVERDUE]),
            ).order_by(
                SubscriptionChargeORM.period_year,
                SubscriptionChargeORM.period_month,
            ).limit(1)
        )
        charge = charge_result.scalar_one_or_none()

        if charge is not None:
            if charge.original_amount is None:
                charge.original_amount = charge.amount
            charge.amount = max(Decimal("0.00"), Decimal(charge.amount) - amount)
            self._session.add(DiscountORM(
                subscription_id=sub.id,
                source_clase_id=clase_id,
                amount=amount,
                applied_to_charge_id=charge.id,
            ))
        else:
            # Sin cargo pendiente → guardar para aplicar al próximo que se genere
            self._session.add(DiscountORM(
                subscription_id=sub.id,
                source_clase_id=clase_id,
                amount=amount,
                applied_to_charge_id=None,
            ))

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

    async def get_credits_for_user_turno(self, user_id: int, turno_id: int) -> list[ClassCreditORM]:
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            select(ClassCreditORM).where(
                ClassCreditORM.user_id == user_id,
                ClassCreditORM.turno_id == turno_id,
                ClassCreditORM.used_at.is_(None),
                ClassCreditORM.expires_at > now,
            )
        )
        return list(result.scalars())
