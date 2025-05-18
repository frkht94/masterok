from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.faq import FAQ, FAQCreate, FAQUpdate, FAQResponse
from core.dependencies import get_current_admin

router = APIRouter(prefix="/faqs", tags=["FAQ"])

# 📩 Для клиентов — список FAQ
@router.get("/", response_model=List[FAQResponse])
def get_faqs(db: Session = Depends(get_db)):
    return db.query(FAQ).order_by(FAQ.created_at.desc()).all()

# 👑 Добавить (только админ)
@router.post("/", response_model=FAQResponse)
def create_faq(
    faq: FAQCreate,
    db: Session = Depends(get_db),
    current_admin_id: int = Depends(get_current_admin)
):
    new_faq = FAQ(**faq.dict())
    db.add(new_faq)
    db.commit()
    db.refresh(new_faq)
    return new_faq

# ✏️ Обновить (только админ)
@router.put("/{faq_id}", response_model=FAQResponse)
def update_faq(
    faq_id: int,
    data: FAQUpdate,
    db: Session = Depends(get_db),
    current_admin_id: int = Depends(get_current_admin)
):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    faq.question = data.question
    faq.answer = data.answer
    db.commit()
    db.refresh(faq)
    return faq

# ❌ Удалить (только админ)
@router.delete("/{faq_id}")
def delete_faq(
    faq_id: int,
    db: Session = Depends(get_db),
    current_admin_id: int = Depends(get_current_admin)
):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    db.delete(faq)
    db.commit()
    return {"message": "Вопрос удалён"}
