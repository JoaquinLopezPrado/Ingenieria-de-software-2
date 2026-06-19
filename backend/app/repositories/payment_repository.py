from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.payment import Payment
from app.models.payment import Payment as PaymentORM


class AbstractPaymentRepository(ABC):

    @abstractmethod
    async def create(
        self,
        amount: Decimal,
        class_price_snapshot: Decimal,
        num_classes_snapshot: int,
        payment_provider_id: str,
        confirmed_at: datetime,
        activity_id: int | None,
        activity_name_snapshot: str,
        month_snapshot: int,
        year_snapshot: int,
        source_type_snapshot: str,
        subscription_charge_id: int | None = None,
        single_enrollment_id: int | None = None,
    ) -> Payment:
        raise NotImplementedError


class PaymentRepository(AbstractPaymentRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        amount: Decimal,
        class_price_snapshot: Decimal,
        num_classes_snapshot: int,
        payment_provider_id: str,
        confirmed_at: datetime,
        activity_id: int | None,
        activity_name_snapshot: str,
        month_snapshot: int,
        year_snapshot: int,
        source_type_snapshot: str,
        subscription_charge_id: int | None = None,
        single_enrollment_id: int | None = None,
    ) -> Payment:
        orm = PaymentORM(
            amount=amount,
            class_price_snapshot=class_price_snapshot,
            num_classes_snapshot=num_classes_snapshot,
            payment_provider_id=payment_provider_id,
            confirmed_at=confirmed_at,
            activity_id=activity_id,
            activity_name_snapshot=activity_name_snapshot,
            month_snapshot=month_snapshot,
            year_snapshot=year_snapshot,
            source_type_snapshot=source_type_snapshot,
            subscription_charge_id=subscription_charge_id,
            single_enrollment_id=single_enrollment_id,
        )
        self._session.add(orm)
        await self._session.flush()
        return self._to_domain(orm)

    def _to_domain(self, orm: PaymentORM) -> Payment:
        return Payment(
            id=orm.id,
            amount=orm.amount,
            class_price_snapshot=orm.class_price_snapshot,
            num_classes_snapshot=orm.num_classes_snapshot,
            payment_provider_id=orm.payment_provider_id,
            confirmed_at=orm.confirmed_at,
            activity_id=orm.activity_id,
            activity_name_snapshot=orm.activity_name_snapshot,
            month_snapshot=orm.month_snapshot,
            year_snapshot=orm.year_snapshot,
            source_type_snapshot=orm.source_type_snapshot,
            subscription_charge_id=orm.subscription_charge_id,
            single_enrollment_id=orm.single_enrollment_id,
        )
