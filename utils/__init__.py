"""
Пакет утилит для проекта DailyComicBot.
Содержит модули для логирования, обработки ошибок и планирования задач.
"""

from typing import Dict, Any
from utils.logger import (
    get_logger, debug, info, warning, error, critical, exception, trace, setLevel,
    log_theme, log_script_creation, log_script_evaluation, log_winner_selection,
    log_image_creation, log_publication
)
from utils.error_handler import (
    handle_exceptions, retry_on_api_error, safe_execute, measure_execution_time,
    APIError, OpenAIError, TelegramError, InstagramError, PerplexityError, StorageError
)
from utils.scheduler import (
    scheduler, add_daily_task, add_news_collection_task, add_publication_task,
    start_scheduler, shutdown_scheduler
)

__all__ = [
    # Логирование
    'get_logger', 'debug', 'info', 'warning', 'error', 'critical', 'exception', 'trace', 'setLevel',
    'log_theme', 'log_script_creation', 'log_script_evaluation', 'log_winner_selection',
    'log_image_creation', 'log_publication',
    
    # Обработка ошибок
    'handle_exceptions', 'retry_on_api_error', 'safe_execute', 'measure_execution_time',
    'APIError', 'OpenAIError', 'TelegramError', 'InstagramError', 'PerplexityError', 'StorageError',
    
    # Планирование задач
    'scheduler', 'add_daily_task', 'add_news_collection_task', 'add_publication_task',
    'start_scheduler', 'shutdown_scheduler',
    
]
