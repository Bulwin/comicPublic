"""
Модуль для настройки системы логирования проекта.
Обеспечивает единый интерфейс для логирования во всех компонентах системы.
Реализован в соответствии с правилами из logging_system.md.
"""

import logging
import sys
import os
import time
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import threading
from queue import Queue
from typing import List

# Импорт конфигурации
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, LOGS_DIR


# Константы для уровней логирования
TRACE = 5  # Добавляем уровень TRACE (ниже DEBUG)
logging.addLevelName(TRACE, "TRACE")


# Очередь для асинхронного логирования
log_queue = Queue()


class AsyncHandler(logging.Handler):
    """
    Обработчик для асинхронного логирования.
    Записывает сообщения в очередь, которая обрабатывается в отдельном потоке.
    """
    
    def __init__(self, handlers):
        """
        Инициализация обработчика.
        
        Args:
            handlers (list): Список обработчиков для записи сообщений.
        """
        super().__init__()
        self.handlers = handlers
        self.queue = log_queue
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
                for handler in self.handlers:
                    if record.levelno >= handler.level:
                        handler.emit(record)
                self.queue.task_done()
            except Exception:
                import traceback
                print(f"Ошибка в потоке логирования: {traceback.format_exc()}")


class CustomFormatter(logging.Formatter):
    """
    Пользовательский форматтер для логов.
    Добавляет информацию о потоке и цветовое форматирование для консоли.
    """
    
    # Цвета для разных уровней логирования (для консоли)
    COLORS = {
        'TRACE': '\033[90m',     # Серый
        'DEBUG': '\033[36m',     # Голубой
        'INFO': '\033[32m',      # Зеленый
        'WARNING': '\033[33m',   # Желтый
        'ERROR': '\033[31m',     # Красный
        'CRITICAL': '\033[41m',  # Красный фон
        'RESET': '\033[0m'       # Сброс цвета
    }
    
    def __init__(self, fmt=None, datefmt=None, style='%', use_colors=False):
        """
        Инициализация форматтера.
        
        Args:
            fmt (str, optional): Формат сообщения.
            datefmt (str, optional): Формат даты.
            style (str, optional): Стиль форматирования.
            use_colors (bool, optional): Использовать цветовое форматирование.
        """
        super().__init__(fmt, datefmt, style)
        self.use_colors = use_colors
    
    def format(self, record):
        """
        Форматирование записи.
        
        Args:
            record: Запись логирования.
            
        Returns:
            str: Отформатированное сообщение.
        """
        # Добавление информации о потоке
        record.threadName = threading.current_thread().name
        
        # Форматирование с помощью базового класса
        message = super().format(record)
        
        # Добавление цветов для консоли
        if self.use_colors:
            levelname = record.levelname
            if levelname in self.COLORS:
                message = f"{self.COLORS[levelname]}{message}{self.COLORS['RESET']}"
        
        return message


def trace(msg, *args, **kwargs):
    """
    Логирование сообщения с уровнем TRACE.
    
    Args:
        msg: Сообщение для логирования.
        *args: Позиционные аргументы.
        **kwargs: Именованные аргументы.
    """
    root_logger.log(TRACE, msg, *args, **kwargs)


def clear_logs():
    """
    Очистка старых логов.
    """
    try:
        # Очистка основного лог-файла
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'w') as f:
                f.write("")
            info("Основной лог-файл очищен")
        
        # Очистка ежедневного лог-файла
        daily_log_file = LOGS_DIR / f"daily_{datetime.now().strftime('%Y-%m-%d')}.log"
        if os.path.exists(daily_log_file):
            with open(daily_log_file, 'w') as f:
                f.write("")
            info("Ежедневный лог-файл очищен")
    except Exception as e:
        print(f"Ошибка при очистке логов: {str(e)}")


