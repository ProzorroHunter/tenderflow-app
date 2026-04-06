import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния для создания фильтра
class FilterStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_keywords = State()
    waiting_for_cpv = State()
    waiting_for_region = State()
    waiting_for_min_amount = State()
    waiting_for_max_amount = State()

# Временное хранилище фильтров (в памяти)
user_filters = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start"""
    welcome_text = """
🎯 <b>Вітаємо у ProzorroHunter!</b>

Я допоможу відстежувати тендери на Prozorro 24/7

<b>Доступні команди:</b>
/create - Створити фільтр
/list - Мої фільтри
/help - Довідка
/stats - Статистика

<i>Почніть зі створення фільтра командою /create</i>
"""
    await message.answer(welcome_text, parse_mode="HTML")
    
    # Инициализируем хранилище для пользователя
    user_id = message.from_user.id
    if user_id not in user_filters:
        user_filters[user_id] = []
    
    logger.info(f"Користувач {user_id} (@{message.from_user.username}) запустив бота")


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Команда /help"""
    help_text = """
📖 <b>Довідка ProzorroHunter</b>

<b>Основні команди:</b>
/create - Створити новий фільтр для моніторингу тендерів
/list - Переглянути усі ваші фільтри
/stats - Статистика використання
/help - Показати цю довідку

<b>Як працює бот:</b>
1️⃣ Створіть фільтр за допомогою /create
2️⃣ Вкажіть ключові слова (наприклад: "ноутбук, комп'ютер")
3️⃣ Налаштуйте параметри (CPV, регіон, сума)
4️⃣ Отримуйте сповіщення про нові тендери!

<b>Приклади ключових слів:</b>
- "меблі офісні"
- "будівельні матеріали"  
- "послуги охорони"
- "комп'ютерна техніка"

<b>Підтримка:</b>
З питань звертайтеся до розробників
"""
    await message.answer(help_text, parse_mode="HTML")


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Команда /stats"""
    user_id = message.from_user.id
    filter_count = len(user_filters.get(user_id, []))
    
    stats_text = f"""
📊 <b>Ваша статистика</b>

👤 Користувач: {message.from_user.full_name}
🔍 Активних фільтрів: {filter_count}
📅 Дата реєстрації: сьогодні

