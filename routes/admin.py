from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from typing import List
from sqlalchemy.orm import Session
from db.database import get_db
from core.dependencies import get_current_admin
from models.user import User, UserAdminResponse, UserDetailAdminResponse
from models.order import Order, OrderAdminResponse
from models.category import Category, CategoryResponse, CategoryUpdate
from models.rating import Rating, AllRatingResponse
from models.payment import Payment
from models.request import ClientRequest
from models.ad import Ad
from fastapi.responses import StreamingResponse
from io import BytesIO
from services.pdf_report import generate_pdf_report




router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

# ---------- Пользователи ----------
@router.get("/users", response_model=List[UserAdminResponse])
async def get_all_users(
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).all()
    return [UserAdminResponse.from_orm(user) for user in users]


@router.get("/users/{user_id}", response_model=UserDetailAdminResponse)
async def get_user_details(
    user_id: int,
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserDetailAdminResponse.from_orm(user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.delete(user)
    db.commit()
    return {"message": f"Пользователь с ID {user_id} успешно удалён"}


@router.put("/users/{user_id}/block")
async def block_user(
    user_id: int,
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.is_verified = False
    db.commit()
    return {"message": f"Пользователь с ID {user_id} заблокирован"}


@router.put("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.is_verified = True
    db.commit()
    return {"message": f"Пользователь с ID {user_id} разблокирован"}

# ---------- Заказы ----------
@router.get("/orders", response_model=List[OrderAdminResponse])
async def get_all_orders(
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    orders = db.query(Order).all()
    return [OrderAdminResponse.from_orm(order) for order in orders]


@router.delete("/orders/{order_id}")
async def delete_order_admin(
    order_id: int,
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    db.delete(order)
    db.commit()
    return {"message": f"Заказ с ID {order_id} успешно удалён"}

# ---------- Категории ----------
@router.get("/categories", response_model=List[CategoryResponse])
async def get_all_categories_admin(
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return db.query(Category).all()


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    category.name = category_update.name
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    db.delete(category)
    db.commit()
    return {"message": f"Категория с ID {category_id} успешно удалена"}

# ---------- Отзывы ----------
@router.get("/ratings", response_model=List[AllRatingResponse])
async def get_all_ratings_admin(
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    ratings = db.query(Rating).all()
    return [AllRatingResponse.from_orm(r) for r in ratings]


@router.delete("/ratings/{rating_id}")
async def delete_rating_admin(
    rating_id: int,
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    rating = db.query(Rating).filter(Rating.id == rating_id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    db.delete(rating)
    db.commit()
    return {"message": f"Отзыв с ID {rating_id} успешно удалён"}


@router.get("/reports/payments/pdf")
def export_payments_pdf(
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    payments = db.query(Payment).all()
    columns = ["ID", "Пользователь", "Сумма", "Тип", "Банк", "Статус"]
    rows = [
        [p.id, p.user_id, p.amount, p.purpose, p.bank, p.status]
        for p in payments
    ]
    pdf_bytes = generate_pdf_report("Отчёт по платежам", columns, rows)
    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": "inline; filename=payments.pdf"})


@router.get("/reports/orders/pdf")
def export_orders_pdf(
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    from models.order import Order
    orders = db.query(Order).all()
    columns = ["ID", "Клиент", "Мастер", "Категория", "Статус"]
    rows = [
        [o.id, o.client_id, o.master_id, o.category_id, o.status]
        for o in orders
    ]
    pdf_bytes = generate_pdf_report("Отчёт по заказам", columns, rows)
    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": "inline; filename=orders.pdf"})


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    current_admin_id: int = Depends(get_current_admin)
):
    total_users = db.query(User).count()
    total_masters = db.query(User).filter(User.user_type == "master").count()
    total_clients = db.query(User).filter(User.user_type == "client").count()

    total_orders = db.query(Order).count()
    total_requests = db.query(ClientRequest).count()
    total_ads = db.query(Ad).count()

    total_payments_sum = db.query(func.sum(Payment.amount)).filter(Payment.status == "paid").scalar() or 0
    active_promotions = db.query(Payment).filter(Payment.purpose == "promote", Payment.is_active == True).count()

    return {
        "users_total": total_users,
        "masters_total": total_masters,
        "clients_total": total_clients,
        "orders_total": total_orders,
        "requests_total": total_requests,
        "ads_total": total_ads,
        "payments_total_sum": total_payments_sum,
        "active_promotions": active_promotions
    }