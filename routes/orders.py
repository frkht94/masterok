from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from db.database import get_db
from core.dependencies import get_current_user
from models.order import Order, OrderCreate, OrderForMaster, ClientOrderResponse
from models.user import User
from models.notification import Notification

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

# ────────────────────── СОЗДАНИЕ ЗАКАЗА ──────────────────────
@router.post("")
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != "client":
        raise HTTPException(status_code=403, detail="Требуются права клиента")

    new_order = Order(
        client_id=current_user.id,
        category_id=order_data.category_id,
        description=order_data.description,
        city=order_data.city,
        address=order_data.address,
        latitude=order_data.latitude,
        longitude=order_data.longitude,
        order_date=order_data.order_date,
        status="pending"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order


# ────────────────────── ПОЛУЧЕНИЕ ЗАКАЗОВ МАСТЕРОМ ──────────────────────
@router.get("/new", response_model=List[OrderForMaster])
async def get_new_orders_for_master(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != "master":
        raise HTTPException(status_code=403, detail="Требуются права мастера")

    if not current_user.category_id or not current_user.city:
        return []

    orders = db.query(Order).filter(
        Order.status == "pending",
        Order.category_id == current_user.category_id,
        Order.city == current_user.city
    ).all()

    return orders


@router.get("/masters/me/orders/in_progress", response_model=List[OrderForMaster])
async def get_in_progress_orders_for_master(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != "master":
        raise HTTPException(status_code=403, detail="Требуются права мастера")

    return db.query(Order).filter(
        Order.status == "in_progress",
        Order.master_id == current_user.id
    ).all()


# ────────────────────── ВЗЯТЬ ЗАКАЗ ──────────────────────
@router.post("/{order_id}/take")
async def take_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != "master":
        raise HTTPException(status_code=403, detail="Требуются права мастера")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Заказ уже в работе или завершён")

    order.status = "in_progress"
    order.master_id = current_user.id
    db.commit()
    return {"message": "Заказ успешно взят в работу"}


# ────────────────────── ЗАВЕРШИТЬ ЗАКАЗ ──────────────────────
@router.post("/{order_id}/complete")
async def complete_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != "master":
        raise HTTPException(status_code=403, detail="Требуются права мастера")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if order.status != "in_progress":
        raise HTTPException(status_code=400, detail="Заказ не в статусе 'in_progress'")
    if order.master_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не назначены на этот заказ")

    order.status = "completed"
    order.completed_at = datetime.utcnow()
    db.commit()
    return {"message": "Заказ завершён"}


# ────────────────────── ОТМЕНИТЬ ЗАКАЗ ──────────────────────
@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != "client":
        raise HTTPException(status_code=403, detail="Требуются права клиента")

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.client_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Отменить можно только заказ в ожидании")

    order.status = "cancelled"
    order.cancelled_at = datetime.utcnow()
    db.commit()
    return {"message": "Заказ отменён"}


# ────────────────────── ЗАКАЗЫ КЛИЕНТА ──────────────────────
@router.get("/clients/me/orders", response_model=List[ClientOrderResponse])
async def get_client_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != "client":
        raise HTTPException(status_code=403, detail="Требуются права клиента")

    return db.query(Order).filter(Order.client_id == current_user.id).all()


# ────────────────────── ПОДРОБНОСТИ ЗАКАЗА ──────────────────────
@router.get("/{order_id}", response_model=OrderForMaster)
async def get_order_details_for_master(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != "master":
        raise HTTPException(status_code=403, detail="Требуются права мастера")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if order.master_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не имеете доступ к этому заказу")

    return order

@router.put("/{order_id}/complete")
def complete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if order.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не можете завершить этот заказ")

    if order.status == "completed":
        raise HTTPException(status_code=400, detail="Заказ уже завершён")

    order.status = "completed"
    notification = Notification(
        user_id=order.master_id,
        message=f"Клиент завершил заказ №{order.id}"
    )
    db.add(notification)

    db.commit()
    db.refresh(order)

    return {"message": "Заказ завершён, теперь вы можете оставить отзыв"}
