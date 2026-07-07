from sqlalchemy import Boolean, Column, Index, Integer, String, text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.mixins import IDMixin, TimestampMixin


class Salon(IDMixin, TimestampMixin, Base):
    __tablename__ = "salones"

    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    turnos = relationship("Turno", back_populates="salon")

    __table_args__ = (
        Index(
            "uq_salones_name_active",
            "name",
            unique=True,
            postgresql_where=text("is_active = TRUE"),
        ),
    )
