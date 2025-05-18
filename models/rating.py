from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# SQLAlchemy модель
class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    master_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order")
    client = relationship("User", foreign_keys=[client_id])
    master = relationship("User", foreign_keys=[master_id])


# Pydantic схемы
class RatingCreate(BaseModel):
    order_id: int
    rating: int
    review_text: Optional[str] = None


class RatingResponse(BaseModel):
    id: int
    order_id: int
    client_id: int
    master_id: int
    rating: int
    review_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AverageRatingResponse(BaseModel):
    master_id: int
    average_rating: Optional[float] = None


class ClientRatingResponse(BaseModel):
    id: int
    master_id: int
    rating: int
    review_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AllRatingResponse(BaseModel):
    id: int
    order_id: int
    client_id: int
    master_id: int
    rating: int
    review_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
