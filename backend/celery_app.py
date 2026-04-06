"""
Celery приложение для фоновых задач
"""
from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

load_dotenv()

# Redis URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Создание Celery приложения
celery_app = Celery(
    "prozorrohunter",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"]  # Модуль с задачами
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Kiev",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 минут максимум на задачу
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Периодические задачи (расписание)
celery_app.conf.beat_schedule = {
    "monitor-tenders-every-10-minutes": {
        "task": "tasks.monitor_all_filters",
        "schedule": crontab(minute="*/10"),  # Каждые 10 минут
    },
    "cleanup-old-notifications": {
        "task": "tasks.cleanup_old_data",
        "schedule": crontab(hour=3, minute=0),  # Каждый день в 3:00
    },
}

if __name__ == "__main__":
    celery_app.start()
