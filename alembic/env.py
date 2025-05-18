from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

# Alembic config
config = context.config

# Логирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Подставляем DATABASE_URL из .env в config
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("❌ DATABASE_URL не найден в .env файле")
config.set_main_option("sqlalchemy.url", database_url)

# Импорт моделей для генерации миграций
from db.database import Base
from models import (
    user, payment, order, rating, request,
    category, chat, sms_code, notification, work_photo
)
from models.user import User  # на случай, если нужно явно

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Миграции в offline-режиме (генерирует SQL скрипты)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Миграции в online-режиме (напрямую в БД)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

# Запуск нужного режима
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
