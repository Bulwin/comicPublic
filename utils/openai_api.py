"""
Модуль для работы с OpenAI API.
Предоставляет функции для генерации текста и изображений.
"""

import os
import json
import logging
import traceback
import time
import functools
from typing import Dict, Any, List, Callable
from datetime import datetime

# Настройка логирования
logger = logging.getLogger(__name__)

def measure_execution_time(func: Callable) -> Callable:
    """
    Декоратор для измерения времени выполнения функции.
    
    Args:
        func (Callable): Функция для измерения времени выполнения.
        
    Returns:
        Callable: Обернутая функция.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Функция {func.__name__} выполнена за {execution_time:.2f} секунд")
        return result
    return wrapper

def call_openai_api(model: str, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 1000, frequency_penalty: float = 0.0) -> Dict[str, Any]:
    """
    Вызов OpenAI API для генерации текста.
    
    Args:
        model (str): Модель OpenAI (например, "gpt-4").
        messages (List[Dict[str, str]]): Сообщения для модели.
        temperature (float, optional): Температура генерации. По умолчанию 0.7.
        max_tokens (int, optional): Максимальное количество токенов. По умолчанию 1000.
        frequency_penalty (float, optional): Штраф за повторение. По умолчанию 0.0.
        
    Returns:
        Dict[str, Any]: Результат вызова API.
        
    Raises:
        Exception: Если не удалось получить ответ от OpenAI API.
    """
    try:
        # Получение промпта из сообщений для логирования
        prompt = ""
        for message in messages:
            if message.get("role") == "user":
                prompt = message.get("content", "")
                break
        
        # Получение системного промпта для логирования
        system_prompt = ""
        for message in messages:
            if message.get("role") == "system":
                system_prompt = message.get("content", "")
                break
        
        logger.info(f"Вызов OpenAI API: {model}")
        logger.info(f"Системный промпт: {system_prompt[:100]}...")
        logger.info(f"Пользовательский промпт: {prompt[:100]}...")
        
        # Используем сообщения без изменений, так как формат задается в настройках ассистента на платформе OpenAI
        modified_messages = messages.copy()
        
        try:
            # OpenAI API не настроен, используем заглушку
            logger.warning("OpenAI API не настроен, используется заглушка")
            response = {
                "content": "Заглушка: ответ от OpenAI API недоступен"
            }
            
            # Проверка наличия ответа
            if response and "content" in response:
                content = response["content"]
                
                # Проверка, что ответ не является заглушкой
                if "Это ответ от заглушки OpenAI API" in content:
                    # Если получена заглушка, выдаем ошибку
                    error_msg = "Получен ответ от заглушки OpenAI API. Необходимо использовать реальный API."
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                # Проверка, что ответ не является пустым или слишком коротким
                if not content or len(content.strip()) < 100:
                    error_msg = "Получен слишком короткий ответ от OpenAI API"
                    logger.error(error_msg)
                    logger.error(f"Ответ: {content}")
                    raise Exception(error_msg)
                
                logger.info(f"Получен ответ от OpenAI API: {content[:100]}...")
                return response
            
            # Если не удалось получить ответ от API
            error_msg = "Не удалось получить ответ от OpenAI API"
            logger.error(error_msg)
            if "error" in response:
                logger.error(f"Ошибка: {response['error']}")
            raise Exception(error_msg)
            
        except Exception as e:
            # В случае ошибки
            error_msg = f"Ошибка при вызове OpenAI API: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Стек вызовов:\n{traceback.format_exc()}")
            raise Exception(error_msg)
    
    except Exception as e:
        error_msg = f"Ошибка при вызове API: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Стек вызовов:\n{traceback.format_exc()}")
        raise Exception(error_msg)
