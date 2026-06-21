from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.mixins import IDMixin


class ClassCredit(IDMixin, Base):
    __tablename__ = "class_credits"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    turno_id = Column(Integer, ForeignKey("turnos.id"), nullable=False)
    source_clase_id = Column(Integer, ForeignKey("clases.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    used_for_clase_id = Column(Integer, ForeignKey("clases.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    turno = relationship("Turno")
    source_clase = relationship("Clase", foreign_keys=[source_clase_id])
    used_for_clase = relationship("Clase", foreign_keys=[used_for_clase_id])
