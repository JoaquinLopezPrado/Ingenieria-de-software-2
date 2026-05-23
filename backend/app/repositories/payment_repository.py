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
        enrollment_id: int,
        amount: Decimal,
        class_price_snapshot: Decimal,
        num_classes_snapshot: int,
        payment_provider_id: str,
        confirmed_at: datetime,
    ) -> Payment:
        raise NotImplementedError


class PaymentRepository(AbstractPaymentRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        enrollment_id: int,
        amount: Decimal,
        class_price_snapshot: Decimal,
        num_classes_snapshot: int,
        payment_provider_id: str,
        confirmed_at: datetime,
    ) -> Payment:
        orm = PaymentORM(
            enrollment_id=enrollment_id,
            amount=amount,
            class_price_snapshot=class_price_snapshot,
            num_classes_snapshot=num_classes_snapshot,
            payment_provider_id=payment_provider_id,
            confirmed_at=confirmed_at,
        )
        self._session.add(orm)
        await self._session.flush()
        return self._to_domain(orm)

    def _to_domain(self, orm: PaymentORM) -> Payment:
        return Payment(
            id=orm.id,
            enrollment_id=orm.enrollment_id,
            amount=orm.amount,
            class_price_snapshot=orm.class_price_snapshot,
            num_classes_snapshot=orm.num_classes_snapshot,
            payment_provider_id=orm.payment_provider_id,
            confirmed_at=orm.confirmed_at,
        )
