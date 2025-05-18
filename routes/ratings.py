from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func

from db.database import get_db
from core.dependencies import get_current_user
from models.rating import Rating, RatingCreate, RatingResponse
from models.order import Order
from models.user import User
from services.moderation import contains_bad_words  # 👈 импорт фильтра

router = APIRouter(prefix="/ratings", tags=["Отзывы"])


@router.post("/create", response_model=RatingResponse)
def create_rating(
    data: RatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Проверка существования заказа
    order = db.query(Order).filter(Order.id == data.order_id).first()

    if not order or order.status != "completed":
        raise HTTPException(status_code=400, detail="Заказ не завершён или не найден")

    if order.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Это не ваш заказ")

    # Проверка наличия уже оставленного отзыва
    existing = db.query(Rating).filter(Rating.order_id == data.order_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Отзыв уже существует")

    # Модерация текста отзыва
    if data.review_text and contains_bad_words(data.review_text):
        raise HTTPException(status_code=400, detail="Комментарий содержит запрещённые слова")

    # Создание нового отзыва
    rating = Rating(
        order_id=data.order_id,
        client_id=current_user.id,
        master_id=order.master_id,
        rating=data.rating,
        review_text=data.review_text
    )

    db.add(rating)
    db.commit()

    # Пересчёт среднего рейтинга мастера
    avg_rating = db.query(func.avg(Rating.rating)) \
        .filter(Rating.master_id == order.master_id) \
        .scalar()

    master = db.query(User).filter(User.id == order.master_id).first()
    master.reputation = avg_rating
    db.commit()
    db.refresh(rating)

    return rating


@router.get("/by-master/{master_id}", response_model=List[RatingResponse])
def get_ratings_by_master(master_id: int, db: Session = Depends(get_db)):
    ratings = db.query(Rating).filter(Rating.master_id == master_id).all()
    return ratings


@router.delete("/{rating_id}")
def delete_rating(
    rating_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rating = db.query(Rating).filter(
        Rating.id == rating_id,
        Rating.client_id == current_user.id
    ).first()

    if not rating:
        raise HTTPException(status_code=404, detail="Отзыв не найден")

    db.delete(rating)
    db.commit()
    return {"message": "Отзыв удалён"}
