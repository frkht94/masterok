from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models.work_photo import WorkPhoto, PhotoResponse
from models.user import User
from core.dependencies import get_current_user
import shutil
import uuid
import os
from typing import List


router = APIRouter(prefix="/photos", tags=["Работы"])

@router.post("/upload", response_model=PhotoResponse)
async def upload_work_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith((".jpg", ".jpeg", ".png")):
        raise HTTPException(status_code=400, detail="Только jpg и png разрешены")

    filename = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    file_path = f"media/{filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    photo = WorkPhoto(user_id=current_user.id, image_path=f"/media/{filename}")
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return photo

# 📂 1. Получить все фото текущего мастера
@router.get("/my", response_model=List[PhotoResponse])
async def get_my_photos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    photos = db.query(WorkPhoto).filter(WorkPhoto.user_id == current_user.id).all()
    return photos


# ❌ 2. Удалить фото по ID
@router.delete("/{photo_id}")
async def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    photo = db.query(WorkPhoto).filter(
        WorkPhoto.id == photo_id,
        WorkPhoto.user_id == current_user.id
    ).first()

    if not photo:
        raise HTTPException(status_code=404, detail="Фото не найдено или не ваше")

    # удаляем сам файл
    file_path = photo.image_path.lstrip("/")  # убираем /media/
    if os.path.exists(file_path):
        os.remove(file_path)

    # удаляем из БД
    db.delete(photo)
    db.commit()

    return {"message": "Фото удалено"}