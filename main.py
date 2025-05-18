from fastapi import FastAPI
from db.database import Base, engine, SessionLocal
from dotenv import load_dotenv
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from routes import sms_auth, chat, notifications, payments, password_reset, users, categories, orders, admin, ratings
from fastapi.staticfiles import StaticFiles
from routes import photos,  requests as request_routes
from datetime import datetime
from services.scheduler import start_scheduler
from core.rate_limiter import limiter



load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(users.router)  #  Подключаем роутеры
app.include_router(categories.router)
app.include_router(orders.router)
app.include_router(admin.router)
app.include_router(sms_auth.router)
app.include_router(photos.router)
app.include_router(ratings.router)
app.include_router(request_routes.router)
app.include_router(chat.router),
app.include_router(notifications.router)
app.include_router(payments.router)
app.include_router(password_reset.router)

from models.user import User  # если лежит отдельно
from models.category import Category
from models.rating import Rating


Base.metadata.create_all(bind=engine)

app.mount("/media", StaticFiles(directory="media"), name="media")


@app.get("/")
async def root():
    return {"message": "Добро пожаловать в API МастерОК!"}

app.mount("/media", StaticFiles(directory="media"), name="media")

if __name__ == "__main__":
    start_scheduler()
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
