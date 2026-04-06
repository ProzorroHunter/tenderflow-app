# 🎯 ProzorroHunter — TenderFlow

> Автоматический 24/7 трекер тендеров Prozorro с уведомлениями в Telegram

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.4+-red.svg)](https://docs.celeryproject.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

## 📋 Содержание

- [Возможности](#-возможности)
- [Технологии](#-технологии)
- [Быстрый старт](#-быстрый-старт)
- [Установка](#-установка)
- [Конфигурация](#-конфигурация)
- [Использование](#-использование)
- [API](#-api)
- [Деплой](#-деплой)
- [Разработка](#-разработка)

## ✨ Возможности

- ✅ **24/7 Мониторинг** — автоматическая проверка новых тендеров каждые 10 минут
- 📱 **Telegram-уведомления** — мгновенные оповещения о подходящих тендерах
- 🔍 **Гибкие фильтры** — поиск по ключевым словам, CPV, регионам, суммам
- 🔗 **Шаринг фильтров** — делитесь настроенными фильтрами с коллегами
- 📊 **Статистика** — полная история найденных тендеров
- 🎨 **Веб-интерфейс** — красивый dashboard для управления (в разработке)
- 🔔 **Каналы** — публикация в Telegram-каналы
- 💾 **История** — все найденные тендеры сохраняются в БД

## 🛠 Технологии

### Backend
- **FastAPI** — современный веб-фреймворк
- **SQLAlchemy** — ORM для работы с БД
- **PostgreSQL** — надежная база данных
- **Celery + Redis** — фоновые задачи и очереди
- **httpx** — асинхронные HTTP-запросы

### Bot
- **aiogram 3.x** — Telegram Bot API
- **asyncio** — асинхронное программирование

### Infrastructure
- **Docker** — контейнеризация
- **Docker Compose** — оркестрация сервисов

## 🚀 Быстрый старт

### С помощью Docker (рекомендуется)

```bash
# 1. Клонировать репозиторий
git clone https://github.com/ProzorroHunter/tenderflow-app.git
cd tenderflow-app

# 2. Создать .env файл
cp .env.example .env
# Отредактируйте .env и добавьте токен бота

# 3. Запустить все сервисы
docker-compose up -d

# 4. Проверить статус
docker-compose ps

# 5. Открыть API документацию
# http://localhost:8000/docs
```

### Локальная установка

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Настроить PostgreSQL и Redis
# Убедитесь, что они запущены

# 3. Настроить переменные окружения
cp .env.example .env
# Отредактируйте .env

# 4. Инициализировать базу данных
python backend/database.py

# 5. Запустить сервисы (в разных терминалах)

# Терминал 1: FastAPI
cd backend
uvicorn main:app --reload

# Терминал 2: Celery Worker
celery -A backend.celery_app worker --loglevel=info

# Терминал 3: Celery Beat
celery -A backend.celery_app beat --loglevel=info

# Терминал 4: Telegram Bot
python bot.py
```

## ⚙️ Конфигурация

### Переменные окружения (.env)

```env
# База данных
DATABASE_URL=postgresql://user:password@localhost:5432/prozorrohunter

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_from_@BotFather
TELEGRAM_CHANNEL_ID=@your_channel_username

# Prozorro API
PROZORRO_API_BASE=https://public-api.prozorro.gov.ua/api/2.5

# Redis
REDIS_URL=redis://localhost:6379/0

# Безопасность
SECRET_KEY=your-super-secret-key-change-this
DEBUG=True
```

### Получение Telegram Bot Token

1. Открыть [@BotFather](https://t.me/BotFather) в Telegram
2. Отправить `/newbot`
3. Следовать инструкциям
4. Скопировать полученный токен в `.env`

## 📖 Использование

### Telegram Bot

1. Найти бота в Telegram (имя из @BotFather)
2. Отправить `/start`
3. Создать первый фильтр:
   - Нажать "➕ Создать фильтр"
   - Ввести название
   - Настроить критерии поиска
   - Готово! Бот начнет мониторинг

### Команды бота

- `/start` — Начать работу
- `/help` — Справка
- `/filters` — Список фильтров
- `/create` — Создать фильтр
- `/stats` — Статистика

### Пример фильтра

**Название:** Строительные работы Харьков  
**Ключевые слова:** ремонт школа  
**CPV:** 45000000  
**Регион:** Харківська область  
**Сумма:** от 100,000 до 5,000,000 грн

## 🔌 API

### Эндпоинты

#### Поиск тендеров
```http
GET /search?keywords=ремонт&min_amount=100000
```

#### Создание фильтра
```http
POST /filters?telegram_id=123456789
Content-Type: application/json

{
  "name": "Мой фильтр",
  "keywords": "строительство",
  "min_amount": 100000,
  "notify_telegram": true
}
```

#### Список фильтров
```http
GET /filters?telegram_id=123456789
```

#### Запуск проверки
```http
POST /filters/1/check
```

Полная документация API: `http://localhost:8000/docs`

## 🌐 Деплой

### Render.com

1. Создать новый Web Service
2. Подключить GitHub репозиторий
3. Настроить:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Добавить переменные окружения
5. Создать PostgreSQL и Redis инстансы
6. Деплой!

### Railway.app

1. Импортировать проект из GitHub
2. Railway автоматически определит Docker
3. Добавить PostgreSQL и Redis плагины
4. Настроить переменные окружения
5. Деплой автоматический

### Heroku

```bash
# 1. Установить Heroku CLI
heroku login

# 2. Создать приложение
heroku create prozorrohunter

# 3. Добавить addons
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini

# 4. Настроить переменные
heroku config:set TELEGRAM_BOT_TOKEN=your_token

# 5. Деплой
git push heroku main

# 6. Запустить worker
heroku ps:scale worker=1 beat=1
```

## 👨‍💻 Разработка

### Структура проекта

```
tenderflow-app/
├── backend/
│   ├── __init__.py
│   ├── main.py           # FastAPI приложение
│   ├── models.py         # SQLAlchemy модели
│   ├── database.py       # Конфигурация БД
│   ├── prozorro.py       # API Prozorro
│   ├── celery_app.py     # Celery конфигурация
│   └── tasks.py          # Celery задачи
├── bot.py                # Telegram бот
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Запуск тестов

```bash
# TODO: Добавить pytest
pytest tests/
```

### Мониторинг Celery

```bash
# Flower - веб-интерфейс для мониторинга
pip install flower
celery -A backend.celery_app flower
# Открыть http://localhost:5555
```

### Логи

```bash
# Docker logs
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f bot

# Локально
tail -f logs/app.log
```

## 📝 Roadmap

- [x] Backend на FastAPI
- [x] Интеграция с Prozorro API
- [x] База данных (PostgreSQL + SQLAlchemy)
- [x] Celery для фоновых задач
- [x] Telegram бот (aiogram 3.x)
- [ ] Frontend (React + Vite + Tailwind)
- [ ] Glassmorphism дизайн
- [ ] Авторизация пользователей
- [ ] Платные подписки
- [ ] Аналитика и дашборды
- [ ] Экспорт данных (Excel, PDF)
- [ ] Email уведомления
- [ ] WebSocket для real-time обновлений

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 Лицензия

MIT License - see [LICENSE](LICENSE) file for details

## 📧 Контакты

Станислав - [@your_telegram](https://t.me/your_username)

Project Link: [https://github.com/ProzorroHunter/tenderflow-app](https://github.com/ProzorroHunter/tenderflow-app)

---

⭐️ Если проект был полезен, поставьте звезду на GitHub!
