from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from db.database import get_db
from models.payment import Payment, PaymentCreate, PaymentResponse
from models.user import User
from models.notification import Notification
from core.dependencies import get_current_user

router = APIRouter(prefix="/payments", tags=["Платежи"])

# Доступные платные пакеты
PACKAGES = {
    3: {"amount": 1800, "name": "Поднять в топ 3 раза/день"},
    5: {"amount": 3250, "name": "Поднять в топ 5 раз/день"},
    7: {"amount": 4890, "name": "Поднять в топ 7 раз/день"},
}

# ✅ Запрос на покупку платного пакета (мок-оплата)
@router.post("/promote")
def promote_master(
    times_per_day: int,
    bank: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type != "master":
        raise HTTPException(status_code=403, detail="Только мастера могут покупать продвижение")

    if times_per_day not in PACKAGES:
        raise HTTPException(status_code=400, detail="Доступны только пакеты: 3, 5, 7 раз в день")

    if bank not in ["Kaspi", "Halyk", "Forte"]:
        raise HTTPException(status_code=400, detail="Банк должен быть: Kaspi, Halyk или Forte")

    # Проверка активного продвижения
    active_payment = db.query(Payment).filter(
        Payment.user_id == current_user.id,
        Payment.purpose == "promote",
        Payment.is_active == True,
        Payment.end_date >= datetime.utcnow()
    ).first()

    if active_payment:
        raise HTTPException(status_code=400, detail="У вас уже есть активное продвижение")

    # Создание платежа
    package = PACKAGES[times_per_day]
    payment = Payment(
        user_id=current_user.id,
        package_name=package["name"],
        times_per_day=times_per_day,
        duration_days=30,
        amount=package["amount"],
        purpose="promote",
        bank=bank,
        status="pending",
        is_active=False
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "payment_id": payment.id,
        "amount": payment.amount,
        "bank": bank,
        "message": f"Создан платёж. Подтвердите оплату через /payments/confirm/{payment.id}"
    }

# ✅ Подтверждение успешной оплаты (мастер вручную нажимает)
@router.post("/confirm/{payment_id}")
def confirm_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user.id
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")

    if payment.status == "paid":
        return {"message": "Платёж уже подтвержден"}

    # Подтверждение
    now = datetime.utcnow()
    payment.status = "paid"
    payment.start_date = now
    payment.end_date = now + timedelta(days=30)
    payment.is_active = True

    # Обновление профиля мастера
    current_user.is_promoted = True
    current_user.promotion_expiration = payment.end_date
    current_user.promote_times_per_day = payment.times_per_day
    current_user.promote_today_used = 0

    # Уведомление
    db.add(Notification(
        user_id=current_user.id,
        message="🎯 Оплата подтверждена! Ваш профиль продвигается в ТОП"
    ))

    db.commit()
    return {"message": "Платёж успешно подтверждён и продвижение активировано"}

# ✅ Оплата за дополнительную заявку (после 5 в день)
@router.post("/extra-request")
def pay_for_extra_request(
    bank: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type != "client":
        raise HTTPException(status_code=403, detail="Только клиент может оплатить заявку")

    if bank not in ["Kaspi", "Halyk", "Forte"]:
        raise HTTPException(status_code=400, detail="Банк должен быть: Kaspi, Halyk или Forte")

    # Платёж
    payment = Payment(
        user_id=current_user.id,
        amount=350,
        purpose="extra_request",
        bank=bank,
        status="paid",
        is_active=True,
        start_date=datetime.utcnow()
    )
    db.add(payment)
    db.commit()

    return {"message": "Оплата за заявку прошла успешно"}

# ✅ (опционально) ручное создание (например, при тестировании)
@router.post("/create", response_model=PaymentResponse)
def create_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type != "master":
        raise HTTPException(status_code=403, detail="Только мастер может покупать продвижение")

    payment = Payment(
        user_id=current_user.id,
        package_name=data.package_type,
        times_per_day=int(data.package_type),
        duration_days=30,
        amount=data.amount,
        purpose="promote",
        bank=data.bank,
        status="paid",
        is_active=True,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30)
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment
