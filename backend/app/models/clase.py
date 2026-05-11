from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.mixins import IDMixin, TimestampMixin


class Clase(IDMixin, TimestampMixin, Base):
    __tablename__ = "clases"

    turno_id = Column(Integer, ForeignKey("turnos.id"), nullable=False)
    date = Column(Date, nullable=False)
    capacity = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    turno = relationship("Turno", back_populates="clases")
