from sqlalchemy import Boolean, Column, Index, String, text
from sqlalchemy.orm import declared_attr

from app.core.database import Base
from app.models.mixins import IDMixin, TimestampMixin


class Activity(IDMixin, TimestampMixin, Base):
    __tablename__ = "activities"

    name = Column(String, nullable=False)
    instructor = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index(
            "uq_activities_name_active",
            "name",
            unique=True,
            postgresql_where=text("is_active = TRUE"),
        ),
    )
