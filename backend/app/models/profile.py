from sqlalchemy import Column, Integer, String, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.mixins import IDMixin, TimestampMixin
from app.domain.profile import Gender

class DocumentType(IDMixin, TimestampMixin, Base):
    __tablename__ = "document_types"
    
    name = Column(String, unique=True, index=True, nullable=False) 
    
    client_profiles = relationship("ClientProfile", back_populates="document_type")

class ClientProfile(IDMixin, TimestampMixin, Base):
    __tablename__ = "client_profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    
    doc_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False)
    document_type = relationship("DocumentType", back_populates="client_profiles")
    doc_number = Column(String, unique=True, index=True, nullable=False)

    gender = Column(Enum(Gender, name="gender_enum", values_callable=lambda x: [e.value for e in x]), nullable=False)

    user = relationship("User", back_populates="client_profile")

class EmployeeProfile(IDMixin, TimestampMixin, Base):
    __tablename__ = "employee_profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    internal_file_number = Column(String, unique=True, nullable=True) 

    user = relationship("User", back_populates="employee_profile")