def setup_logger(name=None, level=None, clear_old_logs=False):
    """
    Настройка и получение логгера.
    
    Args:
        name (str, optional): Имя логгера. По умолчанию None (корневой логгер).
        level (int, optional): Уровень логирования. По умолчанию None (из конфигурации).
        clear_old_logs (bool, optional): Очистить старые логи. По умолчанию False.
    
    Returns:
        logging.Logger: Настроенный логгер.
    """
    # Создание директории для логов, если она не существует
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Очистка старых логов, если требуется
    if clear_old_logs and name is None:
        # Очищаем логи только для корневого логгера
        clear_logs()
    
    # Получение логгера
    logger = logging.getLogger(name)
    
    # Установка уровня логирования
    logger.setLevel(level or LOG_LEVEL)
    
    # Если обработчики уже добавлены, не добавляем новые
    if logger.handlers:
        return logger
    
    # Создание обработчиков
    handlers = []
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = CustomFormatter(LOG_FORMAT, use_colors=True)
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)
    
    # Обработчик для записи в файл с ротацией по размеру
    # Максимальный размер файла - 10 МБ, хранить до 5 файлов
    size_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    size_formatter = CustomFormatter(LOG_FORMAT)
    size_handler.setFormatter(size_formatter)
    handlers.append(size_handler)
    
    # Обработчик для записи в файл с ротацией по времени (ежедневно)
    daily_log_file = LOGS_DIR / f"daily_{datetime.now().strftime('%Y-%m-%d')}.log"
    time_handler = TimedRotatingFileHandler(
        daily_log_file, when='midnight', interval=1, backupCount=30, encoding='utf-8'
    )
    time_formatter = CustomFormatter(LOG_FORMAT)
    time_handler.setFormatter(time_formatter)
    handlers.append(time_handler)
    
    # Создание асинхронного обработчика
    async_handler = AsyncHandler(handlers)
    logger.addHandler(async_handler)
    
    return logger


# Создание корневого логгера при импорте модуля
root_logger = setup_logger()


def get_logger(name=None):
    """
    Получение логгера с заданным именем.
    
    Args:
        name (str, optional): Имя логгера. По умолчанию None (корневой логгер).
    
    Returns:
        logging.Logger: Логгер с заданным именем.
    """
    if name is None:
        return root_logger
    
    return setup_logger(name)


# Функции-обертки для удобства использования
def debug(msg, *args, **kwargs):
    """Логирование сообщения с уровнем DEBUG."""
    root_logger.debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """Логирование сообщения с уровнем INFO."""
    root_logger.info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """Логирование сообщения с уровнем WARNING."""
    root_logger.warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """Логирование сообщения с уровнем ERROR."""
    root_logger.error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """Логирование сообщения с уровнем CRITICAL."""
    root_logger.critical(msg, *args, **kwargs)


def exception(msg, *args, exc_info=True, **kwargs):
    """Логирование исключения с трассировкой стека."""
    root_logger.exception(msg, *args, exc_info=exc_info, **kwargs)


def setLevel(level):
    """
    Установка уровня логирования для корневого логгера.
    
    Args:
        level: Уровень логирования (например, logging.DEBUG, logging.INFO и т.д.).
    """
    root_logger.setLevel(level)


# Специальные функции логирования для проекта DailyComicBot
def log_theme(theme: str):
    """
    Логирование выбранной темы.
    
    Args:
        theme (str): Выбранная тема.
    """
    info(f"Выбранная тема: {theme}")


def log_script_creation(writer_name: str, script_id: str, title: str):
    """
    Логирование создания сценария.
    
    Args:
        writer_name (str): Имя сценариста.
        script_id (str): Идентификатор сценария.
        title (str): Заголовок сценария.
    """
    info(f"Сценарист '{writer_name}' создал сценарий '{script_id}': {title}")


def log_script_evaluation(jury_name: str, script_id: str, score: float):
    """
    Логирование оценки сценария.
    
    Args:
        jury_name (str): Имя члена жюри.
        script_id (str): Идентификатор сценария.
        score (float): Оценка.
    """
    info(f"Жюри '{jury_name}' оценил сценарий '{script_id}' на {score}/100")


def log_winner_selection(script_id: str, title: str, score: float):
    """
    Логирование выбора победителя.
    
    Args:
        script_id (str): Идентификатор сценария-победителя.
        title (str): Заголовок сценария-победителя.
        score (float): Средняя оценка.
    """
    info(f"Выбран победитель: сценарий '{script_id}' ({title}) с оценкой {score:.2f}/100")


def log_image_creation(script_id: str, image_path: str):
    """
    Логирование создания изображения.
    
    Args:
        script_id (str): Идентификатор сценария.
        image_path (str): Путь к созданному изображению.
    """
    info(f"Создано изображение для сценария '{script_id}': {image_path}")


def log_publication(platforms: List[str], image_path: str):
    """
    Логирование публикации.
    
    Args:
        platforms (List[str]): Список платформ, на которых опубликован комикс.
        image_path (str): Путь к опубликованному изображению.
    """
    info(f"Комикс опубликован на платформах: {', '.join(platforms)}. Изображение: {image_path}")
