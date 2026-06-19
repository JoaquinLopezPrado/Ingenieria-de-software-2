from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.domain.subscription import ChargeStatus, SubscriptionStatus
from app.models.mixins import IDMixin, TimestampMixin


class Subscription(IDMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    turno_id = Column(Integer, ForeignKey("turnos.id"), nullable=False)
    status = Column(
        Enum(SubscriptionStatus, name="subscription_status_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    start_date = Column(Date, nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    ends_on = Column(Date, nullable=True)  # baja programada: fin del período pagado

    turno = relationship("Turno", back_populates="subscriptions")
    charges = relationship("SubscriptionCharge", back_populates="subscription", cascade="all, delete-orphan")


class SubscriptionCharge(IDMixin, TimestampMixin, Base):
    __tablename__ = "subscription_charges"
    __table_args__ = (
        UniqueConstraint("subscription_id", "period_month", "period_year", name="uq_charge_subscription_period"),
    )

    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    period_month = Column(Integer, nullable=False)
    period_year = Column(Integer, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    original_amount = Column(Numeric(10, 2), nullable=True)
    status = Column(
        Enum(ChargeStatus, name="charge_status_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    due_date = Column(Date, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    payment_id = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    subscription = relationship("Subscription", back_populates="charges")
    payments = relationship("Payment", back_populates="subscription_charge")
