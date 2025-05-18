from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from db.database import Base
from pydantic import BaseModel

class WorkPhoto(Base):
    __tablename__ = "work_photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    image_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


class PhotoResponse(BaseModel):
    id: int
    image_path: str
    uploaded_at: str

    model_config = {"from_attributes": True}
