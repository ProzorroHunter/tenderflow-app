"""
Конфигурация базы данных
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv
from typing import Generator

from models import Base

load_dotenv()

# URL базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/prozorrohunter")

# Создание движка
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Для Celery лучше использовать NullPool
    echo=False,  # True для отладки SQL-запросов
)

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency для получения сессии БД в FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Инициализация базы данных (создание таблиц)
    """
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована")


if __name__ == "__main__":
    init_db()
