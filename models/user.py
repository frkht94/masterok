from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# SQLAlchemy модель для таблицы users
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    user_type = Column(String, nullable=False)  # 'master', 'client', 'admin'
    is_verified = Column(Boolean, default=False)

    full_name = Column(String, nullable=True)
    about_me = Column(Text, nullable=True)
    photo_url = Column(String, nullable=True)

    category_id = Column(Integer, nullable=True)
    city = Column(String, nullable=True)

    reputation = Column(Float, default=0)
    registration_date = Column(DateTime(timezone=True), server_default=func.now())
    device_token = Column(String, nullable=True)

    # 🔐 Новое поле для ограничения по устройству
    device_id = Column(String, unique=True, nullable=True)

    # 👇 Продвижение
    is_promoted = Column(Boolean, default=False)
    promote_times_per_day = Column(Integer, nullable=True)
    promote_today_used = Column(Integer, default=0)
    last_promoted_at = Column(DateTime, nullable=True)
    promotion_expiration = Column(DateTime, nullable=True)

    # 💳 Связь с платежами
    payments = relationship("Payment", back_populates="user")


# -------------------- Pydantic схемы --------------------

class UserRegistration(BaseModel):
    phone_number: str
    password: str
    user_type: str
    device_id: str
    agreed_to_terms: bool


class UserLogin(BaseModel):
    phone_number: str
    password: str


class ClientProfileUpdate(BaseModel):
    full_name: Optional[str] = None


class MasterProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    about_me: Optional[str] = None
    photo_url: Optional[str] = None
    category_id: Optional[int] = None
    city: Optional[str] = None


class UserAdminResponse(BaseModel):
    id: int
    phone_number: str
    user_type: str
    registration_date: datetime

    class Config:
        from_attributes = True


class UserDetailAdminResponse(BaseModel):
    id: int
    phone_number: str
    user_type: str
    registration_date: datetime
    full_name: Optional[str] = None
    about_me: Optional[str] = None
    photo_url: Optional[str] = None
    category_id: Optional[int] = None
    city: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    phone_number: str
    user_type: str
    full_name: Optional[str] = None
    about_me: Optional[str] = None
    photo_url: Optional[str] = None
    category_id: Optional[int] = None
    city: Optional[str] = None
    is_verified: bool
    reputation: float
    registration_date: datetime
    device_token: Optional[str]

    class Config:
        from_attributes = True
