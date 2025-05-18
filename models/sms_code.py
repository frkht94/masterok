# sms_code.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from db.database import Base
from pydantic import BaseModel
from datetime import datetime

class SMSCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, nullable=False)
    code = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)


class RequestSMSCode(BaseModel):
    phone_number: str


class VerifySMSCode(BaseModel):
    phone_number: str
    code: str

class ForgotPasswordRequest(BaseModel):
    phone_number: str


class ForgotPasswordConfirm(BaseModel):
    phone_number: str
    code: str
    new_password: str
