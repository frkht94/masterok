import psycopg2
import os  # Добавляем import os
from dotenv import load_dotenv

load_dotenv()


# DATABASE_URL = "postgresql://postgres:1234@localhost:5432/masterok_db"  # УДАЛЯЕМ ЭТУ СТРОКУ
DATABASE_URL = os.getenv("DATABASE_URL")  # ИСПОЛЬЗУЕМ os.getenv()


def get_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
    finally:
        conn.close()