from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.ad import Ad, AdCreate, AdResponse
from core.dependencies import get_current_admin

router = APIRouter(prefix="/ads", tags=["Реклама"])

# 👑 Только админ может добавлять
@router.post("/", response_model=AdResponse)
def create_ad(
    ad: AdCreate,
    db: Session = Depends(get_db),
    current_admin_id: int = Depends(get_current_admin)
):
    new_ad = Ad(**ad.dict())
    db.add(new_ad)
    db.commit()
    db.refresh(new_ad)
    return new_ad

# 📋 Показать всем пользователям
@router.get("/", response_model=List[AdResponse])
def list_active_ads(db: Session = Depends(get_db)):
    return db.query(Ad).filter(Ad.is_active == True).order_by(Ad.created_at.desc()).all()

# 🔕 Скрыть (отключить) рекламу
@router.put("/{ad_id}/deactivate")
def deactivate_ad(
    ad_id: int,
    db: Session = Depends(get_db),
    current_admin_id: int = Depends(get_current_admin)
):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Реклама не найдена")
    ad.is_active = False
    db.commit()
    return {"message": "Реклама скрыта"}

# 🔔 Активировать снова
@router.put("/{ad_id}/activate")
def activate_ad(
    ad_id: int,
    db: Session = Depends(get_db),
    current_admin_id: int = Depends(get_current_admin)
):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Реклама не найдена")
    ad.is_active = True
    db.commit()
    return {"message": "Реклама снова активна"}

# ❌ Удалить
@router.delete("/{ad_id}")
def delete_ad(
    ad_id: int,
    db: Session = Depends(get_db),
    current_admin_id: int = Depends(get_current_admin)
):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Реклама не найдена")
    db.delete(ad)
    db.commit()
    return {"message": "Реклама удалена"}
