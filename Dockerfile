FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Устанавливаем PYTHONPATH чтобы Python видел все модули
ENV PYTHONPATH=/app

# Создаём директорию для базы данных
RUN mkdir -p /app/data

# Запускаем только бота (не API!)
CMD ["python", "-u", "bot.py"]
