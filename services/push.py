# services/push.py

import os
import firebase_admin
from firebase_admin import credentials, messaging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Путь к JSON-файлу ключа сервисного аккаунта Firebase
firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS")

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(firebase_credentials_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK инициализирован")
    except Exception as e:
        print(f"❌ Ошибка инициализации Firebase: {e}")

async def send_push_notification(token: str, title: str, body: str):
    """Отправка Push через Firebase Admin SDK"""
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token
        )
        response = messaging.send(message)
        print(f"✅ Push-уведомление отправлено: {response}")
    except Exception as e:
        print(f"❌ Ошибка при отправке push: {e}")
