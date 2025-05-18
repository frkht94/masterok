from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import enum

class OrderStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


# SQLAlchemy модель
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    master_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    description = Column(Text, nullable=False)
    city = Column(String, nullable=False)
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    order_date = Column(DateTime, nullable=True)
    status = Column(String, default="new")  # new, in_progress, completed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)

    client = relationship("User", foreign_keys=[client_id])
    master = relationship("User", foreign_keys=[master_id])
    category = relationship("Category")


# Pydantic-схемы
class OrderCreate(BaseModel):
    category_id: int
    description: str
    city: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    order_date: Optional[datetime] = None


class OrderForMaster(BaseModel):
    id: int
    category_id: int
    description: str
    city: str
    address: str
    latitude: Optional[float]
    longitude: Optional[float]
    order_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ClientOrderResponse(BaseModel):
    id: int
    category_id: int
    description: str
    city: str
    address: Optional[str]
    order_date: Optional[datetime]
    status: str
    created_at: datetime
    master_id: Optional[int]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderAdminResponse(BaseModel):
    id: int
    client_id: int
    category_id: int
    description: str
    city: str
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    order_date: Optional[datetime]
    status: str
    created_at: datetime
    master_id: Optional[int]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]

    class Config:
        from_attributes = True
