from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from typing import Optional, List
from datetime import datetime

from prozorro import search_tenders
from database import get_db, init_db
from models import User, TenderFilter, FoundTender, Notification
from tasks import monitor_filter, test_notification

load_dotenv()

app = FastAPI(
    title="ProzorroHunter — TenderFlow",
    description="Автоматический трекер тендеров Prozorro 24/7",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic модели для API
class FilterCreate(BaseModel):
    name: str
    keywords: Optional[str] = None
    cpv: Optional[str] = None
    region: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    notify_telegram: bool = True
    notify_channel: bool = False


class FilterUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[str] = None
    cpv: Optional[str] = None
    region: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    is_active: Optional[bool] = None
    notify_telegram: Optional[bool] = None
    notify_channel: Optional[bool] = None


class UserCreate(BaseModel):
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


# Startup event
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    init_db()
    print("✅ ProzorroHunter запущен!")


@app.get("/")
async def root():
    return {
        "message": "ProzorroHunter backend успешно запущен",
        "status": "ok",
        "version": "0.2.0",
        "features": ["24/7 monitoring", "Telegram notifications", "Shareable filters"]
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Проверка здоровья системы"""
    try:
        # Проверка БД
        db.execute("SELECT 1")
        
        # Подсчет статистики
        users_count = db.query(User).count()
        filters_count = db.query(TenderFilter).count()
        active_filters = db.query(TenderFilter).filter(TenderFilter.is_active == True).count()
        
        return {
            "status": "healthy",
            "database": "connected",
            "stats": {
                "users": users_count,
                "filters": filters_count,
                "active_filters": active_filters
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


# === ПОИСК ТЕНДЕРОВ ===

@app.get("/search")
async def search_tenders_endpoint(
    keywords: Optional[str] = Query(None, description="Ключевые слова"),
    cpv: Optional[str] = Query(None, description="CPV-код"),
    region: Optional[str] = Query(None, description="Регион"),
    min_amount: Optional[float] = Query(None, description="Минимальная сумма"),
    max_amount: Optional[float] = Query(None, description="Максимальная сумма"),
    limit: int = Query(20, ge=1, le=100)
):
    """Поиск тендеров"""
    tenders = await search_tenders(
        keywords=keywords,
        cpv=cpv,
        region=region,
        min_amount=min_amount,
        max_amount=max_amount,
        limit=limit
    )
    return {
        "count": len(tenders),
        "tenders": tenders[:limit]
    }


# === ПОЛЬЗОВАТЕЛИ ===

@app.post("/users")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Создание или обновление пользователя"""
    existing_user = db.query(User).filter(User.telegram_id == user.telegram_id).first()
    
    if existing_user:
        # Обновляем данные
        existing_user.username = user.username
        existing_user.first_name = user.first_name
        existing_user.last_name = user.last_name
        existing_user.last_active = datetime.utcnow()
        db.commit()
        db.refresh(existing_user)
        return existing_user
    
    # Создаем нового
    new_user = User(
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/users/{telegram_id}")
async def get_user(telegram_id: str, db: Session = Depends(get_db)):
    """Получение пользователя"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# === ФИЛЬТРЫ ===

@app.post("/filters")
async def create_filter(
    telegram_id: str,
    filter_data: FilterCreate,
    db: Session = Depends(get_db)
):
    """Создание нового фильтра"""
    # Получаем пользователя
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Создаем фильтр
    new_filter = TenderFilter(
        user_id=user.id,
        name=filter_data.name,
        keywords=filter_data.keywords,
        cpv=filter_data.cpv,
        region=filter_data.region,
        min_amount=filter_data.min_amount,
        max_amount=filter_data.max_amount,
        notify_telegram=filter_data.notify_telegram,
        notify_channel=filter_data.notify_channel
    )
    db.add(new_filter)
    db.commit()
    db.refresh(new_filter)
    
    # Запускаем первую проверку
    monitor_filter.delay(new_filter.id)
    
    return new_filter


@app.get("/filters")
async def get_user_filters(telegram_id: str, db: Session = Depends(get_db)):
    """Получение всех фильтров пользователя"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    filters = db.query(TenderFilter).filter(TenderFilter.user_id == user.id).all()
    return filters


@app.get("/filters/{filter_id}")
async def get_filter(filter_id: int, db: Session = Depends(get_db)):
    """Получение конкретного фильтра"""
    filter_obj = db.query(TenderFilter).filter(TenderFilter.id == filter_id).first()
    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found")
    return filter_obj


@app.get("/filters/share/{share_code}")
async def get_filter_by_share_code(share_code: str, db: Session = Depends(get_db)):
    """Получение фильтра по коду шаринга"""
    filter_obj = db.query(TenderFilter).filter(TenderFilter.share_code == share_code).first()
    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found")
    return filter_obj


@app.patch("/filters/{filter_id}")
async def update_filter(
    filter_id: int,
    filter_data: FilterUpdate,
    db: Session = Depends(get_db)
):
    """Обновление фильтра"""
    filter_obj = db.query(TenderFilter).filter(TenderFilter.id == filter_id).first()
    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    # Обновляем поля
    update_data = filter_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(filter_obj, field, value)
    
    db.commit()
    db.refresh(filter_obj)
    return filter_obj


@app.delete("/filters/{filter_id}")
async def delete_filter(filter_id: int, db: Session = Depends(get_db)):
    """Удаление фильтра"""
    filter_obj = db.query(TenderFilter).filter(TenderFilter.id == filter_id).first()
    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    db.delete(filter_obj)
    db.commit()
    return {"message": "Filter deleted successfully"}


@app.post("/filters/{filter_id}/check")
async def check_filter_now(filter_id: int, db: Session = Depends(get_db)):
    """Запустить проверку фильтра прямо сейчас"""
    filter_obj = db.query(TenderFilter).filter(TenderFilter.id == filter_id).first()
    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    # Запускаем задачу
    task = monitor_filter.delay(filter_id)
    
    return {
        "message": "Проверка запущена",
        "task_id": task.id,
        "filter_id": filter_id
    }


# === НАЙДЕННЫЕ ТЕНДЕРЫ ===

@app.get("/found-tenders")
async def get_found_tenders(
    telegram_id: str,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """Получение найденных тендеров пользователя"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Получаем тендеры через фильтры пользователя
    tenders = db.query(FoundTender).join(TenderFilter).filter(
        TenderFilter.user_id == user.id
    ).order_by(FoundTender.notified_at.desc()).limit(limit).all()
    
    return tenders


# === ТЕСТИРОВАНИЕ ===

@app.post("/test/notification")
async def send_test_notification(telegram_id: str):
    """Отправка тестового уведомления"""
    task = test_notification.delay(telegram_id, "🎯 Тестовое уведомление от ProzorroHunter!\n\nСистема работает корректно ✅")
    return {
        "message": "Тестовое уведомление отправляется",
        "task_id": task.id
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
