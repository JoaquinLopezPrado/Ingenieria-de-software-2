from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.domain.waitlist import WaitlistStatus
from app.models.mixins import IDMixin, TimestampMixin


class SubscriptionWaitlist(IDMixin, TimestampMixin, Base):
    __tablename__ = "subscription_waitlist"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    turno_id = Column(Integer, ForeignKey("turnos.id", ondelete="CASCADE"), nullable=False)
    status = Column(
        Enum(WaitlistStatus, name="waitlist_status_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    joined_at = Column(DateTime(timezone=True), nullable=False)
    promoted_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    turno = relationship("Turno")
