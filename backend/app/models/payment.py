from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.domain.enrollment import EnrollmentType
from app.models.mixins import IDMixin


class Payment(IDMixin, Base):
    __tablename__ = "payments"

    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    class_price_snapshot = Column(Numeric(10, 2), nullable=False)
    num_classes_snapshot = Column(Integer, nullable=False)
    payment_provider_id = Column(String, nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=False)

    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    activity_name_snapshot = Column(String, nullable=False)
    month_snapshot = Column(Integer, nullable=False)
    year_snapshot = Column(Integer, nullable=False)
    enrollment_type_snapshot = Column(
        Enum(EnrollmentType, name="enrollment_type_enum", create_constraint=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    enrollment = relationship("Enrollment", back_populates="payments")
