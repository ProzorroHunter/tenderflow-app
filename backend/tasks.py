from celery_app import celery_app
from models import SessionLocal, TenderFilter, MatchedTender, Notification
from prozorro import search_tenders
from telegram_bot import send_tender_notification, send_channel_notification
from datetime import datetime, timedelta
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task
def check_new_tenders():
    """
    Основная задача: проверяет новые тендеры по всем активным фильтрам
    Запускается каждые 10 минут
    """
    logger.info("🔍 Начинаю проверку новых тендеров...")
    
    db = SessionLocal()
    try:
        # Получаем все активные фильтры
        active_filters = db.query(TenderFilter).filter(TenderFilter.is_active == True).all()
        
        logger.info(f"Найдено {len(active_filters)} активных фильтров")
        
        for filter_obj in active_filters:
            try:
                # Запускаем асинхронную проверку синхронно (Celery не любит async напрямую)
                asyncio.run(check_filter_for_new_tenders(filter_obj.id))
                
                # Обновляем время последней проверки
                filter_obj.last_checked = datetime.utcnow()
                db.commit()
                
            except Exception as e:
                logger.error(f"❌ Ошибка при проверке фильтра {filter_obj.id}: {e}")
                db.rollback()
                continue
        
        logger.info("✅ Проверка тендеров завершена")
        return {"checked_filters": len(active_filters)}
        
    finally:
        db.close()

async def check_filter_for_new_tenders(filter_id: int):
    """Проверяет один конкретный фильтр на новые тендеры"""
    db = SessionLocal()
    try:
        filter_obj = db.query(TenderFilter).filter(TenderFilter.id == filter_id).first()
        if not filter_obj:
            return
        
        logger.info(f"Проверяю фильтр '{filter_obj.name}' (ID: {filter_id})")
        
        # Подготовка параметров поиска
        keywords = filter_obj.keywords
        cpv = filter_obj.cpv_codes.split(",")[0] if filter_obj.cpv_codes else None
        region = filter_obj.region
        min_amount = filter_obj.min_amount
        max_amount = filter_obj.max_amount
        
        # Ищем тендеры
        tenders = await search_tenders(
            keywords=keywords,
            cpv=cpv,
            region=region,
            min_amount=min_amount,
            max_amount=max_amount,
            limit=50  # Проверяем последние 50 тендеров
        )
        
        new_tenders_count = 0
        
        for tender in tenders:
            tender_id = tender.get("id")
            if not tender_id:
                continue
            
            # Проверяем, не отправляли ли мы уже уведомление об этом тендере
            existing = db.query(MatchedTender).filter(
                MatchedTender.filter_id == filter_id,
                MatchedTender.tender_id == tender_id
            ).first()
            
            if not existing:
                # Новый тендер! Сохраняем в БД
                value = tender.get("value") or tender.get("amount") or {}
                amount = value.get("amount") if isinstance(value, dict) else None
                
                matched_tender = MatchedTender(
                    filter_id=filter_id,
                    tender_id=tender_id,
                    tender_title=tender.get("title", "Без названия"),
                    tender_amount=float(amount) if amount else None,
                    tender_url=f"https://prozorro.gov.ua/tender/{tender_id}",
                    notified=False
                )
                db.add(matched_tender)
                db.commit()
                
                # Отправляем уведомление
                await send_notifications(filter_obj, matched_tender, tender)
                
                matched_tender.notified = True
                db.commit()
                
                new_tenders_count += 1
                logger.info(f"✨ Новый тендер найден: {tender_id}")
        
        if new_tenders_count > 0:
            logger.info(f"🎉 Фильтр '{filter_obj.name}': найдено {new_tenders_count} новых тендеров")
        
    finally:
        db.close()

async def send_notifications(filter_obj, matched_tender, tender_data):
    """Отправляет уведомления в канал и/или лично"""
    try:
        # Формируем красивое сообщение
        message = format_tender_message(matched_tender, tender_data, filter_obj.name)
        
        # Отправляем в канал, если включено
        if filter_obj.notify_channel:
            await send_channel_notification(message)
            log_notification(filter_obj.user_id, 'channel', message, True)
        
        # Отправляем личное сообщение, если включено и есть telegram_id
        if filter_obj.notify_private and filter_obj.user and filter_obj.user.telegram_id:
            await send_tender_notification(filter_obj.user.telegram_id, message)
            log_notification(filter_obj.user_id, 'private', message, True)
            
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления: {e}")
        log_notification(filter_obj.user_id, 'unknown', str(e), False, str(e))

def format_tender_message(matched_tender, tender_data, filter_name):
    """Форматирует сообщение о тендере для Telegram"""
    title = matched_tender.tender_title or "Без названия"
    amount = matched_tender.tender_amount
    url = matched_tender.tender_url
    
    # Форматируем сумму
    amount_str = f"{amount:,.0f} UAH" if amount else "Сумма не указана"
    
    # Получаем заказчика
    procuring = tender_data.get("procuringEntity", {})
    customer = procuring.get("name", "Заказчик не указан")
    
    message = f"""🔔 <b>Новый тендер по фильтру "{filter_name}"</b>

📋 <b>{title}</b>

💰 Сумма: {amount_str}
🏢 Заказчик: {customer}
🔗 <a href="{url}">Открыть на Prozorro</a>

⏰ Найдено: {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
    return message

def log_notification(user_id, type_msg, message, success, error=None):
    """Логирует отправленное уведомление в БД"""
    db = SessionLocal()
    try:
        notification = Notification(
            user_id=user_id,
            type=type_msg,
            message=message[:500],  # Обрезаем для БД
            success=success,
            error_message=error
        )
        db.add(notification)
        db.commit()
    except Exception as e:
        logger.error(f"Ошибка логирования уведомления: {e}")
    finally:
        db.close()

@celery_app.task
def test_notification():
    """Тестовая задача для проверки отправки уведомлений"""
    test_message = """🧪 <b>Тестовое уведомление ProzorroHunter</b>

Если вы видите это сообщение, значит система уведомлений работает корректно!

✅ Celery запущен
✅ Redis подключен  
✅ Telegram бот работает
"""
    asyncio.run(send_channel_notification(test_message))
    return "Тестовое уведомление отправлено"
