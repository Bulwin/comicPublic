"""
Модуль для прямых вызовов к различным LLM API.
Поддерживает: OpenAI GPT, Google Gemini, Anthropic Claude.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils import logger
from utils.runtime_settings import get_setting, get_content_mode
import config

# Пути к промптам
PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "scriptwriter_system_prompt.txt"
SIMPLE_IMAGE_PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "simple_image_prompt.txt"


def load_system_prompt(writer_type: str, content_mode: str = None) -> str:
    """
    Загружает и форматирует системный промпт для сценариста.
    
    Args:
        writer_type: Тип сценариста (A, B, C, D, E)
        
    Returns:
        str: Отформатированный промпт
    """
    writer_info = config.SCRIPTWRITERS.get(writer_type, {})
    
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    return prompt_template.format(
        writer_name=writer_info.get("name", "Сценарист"),
        writer_description=writer_info.get("description", "")
    )


def format_news_message(news: Dict[str, Any]) -> str:
    """
    Форматирует новость для отправки в LLM.
    
    Args:
        news: Словарь с новостью
        
    Returns:
        str: Форматированный текст новости
    """
    title = news.get('title', 'Без заголовка')
    content = news.get('content', '')
    
    return f"""Создай сценарий комикса на основе этой новости:

**Заголовок новости:** {title}

**Содержание:**
{content}

Создай креативный и юмористический сценарий комикса из 4 панелей. Ответ ТОЛЬКО в JSON формате!"""


def parse_json_response(response_text: str) -> Dict[str, Any]:
    """
    Парсит JSON из ответа LLM (может быть обернут в markdown).
    
    Args:
        response_text: Текст ответа
        
    Returns:
        Dict: Распарсенный JSON
    """
    # Убираем markdown блоки если есть
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = response_text.strip()
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        logger.error(f"Текст ответа: {response_text[:500]}")
        raise ValueError(f"Не удалось распарсить JSON: {e}")


# ============================================================================
# OpenAI GPT Client
# ============================================================================

def invoke_gpt(news: Dict[str, Any], writer_type: str) -> Dict[str, Any]:
    """
    Вызывает OpenAI GPT API для генерации сценария.
    
    Args:
        news: Словарь с новостью
        writer_type: Тип сценариста
        
    Returns:
        Dict: Сгенерированный сценарий
    """
    from openai import OpenAI
    
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    model = get_setting("gpt_model", config.GPT_DIRECT_MODEL)
    
    system_prompt = load_system_prompt(writer_type)
    user_message = format_news_message(news)
    
    logger.info(f"Вызов GPT API (модель: {model}) для сценариста {writer_type}")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.8,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content
        script = parse_json_response(response_text)
        
        logger.info(f"GPT API успешно вернул сценарий: {script.get('title', 'Без названия')}")
        return script
        
    except Exception as e:
        logger.error(f"Ошибка GPT API: {e}")
        raise


# ============================================================================
# Google Gemini Client
# ============================================================================

def invoke_gemini(news: Dict[str, Any], writer_type: str) -> Dict[str, Any]:
    """
    Вызывает Google Gemini API для генерации сценария.
    
    Args:
        news: Словарь с новостью
        writer_type: Тип сценариста
        
    Returns:
        Dict: Сгенерированный сценарий
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("Установите google-generativeai: pip install google-generativeai")
    
    api_key = config.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY не установлен в .env")
    
    genai.configure(api_key=api_key)
    model_name = get_setting("gemini_model", config.GEMINI_MODEL)
    
    system_prompt = load_system_prompt(writer_type)
    user_message = format_news_message(news)
    
    logger.info(f"Вызов Gemini API (модель: {model_name}) для сценариста {writer_type}")
    
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt
        )
        
        response = model.generate_content(
            user_message,
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,
                max_output_tokens=2000
            )
        )
        
        response_text = response.text
        script = parse_json_response(response_text)
        
        logger.info(f"Gemini API успешно вернул сценарий: {script.get('title', 'Без названия')}")
        return script
        
    except Exception as e:
        logger.error(f"Ошибка Gemini API: {e}")
        raise


