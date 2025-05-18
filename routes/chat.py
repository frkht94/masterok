from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.chat import ChatMessage, ChatMessageCreate, ChatMessageResponse
from models.order import Order
from models.user import User
from core.dependencies import get_current_user

router = APIRouter(prefix="/chat", tags=["Чат"])


@router.post("/send", response_model=ChatMessageResponse)
def send_message(
    data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == data.order_id).first()
    receiver_id = order.master_id if current_user.id == order.client_id else order.client_id

    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if current_user.id not in [order.client_id, order.master_id]:
        raise HTTPException(status_code=403, detail="Вы не участник этого заказа")

    msg = ChatMessage(
        order_id=data.order_id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        message=data.message,
        is_read=False
    )

    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@router.get("/{order_id}", response_model=List[ChatMessageResponse])
def get_chat_messages(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if current_user.id not in [order.client_id, order.master_id]:
        raise HTTPException(status_code=403, detail="Нет доступа к чату")

    return db.query(ChatMessage).filter(
        ChatMessage.order_id == order_id
    ).order_by(ChatMessage.created_at.asc()).all()

@router.put("/{order_id}/mark-read")
def mark_chat_as_read(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(ChatMessage).filter(
        ChatMessage.order_id == order_id,
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.is_read == False
    ).update({ChatMessage.is_read: True})

    db.commit()
    return {"message": "Все сообщения помечены как прочитанные"}

@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    count = db.query(ChatMessage).filter(
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.is_read == False
    ).count()
    return {"unread_messages": count}
