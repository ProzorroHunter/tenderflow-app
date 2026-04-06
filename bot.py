"""
Telegram-бот для ProzorroHunter
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import httpx

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Создание бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()


# Состояния для создания фильтра
class FilterCreation(StatesGroup):
    waiting_for_name = State()
    waiting_for_keywords = State()
    waiting_for_cpv = State()
    waiting_for_region = State()
    waiting_for_min_amount = State()
    waiting_for_max_amount = State()
    confirm = State()


# === КЛАВИАТУРЫ ===

def main_menu_keyboard():
    """Главное меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать фильтр", callback_data="create_filter")],
        [InlineKeyboardButton(text="📋 Мои фильтры", callback_data="my_filters")],
        [InlineKeyboardButton(text="🔍 Поиск тендеров", callback_data="search_tenders")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="statistics")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ])
    return keyboard


def filter_actions_keyboard(filter_id: int):
    """Действия с фильтром"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Запустить", callback_data=f"run_{filter_id}")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{filter_id}")],
        [InlineKeyboardButton(text="🔗 Поделиться", callback_data=f"share_{filter_id}")],
        [
            InlineKeyboardButton(text="⏸ Остановить", callback_data=f"pause_{filter_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{filter_id}")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="my_filters")]
    ])
    return keyboard


def back_to_menu_keyboard():
    """Кнопка назад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")]
    ])
    return keyboard


# === API ФУНКЦИИ ===

async def register_user(telegram_id: str, username: str = None, first_name: str = None, last_name: str = None):
    """Регистрация пользователя в системе"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/users",
                json={
                    "telegram_id": telegram_id,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя: {e}")
            return None


async def get_user_filters(telegram_id: str):
    """Получение фильтров пользователя"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_BASE_URL}/filters",
                params={"telegram_id": telegram_id}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка получения фильтров: {e}")
            return []


async def create_filter_api(telegram_id: str, filter_data: dict):
    """Создание фильтра"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/filters",
                params={"telegram_id": telegram_id},
                json=filter_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка создания фильтра: {e}")
            return None


async def delete_filter_api(filter_id: int):
    """Удаление фильтра"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(f"{API_BASE_URL}/filters/{filter_id}")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления фильтра: {e}")
            return False


async def toggle_filter_api(filter_id: int, is_active: bool):
    """Включение/выключение фильтра"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.patch(
                f"{API_BASE_URL}/filters/{filter_id}",
                json={"is_active": is_active}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Ошибка изменения статуса фильтра: {e}")
            return False


async def run_filter_check(filter_id: int):
    """Запуск проверки фильтра"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_BASE_URL}/filters/{filter_id}/check")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка запуска проверки: {e}")
            return None


# === ОБРАБОТЧИКИ КОМАНД ===

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработка команды /start"""
    user = message.from_user
    
    # Регистрация пользователя
    await register_user(
        telegram_id=str(user.id),
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    welcome_text = f"""
🎯 <b>Добро пожаловать в ProzorroHunter!</b>

Привет, {user.first_name}! 👋

Я помогу тебе отслеживать тендеры Prozorro 24/7 и получать уведомления о новых возможностях.

<b>Что я умею:</b>
✅ Автоматический мониторинг тендеров по вашим критериям
✅ Мгновенные уведомления о новых тендерах
✅ Фильтрация по ключевым словам, CPV, регионам и суммам
✅ Возможность делиться фильтрами с коллегами
✅ Красивый веб-интерфейс для управления

<b>Начните с создания первого фильтра!</b>
"""
    
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь"""
    help_text = """
📚 <b>Справка ProzorroHunter</b>

<b>Основные команды:</b>
/start - Начать работу с ботом
/help - Показать эту справку
/filters - Мои фильтры
/create - Создать новый фильтр
/stats - Статистика

<b>Как создать фильтр:</b>
1. Нажмите "Создать фильтр"
2. Укажите название (для удобства)
3. Задайте критерии поиска
4. Готово! Бот начнет мониторинг

<b>Критерии фильтрации:</b>
• Ключевые слова - поиск в названии и описании
• CPV код - классификатор товаров и услуг
• Регион - географическое ограничение
• Сумма - минимальная и максимальная

<b>Поддержка:</b>
Вопросы? Напишите @prozorrohunter_support
"""
    
    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=back_to_menu_keyboard()
    )


