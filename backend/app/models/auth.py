from sqlalchemy import Column, DateTime, Integer, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.mixins import IDMixin, TimestampMixin
from app.domain.user import AuthProvider

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
    token_version = Column(Integer, default=0, nullable=False)

    client_profile = relationship("ClientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    employee_profile = relationship("EmployeeProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class RefreshToken(IDMixin, TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class PasswordResetToken(IDMixin, TimestampMixin, Base):
    __tablename__ = "password_reset_tokens"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)