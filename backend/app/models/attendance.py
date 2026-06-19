from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.domain.attendance import AttendanceStatus
from app.models.mixins import IDMixin


class Attendance(IDMixin, Base):
    __tablename__ = "attendances"
    __table_args__ = (
        UniqueConstraint("user_id", "clase_id", name="uq_attendance_user_clase"),
    )

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    clase_id = Column(Integer, ForeignKey("clases.id"), nullable=False)
    status = Column(
        Enum(AttendanceStatus, name="attendance_status_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    marked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    clase = relationship("Clase")
