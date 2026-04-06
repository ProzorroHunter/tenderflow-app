FROM python:3.11-slim

WORKDIR /app

# Устанавливаем только необходимые зависимости
RUN pip install --no-cache-dir aiogram==3.13.0 python-dotenv==1.0.0 aiohttp==3.10.5

# Копируем бота
COPY bot_simple.py bot.py

# Создаём простой HTTP сервер для health check
RUN cat > /app/server.py << 'PYEOF'
from aiohttp import web
import asyncio
import os

async def health(request):
    return web.Response(text="ProzorroHunter Bot OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"✅ HTTP сервер запущено на порту {port}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(start_web_server())
PYEOF

# Создаём скрипт запуска
RUN cat > /app/start.sh << 'SHEOF'
#!/bin/bash
python /app/server.py &
sleep 2
python /app/bot.py
SHEOF

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
