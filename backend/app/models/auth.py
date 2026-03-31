import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.mixins import IDMixin, TimestampMixin

class AuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"

class Role(IDMixin, TimestampMixin, Base):
    __tablename__ = "roles"
    
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    users = relationship("User", back_populates="role")
    
class User(IDMixin, TimestampMixin,Base):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    role = relationship("Role", back_populates="users")
    
    auth_provider = Column(Enum(AuthProvider, name="auth_provider_enum"), default=AuthProvider.LOCAL, nullable=False)
    hashed_password = Column(String, nullable=True) 
    google_id = Column(String, unique=True, nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_2fa_enabled = Column(Boolean, default=False)
    totp_secret = Column(String, nullable=True)

    client_profile = relationship("ClientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    employee_profile = relationship("EmployeeProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")