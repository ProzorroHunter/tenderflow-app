from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

load_dotenv()

# Настройка Celery с Redis
celery_app = Celery(
    "prozorrohunter",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=["tasks"]  # Указываем, где искать задачи
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Kiev",  # Украинское время
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут лимит на задачу
    worker_prefetch_multiplier=1,  # По одной задаче за раз
)

# Настройка периодических задач (beat schedule)
celery_app.conf.beat_schedule = {
    "check-new-tenders-every-10-min": {
        "task": "tasks.check_new_tenders",
        "schedule": 600.0,  # Каждые 10 минут (в секундах)
    },
}

@celery_app.task(bind=True)
def debug_task(self):
    """Тестовая задача для проверки работы Celery"""
    print(f"Request: {self.request!r}")
    return "Celery работает!"
