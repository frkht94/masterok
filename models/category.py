from sqlalchemy import Column, Integer, String
from db.database import Base
from pydantic import BaseModel


# SQLAlchemy модель для таблицы categories
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


# Pydantic-схемы
class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    name: str


class CategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
