import os
import logging
from aiogram import Bot

logger = logging.getLogger(__name__)

# Инициализация бота (будем дорабатывать в Шаге 3)
bot = None
try:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        bot = Bot(token=token)
except Exception as e:
    logger.warning(f"Telegram бот не инициализирован: {e}")

async def send_channel_notification(message: str):
    """Отправляет сообщение в Telegram канал"""
    if not bot:
        logger.warning("Бот не инициализирован, пропускаю отправку в канал")
        return
    
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not channel_id:
        logger.warning("TELEGRAM_CHANNEL_ID не указан")
        return
    
    try:
        await bot.send_message(
            chat_id=channel_id,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=False
        )
        logger.info("✅ Уведомление отправлено в канал")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки в канал: {e}")
        raise

async def send_tender_notification(telegram_id: str, message: str):
    """Отправляет личное сообщение пользователю"""
    if not bot:
        logger.warning("Бот не инициализирован, пропускаю личное сообщение")
        return
    
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=False
        )
        logger.info(f"✅ Личное уведомление отправлено пользователю {telegram_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки личного сообщения: {e}")
        raise
