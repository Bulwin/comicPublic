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
def get_top_news(force_new=False, exclude_news=None) -> Dict[str, Any]:
    """
    Получение главной новости дня через прямой вызов Perplexity API.
    
    Args:
        force_new (bool): Принудительно получить новую новость, игнорируя кэш.
        exclude_news (Dict[str, Any], optional): Новость, которую нужно исключить из поиска.
    
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
        news = call_perplexity_api_directly(exclude_news=exclude_news)
        
        # Сохраняем полученную новость в файл
        if news:
            from tools.storage_tools import store_news
            store_news(news)
            logger.info("Новость сохранена в файл")
        
        return news
    
    except Exception as e:
        logger.error(f"Ошибка при получении главной новости дня: {str(e)}")
        raise PerplexityError(f"Ошибка при получении главной новости дня: {str(e)}")


def read_prompt_from_file():
    """
    Чтение промпта из файла.
    
    Returns:
        tuple: (system_prompt, user_prompt) - системный промпт и пользовательский запрос.
    """
    default_prompt = """Найди самую важную и обсуждаемую новость сегодня в мире.

ОБЯЗАТЕЛЬНО структурируй ответ в следующем формате:

ЗАГОЛОВОК: [Краткий заголовок новости в одну строку]

СОДЕРЖАНИЕ: [Подробное описание новости - что произошло, где, когда, кто участвует, почему это важно. Минимум 3-4 предложения]"""
    
    default_system_prompt = "Ты журналист, который находит и структурирует главные новости дня. Всегда используй указанный формат с разделами ЗАГОЛОВОК и СОДЕРЖАНИЕ."
    
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


def call_perplexity_api_directly(exclude_news=None) -> Dict[str, Any]:
    """
    Прямой вызов Perplexity API для получения главной новости дня.
    
    Args:
        exclude_news (Dict[str, Any], optional): Новость, которую нужно исключить из поиска.
    
    Returns:
        Dict[str, Any]: Информация о главной новости дня.
        
    Raises:
        PerplexityError: Если произошла ошибка при вызове API.
    """
    if not PERPLEXITY_API_KEY:
        raise PerplexityError("PERPLEXITY_API_KEY не установлен")
    
    # Чтение промпта из файла
    system_prompt, user_prompt = read_prompt_from_file()
    
    # Если нужно исключить определенную новость, добавляем это в промпт
    if exclude_news:
        exclude_title = exclude_news.get('title', '')
        exclude_content = exclude_news.get('content', '')
        
        # Добавляем инструкцию исключить текущую новость
        user_prompt += f"\n\nВАЖНО: Найди ДРУГУЮ новость, НЕ связанную с темой: \"{exclude_title}\""
        if exclude_content:
            # Берем первые 200 символов содержания для контекста
            content_preview = exclude_content[:200] + "..." if len(exclude_content) > 200 else exclude_content
            user_prompt += f"\nИсключи новости на тему: {content_preview}"
        user_prompt += "\nНужна совершенно другая, независимая новость дня."
    
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
                    "content": extract_news_content(content),
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
    Извлечение заголовка новости из структурированного содержимого.
    
    Args:
        content (str): Содержимое новости.
        
    Returns:
        str: Заголовок новости.
    """
    if not content:
        return "Новость дня"
    
    # Поиск заголовка в структурированном формате
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Убираем звездочки в начале и конце строки для поиска
        clean_line = line.strip('*').strip()
        
        # Ищем строку с "ЗАГОЛОВОК:" (новый формат)
        if clean_line.upper().startswith('ЗАГОЛОВОК:') or 'ЗАГОЛОВОК:' in clean_line.upper():
            # Находим позицию двоеточия и берем текст после него
            if ':' in clean_line:
                title = clean_line.split(':', 1)[1].strip()
                if title:
                    # Убираем квадратные скобки если есть
                    title = title.strip('[]').strip('*').strip()
                    logger.info(f"Найден заголовок: '{title}'")
                    return title
        
        # Старые форматы для совместимости
        if any(clean_line.lower().startswith(prefix) for prefix in ['заголовок:', 'новость:', 'главная новость:', 'сегодня:']):
            title = clean_line.split(':', 1)[1].strip()
            if title:
                title = title.strip('[]').strip('*').strip()
                logger.info(f"Найден заголовок (старый формат): '{title}'")
                return title
        
        # Если строка в кавычках
        if line.startswith('"') and line.endswith('"'):
            title = line[1:-1]
            logger.info(f"Найден заголовок в кавычках: '{title}'")
            return title
        
        # Если строка выделена звездочками и содержит двоеточие
        if line.startswith('**') and line.endswith('**') and ':' in line:
            title = line[2:-2]
            logger.info(f"Найден заголовок в звездочках: '{title}'")
            return title
    
    # Если ничего не найдено, берем первое предложение
    sentences = content.split('.')
    if sentences and sentences[0].strip():
        title = sentences[0].strip().strip('*').strip()
        # Ограничиваем длину заголовка
        if len(title) > 100:
            title = title[:97] + "..."
        logger.warning(f"Заголовок не найден, используется первое предложение: '{title}'")
        return title
    
    logger.warning("Заголовок не найден, используется значение по умолчанию")
    return "Новость дня"


def extract_news_content(content: str) -> str:
    """
    Извлечение основного содержания новости из структурированного ответа.
    
    Args:
        content (str): Полное содержимое ответа от Perplexity.
        
    Returns:
        str: Основное содержание новости.
    """
    if not content:
        return content
    
    lines = content.split('\n')
    content_lines = []
    capturing_content = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if capturing_content:
                content_lines.append('')
            continue
        
        # Убираем звездочки для поиска
        clean_line = line.strip('*').strip()
            
        # Начинаем захват после "СОДЕРЖАНИЕ:"
        if clean_line.upper().startswith('СОДЕРЖАНИЕ:'):
            content_text = clean_line.split(':', 1)[1].strip()
            if content_text:
                content_lines.append(content_text.strip('[]').strip('*').strip())
            capturing_content = True
            continue
        
        # Останавливаем захват при следующем разделе
        if capturing_content and any(clean_line.upper().startswith(prefix) for prefix in ['ИСТОЧНИК:', 'ВАЖНОСТЬ:', 'ЗАГОЛОВОК:']):
            break
            
        # Добавляем строки содержания
        if capturing_content:
            # Убираем звездочки из содержания
            clean_content_line = line.strip('*').strip()
            if clean_content_line:
                content_lines.append(clean_content_line)
    
    if content_lines:
        result = '\n'.join(content_lines).strip()
        logger.info(f"Извлечено содержание: '{result[:100]}...'")
        return result
    
    # Если структурированного содержания нет, возвращаем весь контент без заголовка
    logger.warning("Структурированное содержание не найдено, возвращаем весь контент")
    return content
