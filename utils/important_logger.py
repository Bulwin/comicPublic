"""
Модуль для логирования только самых важных событий в проекте DailyComicBot.
Создает отдельный лог-файл, в который записываются только ключевые события с датой и временем.
"""

import logging
import sys
import os
import re
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
import threading
from queue import Queue

# Импорт конфигурации
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import LOGS_DIR

# Константы
IMPORTANT_LOG_FILE = LOGS_DIR / "important_events.log"

# Создание директории для логов, если она не существует
os.makedirs(LOGS_DIR, exist_ok=True)

# Очередь для асинхронного логирования
important_log_queue = Queue()


class AsyncImportantHandler(logging.Handler):
    """
    Обработчик для асинхронного логирования важных событий.
    Записывает сообщения в очередь, которая обрабатывается в отдельном потоке.
    """
    
    def __init__(self, handler):
        """
        Инициализация обработчика.
        
        Args:
            handler: Обработчик для записи сообщений.
        """
        super().__init__()
        self.handler = handler
        self.queue = important_log_queue
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
    
    def emit(self, record):
        """
        Добавление записи в очередь.
        
        Args:
            record: Запись логирования.
        """
        self.queue.put(record)
    
    def _process_queue(self):
        """Обработка очереди сообщений в отдельном потоке."""
        while True:
            try:
                record = self.queue.get()
                self.handler.emit(record)
                self.queue.task_done()
            except Exception:
                import traceback
                print(f"Ошибка в потоке логирования важных событий: {traceback.format_exc()}")


class ImportantFormatter(logging.Formatter):
    """
    Форматтер для важных событий.
    Форматирует сообщения с датой и временем.
    """
    
    def __init__(self):
        """Инициализация форматтера."""
        super().__init__('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


# Создание логгера для важных событий
important_logger = logging.getLogger('important_events')
important_logger.setLevel(logging.INFO)

# Создание обработчика для записи в файл
important_handler = RotatingFileHandler(
    IMPORTANT_LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
)
important_formatter = ImportantFormatter()
important_handler.setFormatter(important_formatter)

# Создание асинхронного обработчика
async_important_handler = AsyncImportantHandler(important_handler)
important_logger.addHandler(async_important_handler)

# Отключение передачи сообщений родительским логгерам
important_logger.propagate = False


# Функция для обрезания длинных строк
def truncate_text(text, max_length=100):
    """
    Обрезание длинного текста до указанной длины.
    
    Args:
        text (str): Текст для обрезания.
        max_length (int, optional): Максимальная длина текста. По умолчанию 100.
        
    Returns:
        str: Обрезанный текст.
    """
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text


# Функции для логирования важных событий
def log_perplexity_request():
    """Логирование запроса в Perplexity на новость дня."""
    important_logger.info("Ушел запрос в перплексити на новость дня")


def log_perplexity_response(news):
    """
    Логирование получения ответа от Perplexity с новостью.
    
    Args:
        news (dict): Информация о новости.
    """
    title = news.get('title', 'Без заголовка')
    content = news.get('content', 'Без содержания')
    
    # Не обрезаем заголовок и содержание новости
    important_logger.info(f"Получен ответ от перплексити с новостью: {title}")
    important_logger.info(f"Содержание новости: {content}")


def log_scriptwriter_request(writer_type, writer_name):
    """
    Логирование запроса на шутку к автору.
    
    Args:
        writer_type (str): Тип сценариста (A, B, C, D, E).
        writer_name (str): Имя сценариста.
    """
    important_logger.info(f"Ушел запрос на шутку к автору {writer_name} (тип {writer_type})")


def log_scriptwriter_response(writer_type, writer_name, script):
    """
    Логирование получения ответа от автора.
    
    Args:
        writer_type (str): Тип сценариста (A, B, C, D, E).
        writer_name (str): Имя сценариста.
        script (dict): Сценарий комикса.
    """
    title = script.get('title', 'Без заголовка')
    script_id = script.get('script_id', 'Без ID')
    
    # Не обрезаем заголовок
    important_logger.info(f"Получен ответ от автора {writer_name} (тип {writer_type}): {title} (ID: {script_id})")


def log_jury_request(jury_type, jury_name, script_id, writer_name):
    """
    Логирование отправки запроса в жюри на оценку шутки от автора.
    
    Args:
        jury_type (str): Тип жюри (A, B, C, D, E).
        jury_name (str): Имя члена жюри.
        script_id (str): Идентификатор сценария.
        writer_name (str): Имя автора сценария.
    """
    important_logger.info(f"Отправлен запрос в жюри {jury_name} (тип {jury_type}) на оценку шутки от автора {writer_name} (ID: {script_id})")


def log_jury_response(jury_type, jury_name, script_id, writer_name, score):
    """
    Логирование получения оценки от члена жюри.
    
    Args:
        jury_type (str): Тип жюри (A, B, C, D, E).
        jury_name (str): Имя члена жюри.
        script_id (str): Идентификатор сценария.
        writer_name (str): Имя автора сценария.
        score (float): Оценка.
    """
    important_logger.info(f"Оценка члена жюри {jury_name} (тип {jury_type}) для автора {writer_name} (ID: {script_id}): {score}/100")


def log_winner_selection(script_id, writer_name, title, score):
    """
    Логирование выбора победителя.
    
    Args:
        script_id (str): Идентификатор сценария-победителя.
        writer_name (str): Имя автора сценария-победителя.
        title (str): Заголовок сценария-победителя.
        score (float): Средняя оценка.
    """
    # Не обрезаем заголовок
    important_logger.info(f"Выбран победитель: сценарий '{title}' (ID: {script_id}) от автора {writer_name} с оценкой {score:.2f}/100")


def log_image_creation(script_id, writer_name, image_path):
    """
    Логирование создания изображения.
    
    Args:
        script_id (str): Идентификатор сценария.
        writer_name (str): Имя автора сценария.
        image_path (str): Путь к созданному изображению.
    """
    important_logger.info(f"Создано изображение для сценария от автора {writer_name} (ID: {script_id}): {image_path}")


def log_publication(platforms, image_path):
    """
    Логирование публикации.
    
    Args:
        platforms (list): Список платформ, на которых опубликован комикс.
        image_path (str): Путь к опубликованному изображению.
    """
    important_logger.info(f"Комикс опубликован на платформах: {', '.join(platforms)}. Изображение: {image_path}")


def log_scheduled_task_start(task_name):
    """
    Логирование начала запланированной задачи.
    
    Args:
        task_name (str): Название задачи.
    """
    important_logger.info(f"🕐 Запуск запланированной задачи: {task_name}")


def log_scheduled_task_complete(task_name):
    """
    Логирование завершения запланированной задачи.
    
    Args:
        task_name (str): Название задачи.
    """
    important_logger.info(f"✅ Завершена запланированная задача: {task_name}")


def log_error(context, error_message):
    """
    Логирование ошибки.
    
    Args:
        context (str): Контекст, в котором произошла ошибка.
        error_message (str): Сообщение об ошибке.
    """
    important_logger.error(f"❌ Ошибка в {context}: {error_message}")


def log_publication_success(channel_id, post_id, script_title, average_score):
    """
    Логирование успешной публикации в канал.
    
    Args:
        channel_id (str): ID канала.
        post_id (str): ID поста.
        script_title (str): Заголовок сценария.
        average_score (float): Средняя оценка.
    """
    important_logger.info(f"📤 Успешная публикация в канал {channel_id}, пост {post_id}: '{script_title}' (оценка: {average_score:.1f}/100)")
