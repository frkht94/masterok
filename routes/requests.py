from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from db.database import get_db
from models.request import ClientRequest, RequestResponse
from core.dependencies import get_current_user
from models.user import User
from models.notification import Notification
from datetime import datetime
import shutil
import uuid
import os
from sqlalchemy import and_
from dateutil import parser
import asyncio

from services.push import send_push_notification
from services.moderation import contains_bad_words
from services.image_moderation import is_inappropriate_image_by_url

router = APIRouter(prefix="/requests", tags=["Заявки"])

MEDIA_DIR = "media"
os.makedirs(MEDIA_DIR, exist_ok=True)

def get_image_url_local(filename: str) -> str:
    # Пример — на проде ты можешь вернуть полный URL вида: https://mydomain.kz/media/filename
    return f"http://localhost:8000/media/{filename}"


@router.post("/create", response_model=RequestResponse)
async def create_request(
    category_id: int = Form(...),
    city: str = Form(...),
    address: str = Form(...),
    scheduled_date: str = Form(...),
    description: str = Form(..., min_length=20),
    phone_number: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 🛡 Модерация текста
    if contains_bad_words(description):
        raise HTTPException(status_code=400, detail="Описание содержит запрещённые слова")

    # 📅 Парсим дату
    try:
        scheduled_dt = parser.isoparse(scheduled_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты")

    # 🖼 Работа с изображением
    filename = None
    if file:
        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(MEDIA_DIR, filename)

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file.file.close()

        image_url = get_image_url_local(filename)
        if is_inappropriate_image_by_url(image_url):
            os.remove(filepath)
            raise HTTPException(status_code=400, detail="Фото нарушает правила сообщества")

    # 📊 Проверка лимита заявок
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    requests_today = db.query(ClientRequest).filter(
        and_(
            ClientRequest.client_id == current_user.id,
            ClientRequest.created_at >= today_start
        )
    ).count()

    if requests_today >= 5:
        raise HTTPException(
            status_code=402,
            detail="⚠️ Вы достигли лимита бесплатных заявок (5 в день). Следующая заявка — платная: 350₸"
        )

    # ✅ Сохраняем в базу
    request = ClientRequest(
        client_id=current_user.id,
        category_id=category_id,
        city=city,
        address=address,
        scheduled_date=scheduled_dt,
        description=description,
        photo_url=f"/media/{filename}" if filename else None,
        phone_number=phone_number
    )

    db.add(request)

    # 🔔 Уведомляем подходящих мастеров
    matching_masters = db.query(User).filter(
        User.user_type == "master",
        User.city == city,
        User.category_id == category_id,
        User.is_verified == True
    ).all()

    for master in matching_masters:
        db.add(Notification(
            user_id=master.id,
            message=f"📥 Новая заявка: {description[:30]}... ({city})"
        ))
        if master.device_token:
            await asyncio.sleep(0)  # Предотвращаем блокировку event loop
            await send_push_notification(
                master.device_token,
                "Новая заявка",
                f"{description[:30]}... ({city})"
            )

    db.commit()
    db.refresh(request)

    return request


@router.get("/", response_model=List[RequestResponse])
def list_requests(
    db: Session = Depends(get_db),
    category_id: Optional[int] = None,
    city: Optional[str] = None
):
    query = db.query(ClientRequest)
    if category_id:
        query = query.filter(ClientRequest.category_id == category_id)
    if city:
        query = query.filter(ClientRequest.city.ilike(f"%{city}%"))
    return query.order_by(ClientRequest.created_at.desc()).all()