# ============================================================================
# Anthropic Claude Client
# ============================================================================

def invoke_claude(news: Dict[str, Any], writer_type: str) -> Dict[str, Any]:
    """
    Вызывает Anthropic Claude API для генерации сценария.
    
    Args:
        news: Словарь с новостью
        writer_type: Тип сценариста
        
    Returns:
        Dict: Сгенерированный сценарий
    """
    try:
        import anthropic
    except ImportError:
        raise ImportError("Установите anthropic: pip install anthropic")
    
    api_key = config.ANTHROPIC_API_KEY
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY не установлен в .env")
    
    client = anthropic.Anthropic(api_key=api_key)
    model = get_setting("claude_model", config.CLAUDE_MODEL)
    
    system_prompt = load_system_prompt(writer_type)
    user_message = format_news_message(news)
    
    logger.info(f"Вызов Claude API (модель: {model}) для сценариста {writer_type}")
    
    try:
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        response_text = response.content[0].text
        script = parse_json_response(response_text)
        
        logger.info(f"Claude API успешно вернул сценарий: {script.get('title', 'Без названия')}")
        return script
        
    except Exception as e:
        logger.error(f"Ошибка Claude API: {e}")
        raise


# ============================================================================
# Универсальный клиент
# ============================================================================

def invoke_llm(news: Dict[str, Any], writer_type: str, mode: Optional[str] = None) -> Dict[str, Any]:
    """
    Универсальная функция вызова LLM в зависимости от режима.
    
    Args:
        news: Словарь с новостью
        writer_type: Тип сценариста
        mode: Режим генерации (если None - берется из настроек)
        
    Returns:
        Dict: Сгенерированный сценарий
    """
    if mode is None:
        mode = get_setting("generation_mode", "assistants")
    
    logger.info(f"invoke_llm: режим={mode}, сценарист={writer_type}")
    
    if mode == "assistants":
        # Используем Assistants API (текущий режим)
        from utils.assistants_api import invoke_scriptwriter
        return invoke_scriptwriter(news, writer_type)
    
    elif mode == "gpt":
        return invoke_gpt(news, writer_type)
    
    elif mode == "gemini":
        return invoke_gemini(news, writer_type)
    
    elif mode == "claude":
        return invoke_claude(news, writer_type)
    
    else:
        raise ValueError(f"Неизвестный режим генерации: {mode}")


# ============================================================================
# РЕЖИМ SIMPLE_IMAGE - Шутка + картинка + анекдот
# ============================================================================

def load_simple_image_prompt(writer_type: str) -> str:
    """
    Загружает промпт для режима simple_image.
    
    Args:
        writer_type: Тип сценариста (A, B, C, D, E)
        
    Returns:
        str: Отформатированный промпт
    """
    writer_info = config.SCRIPTWRITERS.get(writer_type, {})
    
    with open(SIMPLE_IMAGE_PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    return prompt_template.format(
        writer_name=writer_info.get("name", "Юморист"),
        writer_description=writer_info.get("description", "")
    )


def format_news_for_simple_image(news: Dict[str, Any]) -> str:
    """
    Форматирует новость для режима simple_image.
    
    Args:
        news: Словарь с новостью
        
    Returns:
        str: Форматированный текст
    """
    title = news.get('title', 'Без заголовка')
    content = news.get('content', '')
    
    return f"""Создай юмористический контент на основе этой новости:

**Заголовок новости:** {title}

**Содержание:**
{content}

Создай:
1. Короткую шутку/подпись к картинке
2. Промпт для Sora (на английском!) для генерации юмористической картинки
3. Короткий анекдот на тему новости

Ответ ТОЛЬКО в JSON формате!"""


def invoke_gpt_simple_image(news: Dict[str, Any], writer_type: str) -> Dict[str, Any]:
    """
    Вызывает GPT API для режима simple_image.
    
    Args:
        news: Словарь с новостью
        writer_type: Тип сценариста
        
    Returns:
        Dict: Результат с joke, sora_prompt, anecdote
    """
    from openai import OpenAI
    
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    model = get_setting("gpt_model", config.GPT_DIRECT_MODEL)
    
    system_prompt = load_simple_image_prompt(writer_type)
    user_message = format_news_for_simple_image(news)
    
    logger.info(f"Вызов GPT API simple_image (модель: {model}) для сценариста {writer_type}")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.9,
            max_tokens=1500
        )
        
        response_text = response.choices[0].message.content
        result = parse_json_response(response_text)
        
        logger.info(f"GPT API simple_image успешно: {result.get('title', 'Без названия')}")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка GPT API simple_image: {e}")
        raise


