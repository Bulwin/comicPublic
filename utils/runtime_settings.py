"""
Модуль для управления динамическими настройками бота.
Позволяет изменять настройки через Telegram без перезапуска.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
import threading

# Путь к файлу настроек
SETTINGS_FILE = Path(__file__).resolve().parent.parent / "data" / "runtime_settings.json"

# Lock для потокобезопасности
_settings_lock = threading.Lock()

# Значения по умолчанию
DEFAULT_SETTINGS = {
    # Режим генерации: "assistants", "gpt", "gemini", "claude"
    "generation_mode": "assistants",
    
    # Использовать ли систему жюри
    "use_jury_evaluation": False,
    
    # Количество сценариев от каждого автора
    "scripts_per_writer": 1,
    
    # Модели для прямых API вызовов
    "gpt_model": "gpt-4o",
    "gemini_model": "gemini-2.0-flash",
    "claude_model": "claude-sonnet-4-20250514",
}

# Описания настроек для UI
SETTINGS_INFO = {
    "generation_mode": {
        "name": "🤖 Режим генерации",
        "description": "Какой API использовать для создания сценариев",
        "options": {
            "assistants": "GPT Assistants (промпты в OpenAI)",
            "gpt": "GPT API (промпт из программы)",
            "gemini": "Google Gemini",
            "claude": "Anthropic Claude"
        }
    },
    "use_jury_evaluation": {
        "name": "👨‍⚖️ Система жюри",
        "description": "Оценивать сценарии жюри или случайный выбор",
        "options": {
            True: "Включено (оценка + топ-4)",
            False: "Выключено (все сценарии)"
        }
    },
    "scripts_per_writer": {
        "name": "📝 Сценариев от автора",
        "description": "Сколько сценариев создает каждый автор",
        "options": {
            1: "1 сценарий",
            2: "2 сценария"
        }
    }
}


def _ensure_settings_file():
    """Создает файл настроек, если не существует."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)


def load_settings() -> Dict[str, Any]:
    """
    Загружает настройки из файла.
    
    Returns:
        Dict[str, Any]: Словарь настроек.
    """
    with _settings_lock:
        _ensure_settings_file()
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Добавляем отсутствующие настройки из DEFAULT_SETTINGS
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        except (json.JSONDecodeError, FileNotFoundError):
            return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Сохраняет настройки в файл.
    
    Args:
        settings: Словарь настроек.
        
    Returns:
        bool: True если успешно сохранено.
    """
    with _settings_lock:
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            return False


def get_setting(key: str, default: Any = None) -> Any:
    """
    Получает значение настройки.
    
    Args:
        key: Ключ настройки.
        default: Значение по умолчанию.
        
    Returns:
        Any: Значение настройки.
    """
    settings = load_settings()
    return settings.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))


def set_setting(key: str, value: Any) -> bool:
    """
    Устанавливает значение настройки.
    
    Args:
        key: Ключ настройки.
        value: Значение.
        
    Returns:
        bool: True если успешно.
    """
    settings = load_settings()
    settings[key] = value
    return save_settings(settings)


def get_generation_mode() -> str:
    """Возвращает текущий режим генерации."""
    return get_setting("generation_mode", "assistants")


def set_generation_mode(mode: str) -> bool:
    """
    Устанавливает режим генерации.
    
    Args:
        mode: "assistants", "gpt", "gemini" или "claude"
        
    Returns:
        bool: True если успешно.
    """
    valid_modes = ["assistants", "gpt", "gemini", "claude"]
    if mode not in valid_modes:
        raise ValueError(f"Недопустимый режим: {mode}. Доступные: {valid_modes}")
    return set_setting("generation_mode", mode)


def get_use_jury_evaluation() -> bool:
    """Возвращает флаг использования жюри."""
    return get_setting("use_jury_evaluation", False)


def set_use_jury_evaluation(value: bool) -> bool:
    """Устанавливает флаг использования жюри."""
    return set_setting("use_jury_evaluation", bool(value))


def get_scripts_per_writer() -> int:
    """Возвращает количество сценариев от автора."""
    return get_setting("scripts_per_writer", 1)


def set_scripts_per_writer(value: int) -> bool:
    """Устанавливает количество сценариев от автора."""
    if value not in [1, 2]:
        raise ValueError("Допустимые значения: 1 или 2")
    return set_setting("scripts_per_writer", int(value))


def get_all_settings_formatted() -> str:
    """
    Возвращает форматированную строку со всеми настройками.
    
    Returns:
        str: Форматированный текст настроек.
    """
    settings = load_settings()
    
    mode_names = {
        "assistants": "GPT Assistants",
        "gpt": "GPT API",
        "gemini": "Gemini",
        "claude": "Claude"
    }
    
    text = "⚙️ *Текущие настройки:*\n\n"
    text += f"🤖 Режим генерации: *{mode_names.get(settings['generation_mode'], settings['generation_mode'])}*\n"
    text += f"👨‍⚖️ Система жюри: *{'Включена' if settings['use_jury_evaluation'] else 'Выключена'}*\n"
    text += f"📝 Сценариев от автора: *{settings['scripts_per_writer']}*\n"
    
    if settings['generation_mode'] != 'assistants':
        model_key = f"{settings['generation_mode']}_model"
        if model_key in settings:
            text += f"🧠 Модель: *{settings[model_key]}*\n"
    
    return text