<i>Створіть більше фільтрів командою /create</i>
"""
    await message.answer(stats_text, parse_mode="HTML")


@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    """Команда /list - показать фильтры"""
    user_id = message.from_user.id
    filters = user_filters.get(user_id, [])
    
    if not filters:
        await message.answer(
            "❌ У вас ще немає фільтрів.\n\n"
            "Створіть перший фільтр командою /create",
            parse_mode="HTML"
        )
        return
    
    text = "📋 <b>Ваші фільтри:</b>\n\n"
    for i, f in enumerate(filters, 1):
        text += f"<b>{i}. {f['name']}</b>\n"
        text += f"   🔑 Ключові слова: {f.get('keywords', 'не вказано')}\n"
        if f.get('cpv'):
            text += f"   📦 CPV: {f['cpv']}\n"
        if f.get('region'):
            text += f"   📍 Регіон: {f['region']}\n"
        if f.get('min_amount') or f.get('max_amount'):
            min_a = f.get('min_amount', '0')
            max_a = f.get('max_amount', '∞')
            text += f"   💰 Сума: {min_a} - {max_a} грн\n"
        text += "\n"
    
    await message.answer(text, parse_mode="HTML")


@dp.message(Command("create"))
async def cmd_create(message: types.Message, state: FSMContext):
    """Команда /create - начать создание фильтра"""
    await message.answer(
        "🆕 <b>Створення нового фільтра</b>\n\n"
        "Введіть назву фільтра (наприклад: 'Комп'ютерна техніка'):",
        parse_mode="HTML"
    )
    await state.set_state(FilterStates.waiting_for_name)


@dp.message(FilterStates.waiting_for_name)
async def process_filter_name(message: types.Message, state: FSMContext):
    """Получение названия фильтра"""
    await state.update_data(name=message.text)
    await message.answer(
        "✅ Назва збережена!\n\n"
        "Тепер введіть <b>ключові слова</b> для пошуку\n"
        "(наприклад: 'ноутбук, комп'ютер, монітор'):\n\n"
        "<i>Або відправте '-' щоб пропустити</i>",
        parse_mode="HTML"
    )
    await state.set_state(FilterStates.waiting_for_keywords)


@dp.message(FilterStates.waiting_for_keywords)
async def process_keywords(message: types.Message, state: FSMContext):
    """Получение ключевых слов"""
    keywords = message.text if message.text != '-' else None
    await state.update_data(keywords=keywords)
    
    await message.answer(
        "✅ Ключові слова збережені!\n\n"
        "Введіть <b>CPV код</b> (наприклад: '30200000-1'):\n\n"
        "<i>Або відправте '-' щоб пропустити</i>",
        parse_mode="HTML"
    )
    await state.set_state(FilterStates.waiting_for_cpv)


@dp.message(FilterStates.waiting_for_cpv)
async def process_cpv(message: types.Message, state: FSMContext):
    """Получение CPV кода"""
    cpv = message.text if message.text != '-' else None
    await state.update_data(cpv=cpv)
    
    await message.answer(
        "✅ CPV збережено!\n\n"
        "Введіть <b>регіон</b> (наприклад: 'Київська область'):\n\n"
        "<i>Або відправте '-' щоб пропустити</i>",
        parse_mode="HTML"
    )
    await state.set_state(FilterStates.waiting_for_region)


@dp.message(FilterStates.waiting_for_region)
async def process_region(message: types.Message, state: FSMContext):
    """Получение региона"""
    region = message.text if message.text != '-' else None
    await state.update_data(region=region)
    
    await message.answer(
        "✅ Регіон збережено!\n\n"
        "Введіть <b>мінімальну суму</b> тендера в грн (наприклад: '50000'):\n\n"
        "<i>Або відправте '-' щоб пропустити</i>",
        parse_mode="HTML"
    )
    await state.set_state(FilterStates.waiting_for_min_amount)


@dp.message(FilterStates.waiting_for_min_amount)
async def process_min_amount(message: types.Message, state: FSMContext):
    """Получение минимальной суммы"""
    min_amount = None
    if message.text != '-':
        try:
            min_amount = float(message.text)
        except ValueError:
            await message.answer("❌ Будь ласка, введіть число або '-'")
            return
    
    await state.update_data(min_amount=min_amount)
    
    await message.answer(
        "✅ Мінімальна сума збережена!\n\n"
        "Введіть <b>максимальну суму</b> тендера в грн (наприклад: '500000'):\n\n"
        "<i>Або відправте '-' щоб завершити</i>",
        parse_mode="HTML"
    )
    await state.set_state(FilterStates.waiting_for_max_amount)


@dp.message(FilterStates.waiting_for_max_amount)
async def process_max_amount(message: types.Message, state: FSMContext):
    """Получение максимальной суммы и завершение создания фильтра"""
    max_amount = None
    if message.text != '-':
        try:
            max_amount = float(message.text)
        except ValueError:
            await message.answer("❌ Будь ласка, введіть число або '-'")
            return
    
    await state.update_data(max_amount=max_amount)
    
    # Получаем все данные
    data = await state.get_data()
    user_id = message.from_user.id
    
    # Сохраняем фильтр
    if user_id not in user_filters:
        user_filters[user_id] = []
    
    user_filters[user_id].append(data)
    
    # Формируем сообщение
    summary = f"""
🎉 <b>Фільтр успішно створено!</b>

📝 <b>Параметри:</b>
- Назва: {data['name']}
- Ключові слова: {data.get('keywords', 'не вказано')}
- CPV: {data.get('cpv', 'не вказано')}
- Регіон: {data.get('region', 'не вказано')}
- Мін. сума: {data.get('min_amount', 'не вказано')} грн
- Макс. сума: {data.get('max_amount', 'не вказано')} грн

<i>Моніторинг почнеться автоматично!</i>

Переглянути всі фільтри: /list
Створити ще один: /create
"""
    
    await message.answer(summary, parse_mode="HTML")
    await state.clear()
    
    logger.info(f"Користувач {user_id} створив фільтр: {data['name']}")


@dp.message()
async def unknown_message(message: types.Message):
    """Обработка неизвестных сообщений"""
    await message.answer(
        "❓ Не зрозуміла команда.\n\n"
        "Використовуйте /help для перегляду доступних команд."
    )


async def main():
    """Основная функция запуска бота"""
    logger.info("🤖 Бот запущено!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
