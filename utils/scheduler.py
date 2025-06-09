"""
Модуль для планирования задач в проекте.
Обеспечивает запуск задач по расписанию с использованием APScheduler.
"""

import os
import sys
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import pytz

# Импорт модулей проекта
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import logger

# Получаем настройки из переменных окружения
TIMEZONE = os.getenv("TIMEZONE", "Europe/Nicosia")
NEWS_COLLECTION_HOUR = int(os.getenv("NEWS_COLLECTION_HOUR", "13"))
NEWS_COLLECTION_MINUTE = int(os.getenv("NEWS_COLLECTION_MINUTE", "0"))
PUBLICATION_TIME_HOUR = int(os.getenv("PUBLICATION_TIME_HOUR", "13"))
PUBLICATION_TIME_MINUTE = int(os.getenv("PUBLICATION_TIME_MINUTE", "15"))


class TaskScheduler:
    """
    Класс для планирования и выполнения задач по расписанию.
    """
    
    def __init__(self):
        """Инициализация планировщика задач."""
        self.scheduler = BackgroundScheduler()
        self.timezone = pytz.timezone(TIMEZONE)
        
        # Добавление обработчика событий для логирования
        self.scheduler.add_listener(
            self._job_listener,
            EVENT_JOB_ERROR | EVENT_JOB_EXECUTED
        )
    
    def _job_listener(self, event):
        """
        Обработчик событий планировщика.
        
        Args:
            event: Событие планировщика.
        """
        if event.exception:
            logger.error(f"Ошибка при выполнении задачи {event.job_id}: {str(event.exception)}")
        else:
            logger.info(f"Задача {event.job_id} успешно выполнена")
    
    def add_daily_task(self, func, hour, minute, job_id=None, **kwargs):
        """
        Добавление ежедневной задачи.
        
        Args:
            func: Функция для выполнения.
            hour (int): Час выполнения.
            minute (int): Минута выполнения.
            job_id (str, optional): Идентификатор задачи. По умолчанию None.
            **kwargs: Дополнительные аргументы для функции.
        """
        trigger = CronTrigger(hour=hour, minute=minute, timezone=self.timezone)
        self.scheduler.add_job(
            func, trigger, id=job_id or func.__name__, kwargs=kwargs,
            replace_existing=True
        )
        logger.info(f"Добавлена ежедневная задача {job_id or func.__name__} на {hour}:{minute} {TIMEZONE}")
    
    def add_news_collection_task(self, func, **kwargs):
        """
        Добавление задачи сбора новостей.
        
        Args:
            func: Функция для выполнения.
            **kwargs: Дополнительные аргументы для функции.
        """
        self.add_daily_task(
            func, NEWS_COLLECTION_HOUR, NEWS_COLLECTION_MINUTE,
            job_id="news_collection", **kwargs
        )
    
    def add_publication_task(self, func, **kwargs):
        """
        Добавление задачи публикации.
        
        Args:
            func: Функция для выполнения.
            **kwargs: Дополнительные аргументы для функции.
        """
        self.add_daily_task(
            func, PUBLICATION_TIME_HOUR, PUBLICATION_TIME_MINUTE,
            job_id="publication", **kwargs
        )
    
    def start(self):
        """Запуск планировщика."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Планировщик задач запущен")
    
    def shutdown(self):
        """Остановка планировщика."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Планировщик задач остановлен")
    
    def get_jobs(self):
        """
        Получение списка запланированных задач.
        
        Returns:
            list: Список запланированных задач.
        """
        return self.scheduler.get_jobs()
    
    def remove_job(self, job_id):
        """
        Удаление задачи по идентификатору.
        
        Args:
            job_id (str): Идентификатор задачи.
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Задача {job_id} удалена")
        except Exception as e:
            logger.error(f"Ошибка при удалении задачи {job_id}: {str(e)}")
    
    def pause_job(self, job_id):
        """
        Приостановка задачи по идентификатору.
        
        Args:
            job_id (str): Идентификатор задачи.
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Задача {job_id} приостановлена")
        except Exception as e:
            logger.error(f"Ошибка при приостановке задачи {job_id}: {str(e)}")
    
    def resume_job(self, job_id):
        """
        Возобновление задачи по идентификатору.
        
        Args:
            job_id (str): Идентификатор задачи.
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Задача {job_id} возобновлена")
        except Exception as e:
            logger.error(f"Ошибка при возобновлении задачи {job_id}: {str(e)}")


# Создание экземпляра планировщика при импорте модуля
scheduler = TaskScheduler()


# Функции-обертки для удобства использования
def add_daily_task(func, hour, minute, job_id=None, **kwargs):
    """Добавление ежедневной задачи."""
    scheduler.add_daily_task(func, hour, minute, job_id, **kwargs)


def add_news_collection_task(func, **kwargs):
    """Добавление задачи сбора новостей."""
    scheduler.add_news_collection_task(func, **kwargs)


def add_publication_task(func, **kwargs):
    """Добавление задачи публикации."""
    scheduler.add_publication_task(func, **kwargs)


def start_scheduler():
    """Запуск планировщика."""
    scheduler.start()


def shutdown_scheduler():
    """Остановка планировщика."""
    scheduler.shutdown()
