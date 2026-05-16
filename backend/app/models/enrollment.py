from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.domain.enrollment import EnrollmentStatus, EnrollmentType
from app.models.mixins import IDMixin, TimestampMixin


class Enrollment(IDMixin, TimestampMixin, Base):
    __tablename__ = "enrollments"

    turno_id = Column(Integer, ForeignKey("turnos.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    enrollment_type = Column(
        Enum(EnrollmentType, name="enrollment_type_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(
        Enum(EnrollmentStatus, name="enrollment_status_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    expires_at = Column(DateTime(timezone=True), nullable=True)
    payment_id = Column(String, nullable=True)

    turno = relationship("Turno", back_populates="enrollments")
    slots = relationship("EnrollmentSlot", back_populates="enrollment", cascade="all, delete-orphan")


class EnrollmentSlot(IDMixin, Base):
    __tablename__ = "enrollment_slots"

    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False)
    clase_id = Column(Integer, ForeignKey("clases.id"), nullable=False)

    enrollment = relationship("Enrollment", back_populates="slots")
    clase = relationship("Clase", back_populates="slots")
