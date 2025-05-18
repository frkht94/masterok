from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# SQLAlchemy модель заявки
class ClientRequest(Base):
    __tablename__ = "client_requests"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    city = Column(String, nullable=False)
    address = Column(String, nullable=True)
    scheduled_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    photo_url = Column(String, nullable=True)
    phone_number = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    is_paid = Column(Boolean, default=False)  # 🆕 платная или нет
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)  # 🆕 связка

    client = relationship("User", backref="client_requests")
    payment = relationship("Payment", backref="client_request", lazy="joined")


# Pydantic модель создания заявки
class RequestCreate(BaseModel):
    category_id: int
    city: str
    address: Optional[str]
    scheduled_date: datetime
    description: str = Field(..., min_length=20)
    photo_url: Optional[str]
    phone_number: str


# Pydantic модель ответа
class RequestResponse(BaseModel):
    id: int
    category_id: int
    city: str
    address: Optional[str]
    scheduled_date: datetime
    description: str
    photo_url: Optional[str]
    phone_number: str
    created_at: datetime

    class Config:
        from_attributes = True
