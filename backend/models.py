"""
Модели базы данных для ProzorroHunter
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """Пользователь системы (Telegram)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    filters = relationship("TenderFilter", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class TenderFilter(Base):
    """Фильтр для мониторинга тендеров"""
    __tablename__ = "tender_filters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Уникальный код для шаринга
    share_code = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4())[:8])
    
    # Параметры фильтра
    name = Column(String, nullable=False)  # Название фильтра (для удобства)
    keywords = Column(String, nullable=True)
    cpv = Column(String, nullable=True)
    region = Column(String, nullable=True)
    min_amount = Column(Float, nullable=True)
    max_amount = Column(Float, nullable=True)
    
    # Настройки уведомлений
    is_active = Column(Boolean, default=True)
    notify_telegram = Column(Boolean, default=True)
    notify_channel = Column(Boolean, default=False)  # Публиковать в канал
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    last_match_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="filters")
    found_tenders = relationship("FoundTender", back_populates="filter", cascade="all, delete-orphan")


class FoundTender(Base):
    """Найденный тендер (для избежания дубликатов уведомлений)"""
    __tablename__ = "found_tenders"

    id = Column(Integer, primary_key=True, index=True)
    filter_id = Column(Integer, ForeignKey("tender_filters.id"), nullable=False)
    
    # Идентификатор тендера из Prozorro
    tender_id = Column(String, unique=True, index=True, nullable=False)
    
    # Базовая информация о тендере
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String, default="UAH")
    status = Column(String, nullable=True)
    
    # Дополнительные данные (полный JSON ответ)
    raw_data = Column(JSON, nullable=True)
    
    # Уведомление
    notified_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    filter = relationship("TenderFilter", back_populates="found_tenders")


class Notification(Base):
    """История уведомлений"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Тип уведомления
    notification_type = Column(String, nullable=False)  # tender_found, system, error
    
    # Содержимое
    title = Column(String, nullable=True)
    message = Column(Text, nullable=True)
    tender_id = Column(String, nullable=True)
    
    # Статус
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="notifications")


class SystemSetting(Base):
    """Системные настройки"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
