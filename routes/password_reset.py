# routes/password_reset.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from models.sms_code import SMSCode
from models.user import User
from passlib.hash import bcrypt
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/password-reset", tags=["Восстановление пароля"])


@router.post("/send-code")
def send_reset_code(phone_number: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    code = str(random.randint(1000, 9999))
    sms = SMSCode(phone_number=phone_number, code=code)
    db.add(sms)
    db.commit()

    # Здесь должна быть отправка SMS (реально или имитация)
    print(f"Reset code: {code}")  # временно печатаем в консоль

    return {"message": "Код для сброса пароля отправлен"}


@router.post("/verify-code")
def verify_code(phone_number: str, code: str, db: Session = Depends(get_db)):
    record = (
        db.query(SMSCode)
        .filter(SMSCode.phone_number == phone_number)
        .order_by(SMSCode.created_at.desc())
        .first()
    )

    if not record or record.code != code or (datetime.utcnow() - record.created_at) > timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="Неверный или просроченный код")

    return {"message": "Код подтвержден"}


@router.post("/set-new-password")
def set_new_password(phone_number: str, code: str, new_password: str, db: Session = Depends(get_db)):
    record = (
        db.query(SMSCode)
        .filter(SMSCode.phone_number == phone_number)
        .order_by(SMSCode.created_at.desc())
        .first()
    )

    if not record or record.code != code or (datetime.utcnow() - record.created_at) > timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="Неверный или просроченный код")

    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user.password = bcrypt.hash(new_password)
    db.commit()

    return {"message": "Пароль успешно изменен"}
