from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.mixins import IDMixin


class SubscriptionClassDiscount(IDMixin, Base):
    __tablename__ = "subscription_class_discounts"

    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    source_clase_id = Column(Integer, ForeignKey("clases.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    applied_to_charge_id = Column(Integer, ForeignKey("subscription_charges.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)

    subscription = relationship("Subscription")
    source_clase = relationship("Clase")
    applied_to_charge = relationship("SubscriptionCharge")
