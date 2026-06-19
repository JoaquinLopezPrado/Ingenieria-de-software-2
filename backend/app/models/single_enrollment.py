from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.domain.single_enrollment import SingleEnrollmentStatus
from app.models.mixins import IDMixin, TimestampMixin


class SingleEnrollment(IDMixin, TimestampMixin, Base):
    __tablename__ = "single_enrollments"

    turno_id = Column(Integer, ForeignKey("turnos.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(
        Enum(SingleEnrollmentStatus, name="single_enrollment_status_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    expires_at = Column(DateTime(timezone=True), nullable=True)
    payment_id = Column(String, nullable=True)
    deposit_amount = Column(Numeric(10, 2), nullable=True)
    deposit_payment_id = Column(String, nullable=True)
    refund_id = Column(String, nullable=True)

    turno = relationship("Turno", back_populates="single_enrollments")
    slots = relationship("SingleEnrollmentSlot", back_populates="enrollment", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="single_enrollment")


class SingleEnrollmentSlot(IDMixin, Base):
    __tablename__ = "single_enrollment_slots"

    enrollment_id = Column(Integer, ForeignKey("single_enrollments.id", ondelete="CASCADE"), nullable=False)
    clase_id = Column(Integer, ForeignKey("clases.id"), nullable=False)

    enrollment = relationship("SingleEnrollment", back_populates="slots")
    clase = relationship("Clase", back_populates="single_slots")
