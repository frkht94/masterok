from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from db.database import Base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatMessageCreate(BaseModel):
    order_id: int
    message: str


class ChatMessageResponse(BaseModel):
    id: int
    sender_id: int
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}

