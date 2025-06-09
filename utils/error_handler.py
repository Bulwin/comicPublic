"""
Модуль для обработки ошибок в проекте.
Предоставляет декораторы и функции для обработки исключений и повторных попыток выполнения.
"""

import functools
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import sys
from pathlib import Path

# Импорт модуля логирования
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import logger


class APIError(Exception):
    """Базовый класс для ошибок API."""
    pass


class OpenAIError(APIError):
    """Ошибка при работе с OpenAI API."""
    pass


class TelegramError(APIError):
    """Ошибка при работе с Telegram API."""
    pass


class InstagramError(APIError):
    """Ошибка при работе с Instagram API."""
    pass


class PerplexityError(APIError):
    """Ошибка при работе с Perplexity API."""
    pass


class StorageError(Exception):
    """Ошибка при работе с хранилищем данных."""
    pass


def handle_exceptions(func):
    """
    Декоратор для обработки исключений.
    Логирует исключение и возвращает None в случае ошибки.
    
    Args:
        func: Декорируемая функция.
        
    Returns:
        Функция-обертка, которая обрабатывает исключения.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Ошибка в функции {func.__name__}: {str(e)}")
            return None
    return wrapper


def retry_on_api_error(max_attempts=3, min_wait=1, max_wait=10):
    """
    Декоратор для повторных попыток выполнения функции при ошибках API.
    
    Args:
        max_attempts (int): Максимальное количество попыток.
        min_wait (int): Минимальное время ожидания между попытками (в секундах).
        max_wait (int): Максимальное время ожидания между попытками (в секундах).
        
    Returns:
        Декоратор для повторных попыток.
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(APIError),
        before_sleep=lambda retry_state: logger.warning(
            f"Повторная попытка {retry_state.attempt_number}/{max_attempts} "
            f"после ошибки: {retry_state.outcome.exception()}"
        ),
        reraise=True
    )


def safe_execute(func, default_value=None, log_error=True, *args, **kwargs):
    """
    Безопасное выполнение функции с обработкой исключений.
    
    Args:
        func: Функция для выполнения.
        default_value: Значение, возвращаемое в случае ошибки.
        log_error (bool): Флаг, указывающий, нужно ли логировать ошибку.
        *args: Позиционные аргументы для функции.
        **kwargs: Именованные аргументы для функции.
        
    Returns:
        Результат выполнения функции или default_value в случае ошибки.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.exception(f"Ошибка при выполнении {func.__name__}: {str(e)}")
        return default_value


def measure_execution_time(func):
    """
    Декоратор для измерения времени выполнения функции.
    
    Args:
        func: Декорируемая функция.
        
    Returns:
        Функция-обертка, которая измеряет время выполнения.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.debug(f"Функция {func.__name__} выполнена за {execution_time:.2f} секунд")
        return result
    return wrapper
