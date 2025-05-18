import os
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from db.database import get_db
from jose import JWTError, jwt
from typing import Optional
from datetime import datetime, timedelta
from models.user import User

ALGORITHM = "HS256"
security = HTTPBearer()


# Создание токена
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=ALGORITHM)


# Получение текущего пользователя по токену
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Неверный токен")
    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


# Проверка на администратора
async def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.user_type != "admin":
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    return current_user.id


# Проверка на клиента
async def get_current_client_id(current_user: User = Depends(get_current_user)):
    if current_user.user_type != "client":
        raise HTTPException(status_code=403, detail="Требуются права клиента")
    return current_user.id


# Проверка на мастера
async def get_current_master_id(current_user: User = Depends(get_current_user)):
    if current_user.user_type != "master":
        raise HTTPException(status_code=403, detail="Требуются права мастера")
    return current_user.id
