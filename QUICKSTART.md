# 🚀 БЫСТРЫЙ СТАРТ — Пошаговый Алгоритм

> **Автор:** Станислав (Харьков, Украина)  
> **Проект:** ProzorroHunter — TenderFlow  
> **Цель:** Запустить 24/7 трекер тендеров Prozorro

---

## 📋 ЧТО УЖЕ СДЕЛАНО ✅

- ✅ Backend на FastAPI с полным CRUD API
- ✅ Модели базы данных (SQLAlchemy + PostgreSQL)
- ✅ Celery + Redis для фоновых задач 24/7
- ✅ Celery Beat для автоматического мониторинга каждые 10 минут
- ✅ Telegram бот на aiogram 3.x с полным функционалом
- ✅ Docker и Docker Compose для деплоя
- ✅ Конфигурация для Render.com, Railway, Heroku
- ✅ Полная документация

---

## 📂 СТРУКТУРА ПРОЕКТА

```
tenderflow-app/
├── backend/
│   ├── __init__.py           # ✅ Пакет backend
│   ├── main.py               # ✅ FastAPI приложение (API эндпоинты)
│   ├── models.py             # ✅ SQLAlchemy модели (БД схема)
│   ├── database.py           # ✅ Конфигурация БД
│   ├── prozorro.py           # ✅ Клиент для Prozorro API
│   ├── celery_app.py         # ✅ Celery конфигурация
│   └── tasks.py              # ✅ Celery задачи (мониторинг 24/7)
│
├── bot.py                    # ✅ Telegram бот (aiogram 3.x)
├── requirements.txt          # ✅ Python зависимости
├── .env.example              # ✅ Пример переменных окружения
├── .gitignore                # ✅ Git игнор файлов
│
├── Dockerfile                # ✅ Docker образ
├── docker-compose.yml        # ✅ Оркестрация всех сервисов
├── render.yaml               # ✅ Конфигурация для Render.com
├── init.sh                   # ✅ Скрипт инициализации
│
├── README.md                 # ✅ Основная документация
├── DEPLOYMENT.md             # ✅ Инструкции по деплою
└── COMMIT_INSTRUCTIONS.md    # ✅ Инструкции для Git/GitHub
```

---

## 🎯 ПОШАГОВЫЙ АЛГОРИТМ

### ШАГ 1: Получение Telegram Bot Token ⚡

**Это КРИТИЧЕСКИ важно! Без этого бот не будет работать.**