# === ОБРАБОТЧИКИ CALLBACK ===

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery):
    """Показать главное меню"""
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "create_filter")
async def start_filter_creation(callback: CallbackQuery, state: FSMContext):
    """Начать создание фильтра"""
    await callback.message.edit_text(
        "➕ <b>Создание нового фильтра</b>\n\n"
        "Шаг 1 из 6: Как назовем фильтр?\n\n"
        "Например: <i>\"Строительные работы в Харькове\"</i>",
        parse_mode="HTML"
    )
    await state.set_state(FilterCreation.waiting_for_name)
    await callback.answer()


@router.message(FilterCreation.waiting_for_name)
async def process_filter_name(message: Message, state: FSMContext):
    """Обработка названия фильтра"""
    await state.update_data(name=message.text)
    
    await message.answer(
        "Шаг 2 из 6: Введите ключевые слова для поиска\n\n"
        "Например: <i>\"ремонт школа\"</i>\n\n"
        "Или отправьте <code>-</code> чтобы пропустить",
        parse_mode="HTML"
    )
    await state.set_state(FilterCreation.waiting_for_keywords)


@router.message(FilterCreation.waiting_for_keywords)
async def process_keywords(message: Message, state: FSMContext):
    """Обработка ключевых слов"""
    keywords = None if message.text == "-" else message.text
    await state.update_data(keywords=keywords)
    
    await message.answer(
        "Шаг 3 из 6: Введите CPV код\n\n"
        "Например: <i>45000000 (строительные работы)</i>\n\n"
        "Или отправьте <code>-</code> чтобы пропустить",
        parse_mode="HTML"
    )
    await state.set_state(FilterCreation.waiting_for_cpv)


@router.message(FilterCreation.waiting_for_cpv)
async def process_cpv(message: Message, state: FSMContext):
    """Обработка CPV"""
    cpv = None if message.text == "-" else message.text
    await state.update_data(cpv=cpv)
    
    await message.answer(
        "Шаг 4 из 6: Введите регион\n\n"
        "Например: <i>Харківська область</i>\n\n"
        "Или отправьте <code>-</code> чтобы пропустить",
        parse_mode="HTML"
    )
    await state.set_state(FilterCreation.waiting_for_region)


@router.message(FilterCreation.waiting_for_region)
async def process_region(message: Message, state: FSMContext):
    """Обработка региона"""
    region = None if message.text == "-" else message.text
    await state.update_data(region=region)
    
    await message.answer(
        "Шаг 5 из 6: Минимальная сумма тендера (в грн)\n\n"
        "Например: <i>100000</i>\n\n"
        "Или отправьте <code>-</code> чтобы пропустить",
        parse_mode="HTML"
    )
    await state.set_state(FilterCreation.waiting_for_min_amount)


@router.message(FilterCreation.waiting_for_min_amount)
async def process_min_amount(message: Message, state: FSMContext):
    """Обработка минимальной суммы"""
    min_amount = None
    if message.text != "-":
        try:
            min_amount = float(message.text.replace(" ", "").replace(",", ""))
        except ValueError:
            await message.answer("❌ Неверный формат числа. Попробуйте снова:")
            return
    
    await state.update_data(min_amount=min_amount)
    
    await message.answer(
        "Шаг 6 из 6: Максимальная сумма тендера (в грн)\n\n"
        "Например: <i>1000000</i>\n\n"
        "Или отправьте <code>-</code> чтобы пропустить",
        parse_mode="HTML"
    )
    await state.set_state(FilterCreation.waiting_for_max_amount)


