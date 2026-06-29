from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=True) 
    hashed_password = Column(String, nullable=False)
    hashed_duress_pin = Column(String, nullable=True) 
    reputation_score = Column(Float, default=1.0) 
    is_active = Column(Boolean, default=True)
    
    is_ngo = Column(Boolean, default=False, index=True)

    reported_incidents = relationship("Incident", back_populates="reporter")