"""
Celery задачи для мониторинга тендеров
"""
import asyncio
from celery_app import celery_app
from database import SessionLocal
from models import TenderFilter, FoundTender, User, Notification
from prozorro import search_tenders
from datetime import datetime, timedelta
from sqlalchemy import and_
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_telegram_notification(user_telegram_id: str, message: str, tender_id: str = None):
    """
    Отправка уведомления в Telegram
    """
    from aiogram import Bot
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN не установлен")
        return False
    
    try:
        bot = Bot(token=bot_token)
        await bot.send_message(
            chat_id=user_telegram_id,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=False
        )
        await bot.session.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")
        return False


async def send_channel_notification(message: str):
    """
    Публикация в Telegram-канал
    """
    from aiogram import Bot
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
    
    if not bot_token or not channel_id:
        logger.error("TELEGRAM_BOT_TOKEN или TELEGRAM_CHANNEL_ID не установлены")
        return False
    
    try:
        bot = Bot(token=bot_token)
        await bot.send_message(
            chat_id=channel_id,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=False
        )
        await bot.session.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка публикации в канал: {e}")
        return False


def format_tender_message(tender: dict, filter_name: str) -> str:
    """
    Форматирование сообщения о тендере
    """
    title = tender.get("title", "Без названия")
    tender_id = tender.get("id", "N/A")
    
    # Получение суммы
    value = tender.get("value") or tender.get("amount")
    amount = "N/A"
    currency = "UAH"
    if isinstance(value, dict):
        amount = value.get("amount", "N/A")
        currency = value.get("currency", "UAH")
    
    # Организатор
    procuring_entity = tender.get("procuringEntity", {})
    procuring_name = procuring_entity.get("name", "N/A")
    
    # Статус
    status = tender.get("status", "N/A")
    
    # Дата
    date_modified = tender.get("dateModified", "N/A")
    
    # Ссылка на тендер
    tender_url = f"https://prozorro.gov.ua/tender/{tender_id}"
    
    message = f"""
🎯 <b>Новый тендер!</b>

📋 <b>Фильтр:</b> {filter_name}

<b>{title}</b>

💰 <b>Сумма:</b> {amount:,.2f} {currency} if isinstance(amount, (int, float)) else amount
🏢 <b>Организатор:</b> {procuring_name}
📊 <b>Статус:</b> {status}
📅 <b>Дата:</b> {date_modified[:10] if isinstance(date_modified, str) else date_modified}

🔗 <a href="{tender_url}">Открыть тендер</a>
"""
    return message.strip()


@celery_app.task(name="tasks.monitor_filter")
def monitor_filter(filter_id: int):
    """
    Проверка конкретного фильтра
    """
    db = SessionLocal()
    try:
        # Получаем фильтр
        tender_filter = db.query(TenderFilter).filter(
            and_(
                TenderFilter.id == filter_id,
                TenderFilter.is_active == True
            )
        ).first()
        
        if not tender_filter:
            logger.warning(f"Фильтр {filter_id} не найден или неактивен")
            return
        
        # Получаем пользователя
        user = db.query(User).filter(User.id == tender_filter.user_id).first()
        if not user:
            logger.warning(f"Пользователь для фильтра {filter_id} не найден")
            return
        
        # Поиск тендеров
        tenders = asyncio.run(search_tenders(
            keywords=tender_filter.keywords,
            cpv=tender_filter.cpv,
            region=tender_filter.region,
            min_amount=tender_filter.min_amount,
            max_amount=tender_filter.max_amount,
            limit=50
        ))
        
        logger.info(f"Найдено {len(tenders)} тендеров для фильтра '{tender_filter.name}'")
        
        # Проверка новых тендеров
        new_count = 0
        for tender in tenders:
            tender_id = tender.get("id")
            if not tender_id:
                continue
            
            # Проверяем, был ли уже этот тендер
            existing = db.query(FoundTender).filter(
                FoundTender.tender_id == tender_id
            ).first()
            
            if existing:
                continue  # Уже был
            
            # Сохраняем новый тендер
            value = tender.get("value") or tender.get("amount") or {}
            amount = value.get("amount") if isinstance(value, dict) else value
            currency = value.get("currency", "UAH") if isinstance(value, dict) else "UAH"
            
            found_tender = FoundTender(
                filter_id=filter_id,
                tender_id=tender_id,
                title=tender.get("title"),
                description=tender.get("description"),
                amount=float(amount) if amount else None,
                currency=currency,
                status=tender.get("status"),
                raw_data=tender
            )
            db.add(found_tender)
            
            # Отправляем уведомление
            message = format_tender_message(tender, tender_filter.name)
            
            # Личное уведомление
            if tender_filter.notify_telegram:
                success = asyncio.run(send_telegram_notification(
                    user.telegram_id,
                    message,
                    tender_id
                ))
                
                # Сохраняем в историю
                notification = Notification(
                    user_id=user.id,
                    notification_type="tender_found",
                    title=tender.get("title"),
                    message=message,
                    tender_id=tender_id,
                    sent=success,
                    sent_at=datetime.utcnow() if success else None
                )
                db.add(notification)
            
            # Публикация в канал
            if tender_filter.notify_channel:
                asyncio.run(send_channel_notification(message))
            
            new_count += 1
        
        # Обновляем время проверки
        tender_filter.last_checked = datetime.utcnow()
        if new_count > 0:
            tender_filter.last_match_at = datetime.utcnow()
        
        db.commit()
        logger.info(f"✅ Фильтр '{tender_filter.name}': {new_count} новых тендеров")
        
    except Exception as e:
        logger.error(f"Ошибка при проверке фильтра {filter_id}: {e}")
        db.rollback()
    finally:
        db.close()


@celery_app.task(name="tasks.monitor_all_filters")
def monitor_all_filters():
    """
    Проверка всех активных фильтров
    """
    db = SessionLocal()
    try:
        # Получаем все активные фильтры
        filters = db.query(TenderFilter).filter(
            TenderFilter.is_active == True
        ).all()
        
        logger.info(f"🔍 Запуск проверки {len(filters)} активных фильтров")
        
        for tender_filter in filters:
            # Запускаем задачу для каждого фильтра
            monitor_filter.delay(tender_filter.id)
        
        logger.info(f"✅ Запущено {len(filters)} задач мониторинга")
        
    except Exception as e:
        logger.error(f"Ошибка при запуске мониторинга: {e}")
    finally:
        db.close()


@celery_app.task(name="tasks.cleanup_old_data")
def cleanup_old_data():
    """
    Очистка старых данных
    """
    db = SessionLocal()
    try:
        # Удаляем уведомления старше 30 дней
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        deleted_notifications = db.query(Notification).filter(
            Notification.created_at < cutoff_date
        ).delete()
        
        # Удаляем найденные тендеры старше 90 дней
        cutoff_tenders = datetime.utcnow() - timedelta(days=90)
        deleted_tenders = db.query(FoundTender).filter(
            FoundTender.notified_at < cutoff_tenders
        ).delete()
        
        db.commit()
        
        logger.info(f"🧹 Очистка: удалено {deleted_notifications} уведомлений и {deleted_tenders} тендеров")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке данных: {e}")
        db.rollback()
    finally:
        db.close()


@celery_app.task(name="tasks.test_notification")
def test_notification(telegram_id: str, message: str = "Тестовое уведомление ProzorroHunter"):
    """
    Тестовая отправка уведомления
    """
    success = asyncio.run(send_telegram_notification(telegram_id, message))
    return {"success": success, "telegram_id": telegram_id}
