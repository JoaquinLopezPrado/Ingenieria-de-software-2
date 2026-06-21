from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.mixins import IDMixin, TimestampMixin


class Clase(IDMixin, TimestampMixin, Base):
    __tablename__ = "clases"

    turno_id = Column(Integer, ForeignKey("turnos.id"), nullable=False)
    date = Column(Date, nullable=False)
    capacity = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    cancelled_reason = Column(String, nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    turno = relationship("Turno", back_populates="clases")
    single_slots = relationship("SingleEnrollmentSlot", back_populates="clase")
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_id])
