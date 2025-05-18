from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from passlib.hash import bcrypt
from datetime import timedelta, datetime
from db.database import get_db
from core.dependencies import create_access_token, get_current_user
from models.user import User, UserRegistration, UserLogin, ClientProfileUpdate, MasterProfileUpdate, UserResponse
from models.sms_code import SMSCode
from models.payment import Payment
from typing import List, Optional
from sqlalchemy import and_
from services.moderation import contains_bad_words
from core.rate_limiter import limiter


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

ACCESS_TOKEN_EXPIRE_MINUTES = 30


@router.post("/register")
@limiter.limit("3/minute")  # 👈 максимум 3 регистрации в минуту с одного IP
async def register_user(user: UserRegistration, request: Request, db: Session = Depends(get_db)):
    # Проверка: не зарегистрировано ли уже устройство
    existing_device = db.query(User).filter(User.device_id == user.device_id).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="С этого устройства уже зарегистрирован аккаунт")

    if not user.agreed_to_terms:
        raise HTTPException(status_code=400, detail="Вы должны принять условия использования")
    
    # проверка подтверждения телефона
    verified = (
        db.query(SMSCode)
        .filter(SMSCode.phone_number == user.phone_number)
        .order_by(SMSCode.created_at.desc())
        .first()
    )

    if not verified:
        raise HTTPException(status_code=400, detail="Номер не подтвержден через SMS")

    existing_user = db.query(User).filter(User.phone_number == user.phone_number).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Номер уже зарегистрирован")

    hashed_password = bcrypt.hash(user.password)
    new_user = User(
        phone_number=user.phone_number,
        password=hashed_password,
        user_type=user.user_type,
        full_name=user.phone_number if user.user_type == "master" else None,
        is_verified=True,
        device_id=user.device_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "phone_number": new_user.phone_number,
        "user_type": new_user.user_type,
        "registration_date": new_user.registration_date,
        "message": "Регистрация прошла успешно"
    }


@router.post("/login")
@limiter.limit("5/minute")
async def login_user(user: UserLogin, request: Request, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.phone_number == user.phone_number).first()
    if not db_user or not bcrypt.verify(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Неверный номер телефона или пароль")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(db_user.id)}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/protected")
async def protected(current_user: User = Depends(get_current_user)):
    return {"message": f"Это защищенный эндпоинт. Пользователь: {current_user.phone_number}"}


@router.put("/masters/me")
async def update_master_profile(
    profile_data: MasterProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != "master":
        raise HTTPException(status_code=403, detail="Требуются права мастера")

    # Проверка на мат
    for field, value in profile_data.dict(exclude_unset=True).items():
        if isinstance(value, str) and contains_bad_words(value):
            raise HTTPException(status_code=400, detail=f"Поле '{field}' содержит запрещённые слова")
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/clients/me")
async def update_client_profile(
    profile_data: ClientProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != "client":
        raise HTTPException(status_code=403, detail="Требуются права клиента")

    for field, value in profile_data.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user

from sqlalchemy.orm import joinedload
from sqlalchemy import and_

@router.get("/top", response_model=List[UserResponse])
def get_top_masters(
    city: Optional[str] = Query(None, description="Фильтр по городу"),
    category_id: Optional[int] = Query(None, description="Фильтр по категории"),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()

    # 1. Деактивируем просроченные оплаты
    expired = db.query(Payment).filter(
        Payment.purpose == "promote",
        Payment.is_active == True,
        Payment.end_date < now
    ).all()
    for payment in expired:
        payment.is_active = False
    db.commit()

    # 2. Загружаем мастеров
    query = db.query(User).filter(User.user_type == "master", User.is_verified == True)

    if city:
        query = query.filter(User.city == city)
    if category_id:
        query = query.filter(User.category_id == category_id)

    masters = query.options(joinedload(User.payments)).all()

    # 3. Делим на продвигаемых и обычных
    promoted = []
    regular = []

    for user in masters:
        active_payment = any(
            p.purpose == "promote" and p.is_active and p.start_date <= now <= p.end_date
            for p in user.payments
        )
        if active_payment:
            promoted.append(user)
        else:
            regular.append(user)

    # 4. Сортировка: сначала продвигаемые по очереди, потом обычные по репутации
    promoted.sort(key=lambda u: u.last_promoted_at or datetime.min)
    regular.sort(key=lambda u: u.reputation or 0, reverse=True)

    # 5. Обновим last_promoted_at у первого рекламного мастера
    if promoted:
        promoted[0].last_promoted_at = now
        db.commit()

    return promoted + regular



