"""
Модуль инструментов для работы с новостями.
Предоставляет функции для получения главной новости дня через прямой вызов Perplexity API.
"""

import sys
from pathlib import Path
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

# Импорт модулей проекта
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import logger, handle_exceptions, retry_on_api_error, PerplexityError
from config import PERPLEXITY_API_KEY


@handle_exceptions
@retry_on_api_error(max_attempts=3)
def get_top_news(force_new=False) -> Dict[str, Any]:
    """
    Получение главной новости дня через прямой вызов Perplexity API.
    
    Args:
        force_new (bool): Принудительно получить новую новость, игнорируя кэш.
    
    Returns:
        Dict[str, Any]: Информация о главной новости дня.
        
    Raises:
        PerplexityError: Если произошла ошибка при получении новости.
    """
    try:
        # Если не принудительное обновление, проверяем существующую новость
        if not force_new:
            from tools.storage_tools import load_news
            existing_news = load_news()
            if existing_news:
                logger.info("Используется существующая новость дня")
                return existing_news
        
        # Прямой вызов Perplexity API
        logger.info("Получение новой новости через Perplexity API")
        return call_perplexity_api_directly()
    
    except Exception as e:
        logger.error(f"Ошибка при получении главной новости дня: {str(e)}")
        raise PerplexityError(f"Ошибка при получении главной новости дня: {str(e)}")


def read_prompt_from_file():
    """
    Чтение промпта из файла.
    
    Returns:
        tuple: (system_prompt, user_prompt) - системный промпт и пользовательский запрос.
    """
    default_prompt = "Какая самая важная и обсуждаемая новость сегодня в мире? Дай краткое описание новости, ее источник и почему она важна."
    default_system_prompt = "Найди и кратко сформулируй главную новость дня на текущую дату. Укажи источник."
    
    try:
        # Попытка чтения промпта из файла
        prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "perplexity_news_prompt.txt"
        
        if prompt_path.exists():
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    
                    # Разделение на системный промпт и пользовательский запрос
                    lines = content.split("\n\n", 1)
                    
                    if len(lines) > 1:
                        system_prompt = lines[0].strip()
                        user_prompt = lines[1].strip()
                        return system_prompt, user_prompt
                    else:
                        # Если нет разделения, используем весь контент как пользовательский запрос
                        return default_system_prompt, content
            except Exception as e:
                logger.warning(f"Ошибка при чтении файла с промптом: {str(e)}")
                return default_system_prompt, default_prompt
        
        # Если файл не существует, возвращаем значения по умолчанию
        logger.warning(f"Файл с промптом не найден: {prompt_path}")
        return default_system_prompt, default_prompt
    
    except Exception as e:
        # В случае ошибки возвращаем значения по умолчанию
        logger.error(f"Ошибка при чтении промпта из файла: {str(e)}")
        return default_system_prompt, default_prompt


def call_perplexity_api_directly() -> Dict[str, Any]:
    """
    Прямой вызов Perplexity API для получения главной новости дня.
    
    Returns:
        Dict[str, Any]: Информация о главной новости дня.
        
    Raises:
        PerplexityError: Если произошла ошибка при вызове API.
    """
    if not PERPLEXITY_API_KEY:
        raise PerplexityError("PERPLEXITY_API_KEY не установлен")
    
    # Чтение промпта из файла
    system_prompt, user_prompt = read_prompt_from_file()
    
    # ЛОГИРОВАНИЕ ОТПРАВЛЯЕМОГО ЗАПРОСА
    logger.info("=== ОТПРАВЛЯЕМЫЙ ЗАПРОС К PERPLEXITY API ===")
    logger.info(f"System prompt: {system_prompt}")
    logger.info(f"User prompt: {user_prompt}")
    logger.info("==========================================")
    
    # Подготовка запроса к Perplexity API
    headers = {
        'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': 'llama-3.1-sonar-large-128k-online',
        'messages': [
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': user_prompt
            }
        ],
        'max_tokens': 1000,
        'temperature': 0.5,  # Умеренная температура для разнообразия без хаоса
        'top_p': 0.9,
        'return_citations': True,
        'return_images': False,
        'return_related_questions': False,
        'search_recency_filter': "day",
        'top_k': 0,
        'stream': False,
        'presence_penalty': 0,
        'frequency_penalty': 1
    }
    
    try:
        logger.info("Отправка запроса к Perplexity API...")
        logger.info(f"Полный payload: {payload}")
        
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ОТВЕТА ОТ PERPLEXITY API
            logger.info("=== ПОЛНЫЙ ОТВЕТ ОТ PERPLEXITY API ===")
            logger.info(f"Статус код: {response.status_code}")
            logger.info(f"Полный JSON ответ: {data}")
            logger.info("=====================================")
            
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                
                logger.info(f"Извлеченный контент: {content}")
                logger.info(f"Цитаты в ответе: {data.get('citations', [])}")
                
                # Формирование результата
                result = {
                    "date": datetime.now().isoformat(),
                    "title": extract_title(content),
                    "content": content,
                    "source": "Perplexity API",
                    "citations": data.get('citations', [])
                }
                
                logger.info(f"Получена главная новость дня: {result['title']}")
                return result
            else:
                logger.error(f"Пустой ответ от Perplexity API. Полный ответ: {data}")
                raise PerplexityError("Пустой ответ от Perplexity API")
        
        elif response.status_code == 401:
            raise PerplexityError("Неверный API ключ Perplexity")
        elif response.status_code == 429:
            raise PerplexityError("Превышен лимит запросов к Perplexity API")
        else:
            raise PerplexityError(f"Ошибка API Perplexity: {response.status_code} - {response.text}")
    
    except requests.exceptions.Timeout:
        raise PerplexityError("Таймаут при обращении к Perplexity API")
    except requests.exceptions.ConnectionError:
        raise PerplexityError("Ошибка соединения с Perplexity API")
    except requests.exceptions.RequestException as e:
        raise PerplexityError(f"Ошибка запроса к Perplexity API: {str(e)}")
    except Exception as e:
        raise PerplexityError(f"Неожиданная ошибка при вызове Perplexity API: {str(e)}")


def extract_title(content: str) -> str:
    """
    Извлечение заголовка новости из содержимого.
    
    Args:
        content (str): Содержимое новости.
        
    Returns:
        str: Заголовок новости.
    """
    if not content:
        return "Новость дня"
    
    # Поиск заголовка в различных форматах
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Если строка начинается с "Заголовок:", "Новость:", "Главная новость:" и т.д.
        if any(line.lower().startswith(prefix) for prefix in ['заголовок:', 'новость:', 'главная новость:', 'сегодня:']):
            title = line.split(':', 1)[1].strip()
            if title:
                return title
        
        # Если строка в кавычках
        if line.startswith('"') and line.endswith('"'):
            return line[1:-1]
        
        # Если строка выделена звездочками
        if line.startswith('**') and line.endswith('**'):
            return line[2:-2]
    
    # Если ничего не найдено, берем первое предложение
    sentences = content.split('.')
    if sentences and sentences[0].strip():
        title = sentences[0].strip()
        # Ограничиваем длину заголовка
        if len(title) > 100:
            title = title[:97] + "..."
        return title
    
    return "Новость дня"
