"""
Пакет агентов для проекта DailyComicBot.
Содержит модули для агента-менеджера, агентов-сценаристов и агентов-жюри.
"""

from agents.manager import ManagerAgent, manager
from agents.scriptwriter import ScriptwriterAgent, create_scriptwriter, create_script
from agents.jury import JuryAgent, create_jury, evaluate_script

__all__ = [
    # Агент-менеджер
    'ManagerAgent', 'manager',
    
    # Агенты-сценаристы
    'ScriptwriterAgent', 'create_scriptwriter', 'create_script',
    
    # Агенты-жюри
    'JuryAgent', 'create_jury', 'evaluate_script'
]