1. Открыть Telegram
2. Найти [@BotFather](https://t.me/BotFather)
3. Отправить команду: `/newbot`
4. Ввести имя бота (например: `ProzorroHunter Bot`)
5. Ввести username бота (например: `prozorrohunter_bot`)
6. **СКОПИРОВАТЬ токен** (выглядит так: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

**Сохраните этот токен! Он понадобится на следующем шаге.**

---

### ШАГ 2: Локальное тестирование с Docker 🐳

#### 2.1. Предварительные требования

Убедитесь, что установлено:
- ✅ Docker Desktop (для Windows/Mac) или Docker Engine (для Linux)
- ✅ Docker Compose

Проверка:
```bash
docker --version
docker-compose --version
```

Если не установлено:
- **Windows/Mac:** [Скачать Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Linux:** 
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  ```

#### 2.2. Настройка переменных окружения

```bash
# Перейти в папку проекта
cd /path/to/tenderflow-app

# Создать .env из примера
cp .env.example .env

# Открыть .env в редакторе
nano .env
# или
code .env
# или любой другой редактор
```

**Отредактировать .env:**
```env
DATABASE_URL=postgresql://prozorro:secure_password_change_me@postgres:5432/prozorrohunter
TELEGRAM_BOT_TOKEN=ВСТАВЬТЕ_ВАШ_ТОКЕН_СЮДА
TELEGRAM_CHANNEL_ID=@your_channel  # Опционально, если есть канал
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-super-secret-key-change-this
DEBUG=True
PROZORRO_API_BASE=https://public-api.prozorro.gov.ua/api/2.5
```

**ВАЖНО:** Замените `ВСТАВЬТЕ_ВАШ_ТОКЕН_СЮДА` на реальный токен из Шага 1!

#### 2.3. Запуск всех сервисов

```bash
# Вариант А: Автоматический запуск
./init.sh

# Вариант Б: Ручной запуск
docker-compose up -d

# Проверить статус
docker-compose ps
```

Вы должны увидеть 6 запущенных контейнеров:
- ✅ `prozorrohunter_db` (PostgreSQL)
- ✅ `prozorrohunter_redis` (Redis)
- ✅ `prozorrohunter_api` (FastAPI)
- ✅ `prozorrohunter_worker` (Celery Worker)
- ✅ `prozorrohunter_beat` (Celery Beat)
- ✅ `prozorrohunter_bot` (Telegram Bot)

#### 2.4. Проверка работоспособности

```bash
# 1. Проверить API
curl http://localhost:8000/health

# Или открыть в браузере:
# http://localhost:8000/docs - Swagger UI

# 2. Проверить логи бота
docker-compose logs -f bot

# 3. Проверить логи worker
docker-compose logs -f worker

# Вы должны увидеть:
# bot       | 🤖 Бот запущен!
# worker    | celery@... ready
# beat      | Scheduler: Sending due task...
```

#### 2.5. Тестирование бота

1. Открыть Telegram
2. Найти вашего бота по username (из Шага 1)
3. Отправить `/start`
4. Вы должны увидеть приветственное сообщение! 🎉

**Если бот отвечает — ВСЁ РАБОТАЕТ!** ✅

---

### ШАГ 3: Создание первого фильтра 🔍

**В Telegram боте:**

1. Нажать **"➕ Создать фильтр"**
2. Ввести название: `Тестовый фильтр`
3. Ввести ключевые слова: `ремонт` (или `-` чтобы пропустить)
4. CPV: `-` (пропустить)
5. Регион: `-` (пропустить)
6. Минимальная сумма: `100000` (или `-`)
7. Максимальная сумма: `-` (пропустить)

**Бот автоматически:**
- Создаст фильтр в базе данных
- Запустит первую проверку
- Начнет мониторинг каждые 10 минут
- Отправит уведомления о новых тендерах

---

### ШАГ 4: Просмотр результатов 📊

#### В Telegram:
- Нажать **"📋 Мои фильтры"**
- Выбрать фильтр
- Посмотреть статистику

#### В API (Swagger UI):
1. Открыть http://localhost:8000/docs
2. Попробовать эндпоинты:
   - `GET /health` — проверка здоровья
   - `GET /search` — прямой поиск тендеров
   - `GET /filters` — список фильтров
   - `GET /found-tenders` — найденные тендеры

#### В логах:
```bash
# Смотреть что находит система
docker-compose logs -f worker

# Вы увидите:
# worker | 🔍 Запуск проверки 1 активных фильтров
# worker | Найдено 15 тендеров для фильтра 'Тестовый фильтр'
# worker | ✅ Фильтр 'Тестовый фильтр': 3 новых тендеров
```

---

### ШАГ 5: Загрузка в GitHub 📤

#### 5.1. Создать репозиторий на GitHub

1. Зайти на [github.com](https://github.com)
2. Нажать **"+"** → **"New repository"**
3. Заполнить:
   - Owner: `ProzorroHunter`
   - Repository name: `tenderflow-app`
   - Description: `Автоматический 24/7 трекер тендеров Prozorro`
   - Public (или Private)
   - **НЕ добавлять** README, .gitignore, license
4. Создать репозиторий

#### 5.2. Загрузить код

```bash
# Перейти в папку проекта
cd /path/to/tenderflow-app

# Инициализировать Git
git init

# Добавить все файлы
git add .

# Проверить что добавляется (НЕ должно быть .env!)
git status

# Создать коммит
git commit -m "🎯 Initial commit: Full ProzorroHunter implementation

- FastAPI backend with Prozorro API
- PostgreSQL models and migrations
- Celery 24/7 monitoring (every 10 min)
- Telegram bot with aiogram 3.x
- Docker and docker-compose
- Full documentation
- Ready for deployment"

# Добавить remote
git remote add origin https://github.com/ProzorroHunter/tenderflow-app.git

# Отправить в GitHub
git branch -M main
git push -u origin main
```

**Проверьте на GitHub — все файлы должны быть загружены!** ✅

---

### ШАГ 6: Деплой на Render.com (БЕСПЛАТНО) 🌐

#### 6.1. Создать аккаунт

1. Зайти на [render.com](https://render.com)
2. Sign Up (можно через GitHub)
3. Подтвердить email

#### 6.2. Деплой через Blueprint (автоматически)

1. Нажать **"New"** → **"Blueprint"**
2. Подключить GitHub
3. Выбрать репозиторий `ProzorroHunter/tenderflow-app`
4. Render найдет `render.yaml`
5. Нажать **"Apply"**

#### 6.3. Настроить переменные

Render запросит:
- **TELEGRAM_BOT_TOKEN** — ваш токен из Шага 1
- **TELEGRAM_CHANNEL_ID** — ID канала (опционально, можно оставить пустым)

Остальное создается автоматически!

#### 6.4. Дождаться деплоя

Render автоматически:
- Создаст PostgreSQL базу данных
- Создаст Redis
- Деплоит API (FastAPI)
- Запустит Celery Worker
- Запустит Celery Beat
- Запустит Telegram бота

**Время деплоя: ~5-10 минут**

#### 6.5. Проверить

1. Открыть URL вашего API (например: `https://prozorrohunter-api.onrender.com`)
2. Добавить `/docs` — увидите Swagger UI
3. Проверить `/health` — должен вернуть `{"status": "healthy"}`
4. Протестировать бота в Telegram — должен работать! 🎉

---

### ШАГ 7: Тестирование в продакшене ✅

#### 7.1. Создать фильтр через бота

Повторите Шаг 3 в продакшен-боте.

#### 7.2. Проверить автоматический мониторинг

Подождите 10 минут — бот должен автоматически проверить фильтры и отправить уведомления.

#### 7.3. Мониторинг логов на Render

1. Зайти в Dashboard на Render
2. Открыть каждый сервис
3. Смотреть логи (Logs tab)

**Вы должны увидеть:**
```
worker | 🔍 Запуск проверки активных фильтров
worker | Найдено 15 тендеров для фильтра '...'
bot    | 🎯 Новый тендер!
```

---

## 🎯 ИТОГОВЫЙ ЧЕКЛИСТ

### Локально ✅
- [ ] Docker и Docker Compose установлены
- [ ] Получен Telegram Bot Token
- [ ] Создан и настроен `.env`
- [ ] Запущены все сервисы (`docker-compose up -d`)
- [ ] API доступен на `http://localhost:8000/docs`
- [ ] Бот отвечает в Telegram
- [ ] Создан тестовый фильтр
- [ ] Получены уведомления о тендерах

### GitHub ✅
- [ ] Создан репозиторий `ProzorroHunter/tenderflow-app`
- [ ] Загружен весь код (`git push`)
- [ ] `.env` НЕ загружен (проверить!)
- [ ] README.md отображается корректно

### Render.com ✅
- [ ] Создан аккаунт на Render
- [ ] Деплой через Blueprint успешен
- [ ] Все 6 сервисов работают
- [ ] API доступен по URL
- [ ] Бот работает в продакшене
- [ ] Автоматический мониторинг каждые 10 минут
- [ ] Уведомления приходят в Telegram

---

## 🆘 ЧТО ДЕЛАТЬ ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

### Бот не отвечает
```bash
# Проверить токен
echo $TELEGRAM_BOT_TOKEN

# Проверить логи
docker-compose logs bot

# Перезапустить
docker-compose restart bot
```

### API не доступен
```bash
# Проверить статус
docker-compose ps

# Проверить логи
docker-compose logs api

# Перезапустить
docker-compose restart api
```

### Celery не работает
```bash
# Проверить Redis
docker-compose logs redis

# Проверить Worker
docker-compose logs worker

# Перезапустить всё
docker-compose restart worker beat
```

### База данных не подключается
```bash
# Проверить PostgreSQL
docker-compose logs postgres

# Проверить переменные
docker-compose exec api env | grep DATABASE

# Пересоздать
docker-compose down
docker-compose up -d
```

### Полный сброс
```bash
# Остановить всё
docker-compose down -v

# Удалить volumes
docker volume prune

# Запустить заново
docker-compose up -d
```

---

## 📞 ПОДДЕРЖКА

- **GitHub Issues:** [создать issue](https://github.com/ProzorroHunter/tenderflow-app/issues)
- **Документация:** см. README.md и DEPLOYMENT.md
- **Telegram:** @prozorrohunter_support

---

## 🎉 ПОЗДРАВЛЯЮ!

Если вы прошли все шаги — у вас теперь работает:

✅ Полноценная система мониторинга тендеров 24/7  
✅ Автоматические уведомления в Telegram  
✅ Профессиональный API на FastAPI  
✅ Масштабируемая архитектура  
✅ Готовность к монетизации  

**Следующие шаги:**
1. Добавить Frontend (React + Glassmorphism)
2. Настроить платные подписки
3. Добавить аналитику и дашборды
4. Масштабировать на большее количество пользователей

---

**Удачи с проектом! 🚀**
