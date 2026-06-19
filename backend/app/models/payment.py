from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.mixins import IDMixin


class Payment(IDMixin, Base):
    __tablename__ = "payments"

    # Fuente del pago: exactamente una de las dos FKs está poblada.
    subscription_charge_id = Column(Integer, ForeignKey("subscription_charges.id"), nullable=True)
    single_enrollment_id = Column(Integer, ForeignKey("single_enrollments.id"), nullable=True)

    amount = Column(Numeric(10, 2), nullable=False)
    class_price_snapshot = Column(Numeric(10, 2), nullable=False)
    num_classes_snapshot = Column(Integer, nullable=False)
    payment_provider_id = Column(String, nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=False)

    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    activity_name_snapshot = Column(String, nullable=False)
    month_snapshot = Column(Integer, nullable=False)
    year_snapshot = Column(Integer, nullable=False)
    # "subscription" | "single"
    source_type_snapshot = Column(String, nullable=False)

    subscription_charge = relationship("SubscriptionCharge", back_populates="payments")
    single_enrollment = relationship("SingleEnrollment", back_populates="payments")
