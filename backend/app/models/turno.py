from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, Numeric, String, Time, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.domain.turno import DiaSemana
from app.models.mixins import IDMixin, TimestampMixin


class Turno(IDMixin, TimestampMixin, Base):
    __tablename__ = "turnos"

    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    # Nullable a nivel de base para no romper turnos existentes creados antes de
    # modelar Salon; a partir de ahora es obligatorio en el schema de alta/edición.
    salon_id = Column(Integer, ForeignKey("salones.id"), nullable=True)
    description = Column(String, nullable=False)
    instructor = Column(String, nullable=False)
    start_time = Column(Time(timezone=False), nullable=False)
    end_time = Column(Time(timezone=False), nullable=False)
    capacity = Column(Integer, nullable=False)
    class_price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)

    activity = relationship("Activity", back_populates="turnos")
    salon = relationship("Salon", back_populates="turnos")
    days = relationship("TurnoDia", back_populates="turno", cascade="all, delete-orphan")
    clases = relationship("Clase", back_populates="turno", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="turno")
    single_enrollments = relationship("SingleEnrollment", back_populates="turno")

    __table_args__ = (
        UniqueConstraint(
            "activity_id", "description", "start_time", "end_time", "salon_id",
            name="uq_turno_actividad_descripcion_horario",
        ),
    )


class TurnoDia(IDMixin, Base):
    __tablename__ = "turno_dias"

    turno_id = Column(Integer, ForeignKey("turnos.id", ondelete="CASCADE"), nullable=False)
    dia = Column(
        Enum(DiaSemana, name="dia_semana_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    turno = relationship("Turno", back_populates="days")

    __table_args__ = (
        UniqueConstraint("turno_id", "dia", name="uq_turno_dia"),
    )
