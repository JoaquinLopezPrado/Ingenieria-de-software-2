from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func

class IDMixin:
    """Provee la columna ID estándar para todas las tablas."""
    id = Column(Integer, primary_key=True, index=True)

class TimestampMixin:
    """Provee columnas de auditoría que se completan solas."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)