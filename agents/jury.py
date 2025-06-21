"""
Модуль агентов-жюри для проекта DailyComicBot.
Отвечает за оценку сценариев комиксов через Assistants API.
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Импорт модулей проекта
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import logger, handle_exceptions, measure_execution_time
from config import SCRIPTWRITERS


class JuryAgent:
    """
    Агент-жюри, оценивающий сценарии комиксов.
    """
    
    def __init__(self, jury_type: str):
        """
        Инициализация агента-жюри.
        
        Args:
            jury_type (str): Тип жюри (A, B, C, D, E).
        """
        if jury_type not in SCRIPTWRITERS:
            raise ValueError(f"Неизвестный тип жюри: {jury_type}")
        
        self.jury_type = jury_type
        self.jury_info = SCRIPTWRITERS[jury_type]
        self.name = self.jury_info["name"]
        self.description = self.jury_info["description"]
        
        logger.info(f"Агент-жюри {self.name} (тип {jury_type}) инициализирован")
    
    @measure_execution_time
    def evaluate_script(self, script: Dict[str, Any], news: Dict[str, Any]) -> Dict[str, Any]:
        """
        Оценка сценария комикса через Assistants API.
        
        Args:
            script (Dict[str, Any]): Сценарий комикса.
            news (Dict[str, Any]): Информация о новости дня.
            
        Returns:
            Dict[str, Any]: Результат оценки.
        """
        logger.info(f"Жюри {self.name} начинает оценку сценария {script.get('script_id', 'без ID')} через Assistants API")
        
        try:
            # Используем Assistants API для оценки сценария
            from utils.assistants_api import invoke_jury
            
            evaluation = invoke_jury(script, self.jury_type, news)
            
            if not evaluation:
                raise Exception("Assistants API вернул пустой результат")
            
            # Добавление метаданных
            evaluation["jury_type"] = self.jury_type
            evaluation["jury_name"] = self.name
            evaluation["script_id"] = script.get("script_id", "unknown")
            
            # Логирование оценки сценария
            logger.log_script_evaluation(
                self.name,
                script.get('script_id', 'unknown'),
                evaluation.get('total_score', 0)
            )
            
            logger.info(f"Оценка успешно создана через Assistants API для жюри {self.jury_type}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Ошибка при оценке сценария через Assistants API: {str(e)}")
            raise Exception(f"Не удалось оценить сценарий для жюри {self.jury_type}: {str(e)}")


# Функция для создания агента-жюри
def create_jury(jury_type: str) -> JuryAgent:
    """
    Создание агента-жюри.
    
    Args:
        jury_type (str): Тип жюри (A, B, C, D, E).
        
    Returns:
        JuryAgent: Агент-жюри.
    """
    return JuryAgent(jury_type)


# Функция для оценки сценария
def evaluate_script(jury_type: str, script: Dict[str, Any], news: Dict[str, Any]) -> Dict[str, Any]:
    """
    Оценка сценария комикса через Assistants API.
    
    Args:
        jury_type (str): Тип жюри (A, B, C, D, E).
        script (Dict[str, Any]): Сценарий комикса.
        news (Dict[str, Any]): Информация о новости дня.
        
    Returns:
        Dict[str, Any]: Результат оценки.
    """
    jury = create_jury(jury_type)
    return jury.evaluate_script(script, news)
