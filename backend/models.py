from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/prozorrohunter")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    """Пользователь системы"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Отношения
    filters = relationship("TenderFilter", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user")

class TenderFilter(Base):
    """Фильтры поиска тендеров для пользователя"""
    __tablename__ = "tender_filters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Параметры поиска
    name = Column(String, nullable=False)  # Название фильтра (например "IT тендеры Киев")
    keywords = Column(String, nullable=True)  # Ключевые слова через запятую
    cpv_codes = Column(String, nullable=True)  # CPV коды через запятую
    region = Column(String, nullable=True)  # Регион/область
    min_amount = Column(Float, nullable=True)  # Минимальная сумма
    max_amount = Column(Float, nullable=True)  # Максимальная сумма
    
    # Настройки уведомлений
    notify_channel = Column(Boolean, default=False)  # Отправлять в Telegram канал
    notify_private = Column(Boolean, default=True)   # Отправлять личное сообщение
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)  # Когда последний раз проверяли
    is_active = Column(Boolean, default=True)
    
    # Отношения
    user = relationship("User", back_populates="filters")
    matched_tenders = relationship("MatchedTender", back_populates="filter", cascade="all, delete-orphan")

class MatchedTender(Base):
    """Найденные тендеры по фильтру (чтобы не дублировать уведомления)"""
    __tablename__ = "matched_tenders"
    
    id = Column(Integer, primary_key=True, index=True)
    filter_id = Column(Integer, ForeignKey("tender_filters.id"), nullable=False)
    tender_id = Column(String, nullable=False, index=True)  # ID тендера из Prozorro API
    tender_title = Column(String, nullable=True)
    tender_amount = Column(Float, nullable=True)
    tender_url = Column(String, nullable=True)
    matched_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)  # Было ли отправлено уведомление
    
    # Отношения
    filter = relationship("TenderFilter", back_populates="matched_tenders")

class Notification(Base):
    """История отправленных уведомлений"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    type = Column(String, nullable=False)  # 'channel' или 'private'
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    error_message = Column(String, nullable=True)
    
    # Отношения
    user = relationship("User", back_populates="notifications")

# Функция для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
