from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from random import randint
from db.database import get_db
from models.sms_code import SMSCode, RequestSMSCode, VerifySMSCode, ForgotPasswordRequest, ForgotPasswordConfirm
from models.user import User
from passlib.context import CryptContext
import os

router = APIRouter(prefix="/auth", tags=["Auth (SMS)"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/request-code")
async def request_code(data: RequestSMSCode, db: Session = Depends(get_db)):
    phone = data.phone_number
    existing_user = db.query(User).filter(User.phone_number == phone).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким номером уже существует")

    code = str(randint(1000, 9999))
    expires = datetime.utcnow() + timedelta(minutes=5)

    # сохраняем код в БД
    sms_entry = SMSCode(phone_number=phone, code=code, expires_at=expires)
    db.add(sms_entry)
    db.commit()

    # вместо настоящей отправки — временный вывод в консоль
    print(f"📨 SMS-код для {phone}: {code}")

    return {"message": "Код подтверждения отправлен на номер телефона"}


@router.post("/verify-code")
async def verify_code(data: VerifySMSCode, db: Session = Depends(get_db)):
    code_entry = (
        db.query(SMSCode)
        .filter(SMSCode.phone_number == data.phone_number)
        .order_by(SMSCode.created_at.desc())
        .first()
    )

    if not code_entry or code_entry.code != data.code:
        raise HTTPException(status_code=400, detail="Неверный код")

    if code_entry.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Код истёк")

    # удаляем все коды для этого номера
    db.query(SMSCode).filter(SMSCode.phone_number == data.phone_number).delete()
    db.commit()

    return {"message": "Телефон подтвержден. Теперь вы можете завершить регистрацию."}


@router.post("/forgot-password/request")
async def forgot_password_request(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == data.phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    code = str(randint(1000, 9999))
    expires = datetime.utcnow() + timedelta(minutes=5)

    sms_entry = SMSCode(phone_number=data.phone_number, code=code, expires_at=expires)
    db.add(sms_entry)
    db.commit()

    print(f"📨 Код для сброса пароля {data.phone_number}: {code}")
    return {"message": "Код отправлен на номер телефона"}

@router.post("/forgot-password/confirm")
async def forgot_password_confirm(data: ForgotPasswordConfirm, db: Session = Depends(get_db)):
    code_entry = (
        db.query(SMSCode)
        .filter(SMSCode.phone_number == data.phone_number)
        .order_by(SMSCode.created_at.desc())
        .first()
    )

    if not code_entry or code_entry.code != data.code:
        raise HTTPException(status_code=400, detail="Неверный код")

    if code_entry.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Код истёк")

    user = db.query(User).filter(User.phone_number == data.phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    hashed_password = pwd_context.hash(data.new_password)
    user.password = hashed_password

    # удаляем коды
    db.query(SMSCode).filter(SMSCode.phone_number == data.phone_number).delete()
    db.commit()

    return {"message": "Пароль успешно обновлён"}