"""
Модуль агентов-сценаристов для проекта DailyComicBot.
Отвечает за создание сценариев комиксов на основе новостей дня.
Поддерживает несколько режимов: Assistants API, GPT, Gemini, Claude.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Импорт модулей проекта
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import logger, handle_exceptions, measure_execution_time
from utils.runtime_settings import get_generation_mode
from config import SCRIPTWRITERS


class ScriptwriterAgent:
    """
    Агент-сценарист, создающий сценарии комиксов на основе новостей дня.
    Поддерживает разные LLM провайдеры в зависимости от настроек.
    """
    
    def __init__(self, writer_type: str):
        """
        Инициализация агента-сценариста.
        
        Args:
            writer_type (str): Тип сценариста (A, B, C, D, E).
        """
        if writer_type not in SCRIPTWRITERS:
            raise ValueError(f"Неизвестный тип сценариста: {writer_type}")
        
        self.writer_type = writer_type
        self.writer_info = SCRIPTWRITERS[writer_type]
        self.name = self.writer_info["name"]
        self.description = self.writer_info["description"]
        
        logger.info(f"Агент-сценарист {self.name} (тип {writer_type}) инициализирован")
    
    @measure_execution_time
    def create_script(self, news: Dict[str, Any], script_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Создание сценария комикса на основе новости дня.
        Использует LLM в зависимости от текущего режима генерации.
        
        Args:
            news (Dict[str, Any]): Информация о новости дня.
            script_id (Optional[str]): Идентификатор сценария. По умолчанию None.
            
        Returns:
            Dict[str, Any]: Сгенерированный сценарий.
        """
        mode = get_generation_mode()
        mode_names = {
            "assistants": "Assistants API",
            "gpt": "GPT API",
            "gemini": "Gemini API",
            "claude": "Claude API"
        }
        
        logger.info(f"Сценарист {self.name} начинает создание сценария через {mode_names.get(mode, mode)}")
        
        try:
            # Используем универсальный LLM клиент
            from utils.llm_clients import invoke_llm
            
            script = invoke_llm(news, self.writer_type, mode)
            
            if not script:
                raise Exception(f"{mode_names.get(mode, mode)} вернул пустой результат")
            
            # Добавление метаданных
            script["writer_type"] = self.writer_type
            script["writer_name"] = self.name
            script["generation_mode"] = mode
            
            if script_id:
                script["script_id"] = script_id
            
            # Логирование создания сценария
            logger.log_script_creation(
                self.name,
                script.get('script_id', 'unknown'),
                script.get('title', 'Без названия')
            )
            
            logger.info(f"Сценарий успешно создан через {mode_names.get(mode, mode)} для сценариста {self.writer_type}")
            return script
            
        except Exception as e:
            logger.error(f"Ошибка при создании сценария через {mode_names.get(mode, mode)}: {str(e)}")
            raise Exception(f"Не удалось создать сценарий для сценариста {self.writer_type}: {str(e)}")


# Функция для создания агента-сценариста
def create_scriptwriter(writer_type: str) -> ScriptwriterAgent:
    """
    Создание агента-сценариста.
    
    Args:
        writer_type (str): Тип сценариста (A, B, C, D, E).
        
    Returns:
        ScriptwriterAgent: Агент-сценарист.
    """
    return ScriptwriterAgent(writer_type)


# Функция для создания сценария
def create_script(writer_type: str, news: Dict[str, Any], script_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Создание сценария комикса через Assistants API.
    
    Args:
        writer_type (str): Тип сценариста (A, B, C, D, E).
        news (Dict[str, Any]): Информация о новости дня.
        script_id (Optional[str]): Идентификатор сценария. По умолчанию None.
        
    Returns:
        Dict[str, Any]: Сгенерированный сценарий.
    """
    scriptwriter = create_scriptwriter(writer_type)
    return scriptwriter.create_script(news, script_id)
