#!/bin/bash
# Скрипт инициализации ProzorroHunter

echo "🎯 ProzorroHunter — Инициализация проекта"
echo ""

# Проверка наличия .env
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден. Копирую из .env.example..."
    cp .env.example .env
    echo "✅ Файл .env создан. Отредактируйте его перед запуском!"
    echo ""
    echo "Необходимо добавить:"
    echo "  - TELEGRAM_BOT_TOKEN (от @BotFather)"
    echo "  - TELEGRAM_CHANNEL_ID (опционально)"
    echo ""
    exit 1
fi

echo "1️⃣ Проверка зависимостей..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и повторите."
    exit 1
fi

echo "✅ Docker и Docker Compose установлены"
echo ""

echo "2️⃣ Запуск сервисов..."
docker-compose up -d

echo ""
echo "3️⃣ Ожидание готовности сервисов..."
sleep 10

echo ""
echo "4️⃣ Инициализация базы данных..."
docker-compose exec api python -c "from backend.database import init_db; init_db()"

echo ""
echo "✅ Проект успешно инициализирован!"
echo ""
echo "📊 Статус сервисов:"
docker-compose ps

echo ""
echo "🌐 API документация: http://localhost:8000/docs"
echo "💾 База данных: localhost:5432"
echo "🔴 Redis: localhost:6379"
echo ""
echo "📱 Telegram бот запущен. Найдите его в Telegram и отправьте /start"
echo ""
echo "Для просмотра логов:"
echo "  docker-compose logs -f api"
echo "  docker-compose logs -f worker"
echo "  docker-compose logs -f bot"
echo ""
echo "Для остановки:"
echo "  docker-compose down"
