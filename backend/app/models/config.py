from sqlalchemy import Column, String

from app.core.database import Base


class AppConfig(Base):
    __tablename__ = "app_config"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