def invoke_gemini_simple_image(news: Dict[str, Any], writer_type: str) -> Dict[str, Any]:
    """
    Вызывает Gemini API для режима simple_image.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("Установите google-generativeai: pip install google-generativeai")
    
    api_key = config.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY не установлен в .env")
    
    genai.configure(api_key=api_key)
    model_name = get_setting("gemini_model", config.GEMINI_MODEL)
    
    system_prompt = load_simple_image_prompt(writer_type)
    user_message = format_news_for_simple_image(news)
    
    logger.info(f"Вызов Gemini API simple_image (модель: {model_name}) для сценариста {writer_type}")
    
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt
        )
        
        response = model.generate_content(
            user_message,
            generation_config=genai.types.GenerationConfig(
                temperature=0.9,
                max_output_tokens=1500
            )
        )
        
        result = parse_json_response(response.text)
        logger.info(f"Gemini API simple_image успешно: {result.get('title', 'Без названия')}")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка Gemini API simple_image: {e}")
        raise


def invoke_claude_simple_image(news: Dict[str, Any], writer_type: str) -> Dict[str, Any]:
    """
    Вызывает Claude API для режима simple_image.
    """
    try:
        import anthropic
    except ImportError:
        raise ImportError("Установите anthropic: pip install anthropic")
    
    api_key = config.ANTHROPIC_API_KEY
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY не установлен в .env")
    
    client = anthropic.Anthropic(api_key=api_key)
    model = get_setting("claude_model", config.CLAUDE_MODEL)
    
    system_prompt = load_simple_image_prompt(writer_type)
    user_message = format_news_for_simple_image(news)
    
    logger.info(f"Вызов Claude API simple_image (модель: {model}) для сценариста {writer_type}")
    
    try:
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        result = parse_json_response(response.content[0].text)
        logger.info(f"Claude API simple_image успешно: {result.get('title', 'Без названия')}")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка Claude API simple_image: {e}")
        raise


def invoke_llm_simple_image(news: Dict[str, Any], writer_type: str, mode: Optional[str] = None) -> Dict[str, Any]:
    """
    Универсальная функция вызова LLM для режима simple_image.
    
    Args:
        news: Словарь с новостью
        writer_type: Тип сценариста
        mode: Режим генерации API (gpt, gemini, claude)
        
    Returns:
        Dict: Результат с title, joke, sora_prompt, anecdote
    """
    if mode is None:
        mode = get_setting("generation_mode", "gpt")
    
    # В режиме simple_image не используем assistants, переключаемся на gpt
    if mode == "assistants":
        mode = "gpt"
    
    logger.info(f"invoke_llm_simple_image: режим={mode}, сценарист={writer_type}")
    
    if mode == "gpt":
        return invoke_gpt_simple_image(news, writer_type)
    elif mode == "gemini":
        return invoke_gemini_simple_image(news, writer_type)
    elif mode == "claude":
        return invoke_claude_simple_image(news, writer_type)
    else:
        # По умолчанию GPT
        return invoke_gpt_simple_image(news, writer_type)