@router.message(FilterCreation.waiting_for_max_amount)
async def process_max_amount(message: Message, state: FSMContext):
    """Обработка максимальной суммы и создание фильтра"""
    max_amount = None
    if message.text != "-":
        try:
            max_amount = float(message.text.replace(" ", "").replace(",", ""))
        except ValueError:
            await message.answer("❌ Неверный формат числа. Попробуйте снова:")
            return
    
    await state.update_data(max_amount=max_amount)
    
    # Получаем все данные
    data = await state.get_data()
    
    # Создаем фильтр
    filter_data = {
        "name": data["name"],
        "keywords": data.get("keywords"),
        "cpv": data.get("cpv"),
        "region": data.get("region"),
        "min_amount": data.get("min_amount"),
        "max_amount": data.get("max_amount"),
        "notify_telegram": True,
        "notify_channel": False
    }
    
    result = await create_filter_api(str(message.from_user.id), filter_data)
    
    if result:
        summary = f"""
✅ <b>Фильтр создан успешно!</b>

📋 <b>Название:</b> {data['name']}
"""
        if data.get("keywords"):
            summary += f"🔍 <b>Ключевые слова:</b> {data['keywords']}\n"
        if data.get("cpv"):
            summary += f"📝 <b>CPV:</b> {data['cpv']}\n"
        if data.get("region"):
            summary += f"📍 <b>Регион:</b> {data['region']}\n"
        if data.get("min_amount"):
            summary += f"💰 <b>От:</b> {data['min_amount']:,.0f} грн\n"
        if data.get("max_amount"):
            summary += f"💰 <b>До:</b> {data['max_amount']:,.0f} грн\n"
        
        summary += f"\n🔗 <b>Код для шаринга:</b> <code>{result.get('share_code')}</code>"
        summary += "\n\n✨ Мониторинг запущен! Я буду присылать уведомления о новых тендерах."
        
        await message.answer(summary, parse_mode="HTML", reply_markup=main_menu_keyboard())
    else:
        await message.answer(
            "❌ Ошибка при создании фильтра. Попробуйте позже.",
            reply_markup=main_menu_keyboard()
        )
    
    await state.clear()


@router.callback_query(F.data == "my_filters")
async def show_my_filters(callback: CallbackQuery):
    """Показать фильтры пользователя"""
    telegram_id = str(callback.from_user.id)
    filters = await get_user_filters(telegram_id)
    
    if not filters:
        await callback.message.edit_text(
            "📋 <b>У вас пока нет фильтров</b>\n\n"
            "Создайте первый фильтр для начала мониторинга!",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return
    
    text = f"📋 <b>Ваши фильтры</b> ({len(filters)}):\n\n"
    
    keyboard_buttons = []
    for f in filters:
        status = "▶️" if f["is_active"] else "⏸"
        text += f"{status} <b>{f['name']}</b>\n"
        if f.get("keywords"):
            text += f"   🔍 {f['keywords']}\n"
        text += f"   📊 Найдено: {len(f.get('found_tenders', []))}\n\n"
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{status} {f['name'][:30]}",
                callback_data=f"filter_{f['id']}"
            )
        ])
    
    keyboard_buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("filter_"))
async def show_filter_details(callback: CallbackQuery):
    """Показать детали фильтра"""
    filter_id = int(callback.data.split("_")[1])
    
    # Здесь должен быть запрос к API для получения деталей
    # Пока показываем кнопки действий
    
    await callback.message.edit_text(
        f"📋 <b>Фильтр #{filter_id}</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=filter_actions_keyboard(filter_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("run_"))
async def run_filter(callback: CallbackQuery):
    """Запустить проверку фильтра"""
    filter_id = int(callback.data.split("_")[1])
    
    result = await run_filter_check(filter_id)
    
    if result:
        await callback.answer("✅ Проверка запущена!", show_alert=True)
    else:
        await callback.answer("❌ Ошибка запуска", show_alert=True)


@router.callback_query(F.data.startswith("delete_"))
async def delete_filter(callback: CallbackQuery):
    """Удалить фильтр"""
    filter_id = int(callback.data.split("_")[1])
    
    success = await delete_filter_api(filter_id)
    
    if success:
        await callback.answer("🗑 Фильтр удален", show_alert=True)
        await show_my_filters(callback)
    else:
        await callback.answer("❌ Ошибка удаления", show_alert=True)


@router.callback_query(F.data == "statistics")
async def show_statistics(callback: CallbackQuery):
    """Показать статистику"""
    telegram_id = str(callback.from_user.id)
    filters = await get_user_filters(telegram_id)
    
    active_count = sum(1 for f in filters if f["is_active"])
    total_found = sum(len(f.get("found_tenders", [])) for f in filters)
    
    stats_text = f"""
📊 <b>Ваша статистика</b>

📋 Всего фильтров: {len(filters)}
▶️ Активных: {active_count}
🎯 Найдено тендеров: {total_found}

📅 Дата регистрации: сегодня
"""
    
    await callback.message.edit_text(
        stats_text,
        parse_mode="HTML",
        reply_markup=back_to_menu_keyboard()
    )
    await callback.answer()


# === ЗАПУСК БОТА ===

async def main():
    """Запуск бота"""
    dp.include_router(router)
    
    # Удаляем вебхуки (для polling)
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("🤖 Бот запущен!")
    
    # Запуск polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
