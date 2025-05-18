from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from core.dependencies import get_current_admin
from models.category import Category, CategoryCreate, CategoryResponse

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

# Получение всех категорий
@router.get("", response_model=list[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()



# Создание новой категории
@router.post("", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    current_admin_id: int = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(Category).filter(Category.name == category_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Категория с таким названием уже существует")

    new_category = Category(name=category_data.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category
