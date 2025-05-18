from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from db.database import Base
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy.orm import relationship
from typing import Optional


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Назначение платежа: promote или extra_request
    purpose = Column(String, nullable=False, default="promote")

    # Название пакета (если есть)
    package_name = Column(String, nullable=True)

    # Кол-во подъемов в день: 3, 5, 7 (только для promote)
    times_per_day = Column(Integer, nullable=True)

    # Продолжительность в днях (по умолчанию 30)
    duration_days = Column(Integer, default=30)

    # Сумма оплаты
    amount = Column(Float, nullable=False)

    # Банк: kaspi, halyk, forte
    bank = Column(String, nullable=False)

    # Статус оплаты
    status = Column(String, default="pending")  # pending / paid / failed

    # Даты начала и окончания
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)

    # Активен ли пакет
    is_active = Column(Boolean, default=False)

    # Связь с пользователем
    user = relationship("User", back_populates="payments")


# 📦 Pydantic модель для создания платежа
class PaymentCreate(BaseModel):
    amount: int = Field(..., gt=0)
    package_type: str  # "3", "5", "7"
    bank: str  # Kaspi, Halyk, Forte


# 📄 Ответ клиенту
class PaymentResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    package_name: Optional[str] = None
    purpose: str
    bank: str
    status: str
    is_active: bool
    start_date: datetime
    end_date: Optional[datetime] = None

    class Config:
        from_attributes = True
