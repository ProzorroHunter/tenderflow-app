from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from typing import Optional, List
from datetime import datetime

from prozorro import search_tenders
from models import get_db, Base, engine, User, TenderFilter, MatchedTender
from tasks import check_new_tenders, test_notification

load_dotenv()

# Создаём таблицы в БД при старте
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ProzorroHunter — TenderFlow",
    description="Автоматический трекер тендеров Prozorro 24/7",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "ProzorroHunter backend успешно запущен",
        "status": "ok",
        "version": "0.1.0",
        "features": ["search", "filters", "notifications", "24/7 monitoring"]
    }

@app.get("/search")
async def search_tenders_endpoint(
    keywords: Optional[str] = Query(None, description="Ключевые слова"),
    cpv: Optional[str] = Query(None, description="CPV-код"),
    region: Optional[str] = Query(None, description="Регион"),
    min_amount: Optional[float] = Query(None, description="Минимальная сумма"),
    max_amount: Optional[float] = Query(None, description="Максимальная сумма"),
    limit: int = Query(20, ge=1, le=100)
):
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

# ===== API для управления фильтрами =====

@app.post("/users")
async def create_user(telegram_id: str, username: Optional[str] = None, db: Session = Depends(get_db)):
    """Создаёт нового пользователя"""
    existing = db.query(User).filter(User.telegram_id == telegram_id).first()
    if existing:
        return {"message": "Пользователь уже существует", "user_id": existing.id}
    
    user = User(telegram_id=telegram_id, username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Пользователь создан", "user_id": user.id}

@app.post("/filters")
async def create_filter(
    user_id: int,
    name: str,
    keywords: Optional[str] = None,
    cpv_codes: Optional[str] = None,
    region: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    notify_channel: bool = True,
    notify_private: bool = True,
    db: Session = Depends(get_db)
):
    """Создаёт новый фильтр для пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    filter_obj = TenderFilter(
        user_id=user_id,
        name=name,
        keywords=keywords,
        cpv_codes=cpv_codes,
        region=region,
        min_amount=min_amount,
        max_amount=max_amount,
        notify_channel=notify_channel,
        notify_private=notify_private
    )
    db.add(filter_obj)
    db.commit()
    db.refresh(filter_obj)
    return {
        "message": "Фильтр создан",
        "filter_id": filter_obj.id,
        "shareable_link": f"/filters/{filter_obj.id}/share"
    }

@app.get("/filters/{user_id}")
async def get_user_filters(user_id: int, db: Session = Depends(get_db)):
    """Получает все фильтры пользователя"""
    filters = db.query(TenderFilter).filter(TenderFilter.user_id == user_id).all()
    return {
        "filters": [
            {
                "id": f.id,
                "name": f.name,
                "keywords": f.keywords,
                "region": f.region,
                "min_amount": f.min_amount,
                "max_amount": f.max_amount,
                "is_active": f.is_active,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "last_checked": f.last_checked.isoformat() if f.last_checked else None
            }
            for f in filters
        ]
    }

@app.get("/filters/{filter_id}/matches")
async def get_filter_matches(filter_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """Получает найденные тендеры по фильтру"""
    matches = db.query(MatchedTender).filter(
        MatchedTender.filter_id == filter_id
    ).order_by(MatchedTender.matched_at.desc()).limit(limit).all()
    
    return {
        "filter_id": filter_id,
        "matches": [
            {
                "tender_id": m.tender_id,
                "title": m.tender_title,
                "amount": m.tender_amount,
                "url": m.tender_url,
                "matched_at": m.matched_at.isoformat() if m.matched_at else None,
                "notified": m.notified
            }
            for m in matches
        ]
    }

@app.delete("/filters/{filter_id}")
async def delete_filter(filter_id: int, db: Session = Depends(get_db)):
    """Удаляет фильтр"""
    filter_obj = db.query(TenderFilter).filter(TenderFilter.id == filter_id).first()
    if not filter_obj:
        raise HTTPException(status_code=404, detail="Фильтр не найден")
    
    db.delete(filter_obj)
    db.commit()
    return {"message": "Фильтр удалён"}

# ===== API для ручного управления Celery =====

@app.post("/admin/check-now")
async def trigger_manual_check():
    """Ручной запуск проверки тендеров"""
    task = check_new_tenders.delay()
    return {
        "message": "Проверка запущена",
        "task_id": task.id,
        "status": "pending"
    }

@app.post("/admin/test-notification")
async def trigger_test_notification():
    """Отправляет тестовое уведомление"""
    task = test_notification.delay()
    return {
        "message": "Тестовое уведомление отправлено",
        "task_id": task.id
    }

@app.get("/admin/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Статистика системы"""
    users_count = db.query(User).count()
    filters_count = db.query(TenderFilter).count()
    active_filters = db.query(TenderFilter).filter(TenderFilter.is_active == True).count()
    matches_count = db.query(MatchedTender).count()
    notified_count = db.query(MatchedTender).filter(MatchedTender.notified == True).count()
    
    return {
        "users": users_count,
        "filters_total": filters_count,
        "filters_active": active_filters,
        "tenders_matched": matches_count,
        "tenders_notified": notified_count,
        "system_status": "running",
        "check_interval": "10 minutes"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
