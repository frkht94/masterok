from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from db.database import Base
from pydantic import BaseModel
from datetime import datetime


class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)          # Название рекламы
    image_url = Column(String, nullable=True)       # Картинка
    link = Column(String, nullable=True)            # Куда ведёт
    company_name = Column(String, nullable=True)    # Название рекламодателя
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AdCreate(BaseModel):
    title: str
    image_url: str
    link: str
    company_name: str


class AdResponse(BaseModel):
    id: int
    title: str
    image_url: str
    link: str
    company_name: str
    created_at: datetime

    class Config:
        from_attributes = True
