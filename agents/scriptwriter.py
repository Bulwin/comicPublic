"""
Модуль агентов-сценаристов для проекта DailyComicBot.
Отвечает за создание сценариев комиксов на основе новостей дня.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# Импорт модулей проекта
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import logger, handle_exceptions, measure_execution_time
from config import SCRIPTWRITERS


class ScriptwriterAgent:
    """
    Агент-сценарист, создающий сценарии комиксов на основе новостей дня.
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
        
        Args:
            news (Dict[str, Any]): Информация о новости дня.
            script_id (Optional[str]): Идентификатор сценария. По умолчанию None.
            
        Returns:
            Dict[str, Any]: Сгенерированный сценарий.
        """
        logger.info(f"Сценарист {self.name} начинает создание сценария")
        
        # Формирование запроса для OpenAI API
        prompt = self._create_prompt(news)
        
        # Вызов OpenAI API для генерации сценария
        script = self._generate_script(prompt, news)
        
        # Добавление метаданных
        script["writer_type"] = self.writer_type
        script["writer_name"] = self.name
        
        if script_id:
            script["script_id"] = script_id
        
        # Логирование создания сценария
        logger.log_script_creation(
            self.name,
            script.get('script_id', 'unknown'),
            script.get('title', 'Без названия')
        )
        return script
    
    def _create_prompt(self, news: Dict[str, Any]) -> str:
        """
        Создание промпта для генерации сценария.
        
        Args:
            news (Dict[str, Any]): Информация о новости дня.
            
        Returns:
            str: Промпт для генерации сценария.
        """
        # Базовая информация о новости
        title = news.get("title", "")
        content = news.get("content", "")
        
        # Формирование промпта в зависимости от типа сценариста
        prompt = f"""
        Ты - сценарист комиксов с уникальным стилем юмора: {self.description}
        
        Создай сценарий комикса из 4 панелей на основе следующей новости:
        
        Заголовок: {title}
        
        Содержание: {content}
        
        Твой сценарий должен соответствовать твоему стилю юмора и содержать:
        1. Заголовок комикса
        2. Краткое описание сюжета
        3. Детальное описание каждой из 4 панелей (визуальное описание, диалоги персонажей, текст от автора)
        4. Подпись под комиксом
        
        Сценарий должен быть оригинальным, юмористическим и связанным с новостью дня.
        """
        
        # Дополнительные инструкции в зависимости от типа сценариста
        if self.writer_type == "A":
            prompt += """
            Помни, что ты создаешь классический компанейский юмор, добрый, на уровне столовых анекдотов.
            Твои шутки должны быть понятны широкой аудитории, без сложных отсылок.
            Избегай грубости, пошлости и оскорблений.
            """
        elif self.writer_type == "B":
            prompt += """
            Помни, что ты создаешь черный юмор, мрачные шутки, сатиру.
            Используй иронию, сарказм, неожиданные повороты, абсурдные ситуации.
            Не переходи границы приличия, избегай слишком жестоких шуток.
            """
        elif self.writer_type == "C":
            prompt += """
            Помни, что ты создаешь юмор за гранью, с легкой нетерпимостью к меньшинствам, высмеиванием феминисток, веганов, ЛГБТ, БЛМ и прочих.
            Используй провокационные шутки, стереотипы, преувеличения.
            Не используй прямые оскорбления и призывы к ненависти.
            """
        elif self.writer_type == "D":
            prompt += """
            Помни, что ты создаешь иронию, постиронию, абсурд, сарказм.
            Используй многослойные шутки, отсылки к поп-культуре, метаюмор.
            Не делай шутки слишком сложными для понимания.
            """
        elif self.writer_type == "E":
            prompt += """
            Помни, что ты создаешь каламбуры и игру слов.
            Используй лингвистические шутки, игру с многозначностью слов, созвучия.
            Убедись, что каламбуры понятны и не слишком натянуты.
            """
        
        return prompt
    
    def _generate_script(self, prompt: str, news: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерация сценария с помощью OpenAI API.
        
        Args:
            prompt (str): Промпт для генерации сценария.
            news (Dict[str, Any]): Информация о новости дня.
            
        Returns:
            Dict[str, Any]: Сгенерированный сценарий.
        """
        try:
            # Попытка использовать OpenAI API через MCP сервер
            from utils import use_mcp_tool
            
            # Вызов OpenAI API через MCP сервер
            response = use_mcp_tool(
                server_name="openai",
                tool_name="chat",
                arguments={
                    "model": "gpt-4",
                    "messages": [
                        {"role": "system", "content": f"Ты - сценарист комиксов с именем {self.name}. {self.description}"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.8
                }
            )
            
            # Если получен ответ от API
            if response and "content" in response:
                # Парсинг ответа для извлечения сценария
                return self._parse_gpt_response(response["content"], news)
            
            # Если не удалось получить ответ от API, используем заглушку
            logger.warning(f"Не удалось получить ответ от OpenAI API, используется заглушка для функции _generate_script (тип: {self.writer_type})")
            return self._generate_fallback_script(news)
            
        except Exception as e:
            # В случае ошибки используем заглушку
            logger.error(f"Ошибка при вызове OpenAI API: {str(e)}")
            logger.warning(f"Используется заглушка для функции _generate_script (тип: {self.writer_type})")
            return self._generate_fallback_script(news)
    
    def _parse_gpt_response(self, response_text: str, news: Dict[str, Any]) -> Dict[str, Any]:
        """
        Парсинг ответа от GPT для извлечения сценария.
        
        Args:
            response_text (str): Текст ответа от GPT.
            news (Dict[str, Any]): Информация о новости дня.
            
        Returns:
            Dict[str, Any]: Сгенерированный сценарий.
        """
        try:
            # Инициализация сценария
            script = {
                "title": "",
                "description": "",
                "panels": [],
                "caption": ""
            }
            
            # Попытка парсинга JSON, если ответ в формате JSON
            try:
                # Проверяем, есть ли в ответе JSON-структура
                if '{' in response_text and '}' in response_text:
                    # Извлекаем JSON из ответа
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    json_str = response_text[json_start:json_end]
                    
                    # Пытаемся распарсить JSON
                    json_data = json.loads(json_str)
                    
                    # Если успешно распарсили JSON, используем его
                    if isinstance(json_data, dict):
                        # Заголовок
                        if "title" in json_data:
                            script["title"] = json_data["title"]
                        
                        # Описание
                        if "description" in json_data:
                            script["description"] = json_data["description"]
                        
                        # Панели
                        if "panels" in json_data and isinstance(json_data["panels"], list):
                            for panel_data in json_data["panels"]:
                                panel = {
                                    "description": panel_data.get("description", ""),
                                    "dialog": [],
                                    "narration": panel_data.get("narration", "")
                                }
                                
                                # Диалоги
                                if "dialog" in panel_data and isinstance(panel_data["dialog"], list):
                                    for dialog in panel_data["dialog"]:
                                        if isinstance(dialog, dict):
                                            panel["dialog"].append({
                                                "character": dialog.get("character", ""),
                                                "text": dialog.get("text", ""),
                                                "note": dialog.get("note", "")
                                            })
                                
                                script["panels"].append(panel)
                        
                        # Подпись
                        if "caption" in json_data:
                            script["caption"] = json_data["caption"]
                        
                        # Если успешно распарсили JSON, возвращаем результат
                        if script["title"] and script["description"] and script["panels"]:
                            return script
            except Exception as e:
                # Если не удалось распарсить JSON, продолжаем с текстовым форматом
                logger.warning(f"Не удалось распарсить JSON: {str(e)}. Продолжаем с текстовым форматом.")
            
            # Парсинг текстового формата
            
            # Поиск заголовка
            for line in response_text.split('\n'):
                line = line.strip()
                if line.lower().startswith("заголовок:") or line.lower().startswith("название:") or line.lower().startswith("title:"):
                    script["title"] = line.split(":", 1)[1].strip()
                    break
            
            # Поиск общего описания
            description_found = False
            description_lines = []
            for line in response_text.split('\n'):
                line = line.strip()
                if line.lower().startswith("общее описание:") or line.lower().startswith("описание:") or line.lower().startswith("description:"):
                    description_found = True
                    if ":" in line:
                        description_lines.append(line.split(":", 1)[1].strip())
                    continue
                
                if description_found:
                    if line and not (line.lower().startswith("панель") or line.lower().startswith("panel") or line.lower().startswith("подпись") or line.lower().startswith("caption")):
                        description_lines.append(line)
                    else:
                        description_found = False
            
            script["description"] = " ".join(description_lines).strip()
            
            # Поиск панелей
            current_panel = None
            in_visual_scene = False
            
            for line in response_text.split('\n'):
                line = line.strip()
                
                # Начало новой панели
                if line.lower().startswith("панель") or line.lower().startswith("panel"):
                    if current_panel is not None:
                        script["panels"].append(current_panel)
                    
                    current_panel = {
                        "description": "",
                        "dialog": [],
                        "narration": ""
                    }
                    continue
                
                # Если текущая панель не инициализирована, пропускаем строку
                if current_panel is None:
                    continue
                
                # Изображение или описание панели
                if line.lower().startswith("изображение:") or line.lower().startswith("описание:") or line.lower().startswith("description:") or line.lower().startswith("визуальная сцена:"):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        current_panel["description"] = parts[1].strip()
                    in_visual_scene = True
                    continue
                
                # Диалоги
                if line.lower().startswith("диалоги:") or line.lower().startswith("dialog:"):
                    in_visual_scene = False
                    continue
                
                # Текст от автора
                if line.lower().startswith("текст от автора:") or line.lower().startswith("narration:"):
                    in_visual_scene = False
                    current_panel["narration"] = line.split(":", 1)[1].strip()
                    continue
                
                # Запоминающаяся подпись в конце
                if line.lower().startswith("запоминающаяся подпись в конце:") or line.lower().startswith("подпись в конце:"):
                    in_visual_scene = False
                    script["caption"] = line.split(":", 1)[1].strip()
                    continue
                
                # Реплики персонажей или продолжение визуальной сцены
                if in_visual_scene:
                    # Если это продолжение визуальной сцены
                    if current_panel["description"]:
                        current_panel["description"] += " " + line
                    else:
                        current_panel["description"] = line
                elif line.startswith("-") or line.startswith("*"):
                    # Если это реплика персонажа
                    line = line[1:].strip()
                    
                    # Проверяем, есть ли в строке двоеточие
                    if ":" in line:
                        parts = line.split(":", 1)
                        character = parts[0].strip()
                        text = parts[1].strip()
                        
                        # Проверка на наличие примечания в скобках
                        note = ""
                        if "(" in character and ")" in character:
                            note_start = character.find("(")
                            note_end = character.find(")")
                            if note_start < note_end:
                                note = character[note_start+1:note_end].strip()
                                character = character[:note_start].strip()
                        
                        current_panel["dialog"].append({
                            "character": character,
                            "text": text,
                            "note": note
                        })
                    else:
                        # Если это просто текст без персонажа
                        current_panel["dialog"].append({
                            "character": "",
                            "text": line,
                            "note": ""
                        })
                elif ":" in line and not line.lower().startswith("изображение:") and not line.lower().startswith("описание:") and not line.lower().startswith("description:"):
                    # Если это реплика персонажа в формате "Персонаж: Текст"
                    parts = line.split(":", 1)
                    character = parts[0].strip()
                    text = parts[1].strip()
                    
                    # Проверка на наличие примечания в скобках
                    note = ""
                    if "(" in character and ")" in character:
                        note_start = character.find("(")
                        note_end = character.find(")")
                        if note_start < note_end:
                            note = character[note_start+1:note_end].strip()
                            character = character[:note_start].strip()
                    
                    current_panel["dialog"].append({
                        "character": character,
                        "text": text,
                        "note": note
                    })
            
            # Добавляем последнюю панель
            if current_panel is not None:
                script["panels"].append(current_panel)
            
            # Поиск подписи под комиксом
            for line in response_text.split('\n'):
                line = line.strip()
                if line.lower().startswith("подпись под комиксом:") or line.lower().startswith("подпись:") or line.lower().startswith("caption:"):
                    script["caption"] = line.split(":", 1)[1].strip()
                    break
            
            # Проверка наличия всех необходимых элементов
            if not script["title"]:
                script["title"] = f"Комикс о {news.get('title', 'новости дня')}"
            
            if not script["description"]:
                script["description"] = f"Комикс на тему: {news.get('title', 'новости дня')}"
            
            if not script["panels"]:
                script["panels"] = [
                    {"description": "Панель 1", "dialog": [{"character": "Персонаж", "text": "Текст", "note": ""}]},
                    {"description": "Панель 2", "dialog": [{"character": "Персонаж", "text": "Текст", "note": ""}]},
                    {"description": "Панель 3", "dialog": [{"character": "Персонаж", "text": "Текст", "note": ""}]},
                    {"description": "Панель 4", "dialog": [{"character": "Персонаж", "text": "Текст", "note": ""}]}
                ]
            
            if not script["caption"]:
                script["caption"] = f"Комикс на тему: {news.get('title', 'новости дня')}"
            
            return script
            
        except Exception as e:
            # В случае ошибки при парсинге используем заглушку
            logger.error(f"Ошибка при парсинге ответа от GPT: {str(e)}")
            return self._generate_fallback_script(news)
    
    def _generate_fallback_script(self, news: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерация заглушки для сценария.
        
        Args:
            news (Dict[str, Any]): Информация о новости дня.
            
        Returns:
            Dict[str, Any]: Сгенерированный сценарий.
        """
        # Заглушки для разных типов сценаристов
        if self.writer_type == "A":
            return {
                "title": "Искусственный интеллект на собеседовании",
                "description": "Комикс о том, как новая модель ИИ пытается пройти собеседование на работу.",
                "panels": [
                    {
                        "description": "Офис. Менеджер по персоналу сидит за столом, напротив него - робот с надписью 'GPT-Image-1'.",
                        "dialog": [
                            {"character": "Менеджер", "text": "Итак, расскажите о своем опыте работы с изображениями."},
                            {"character": "GPT-Image-1", "text": "Я могу создавать любые изображения по текстовому описанию!"}
                        ]
                    },
                    {
                        "description": "Крупный план менеджера и робота.",
                        "dialog": [
                            {"character": "Менеджер", "text": "А какое качество вы предпочитаете: low, medium или high?"},
                            {"character": "GPT-Image-1", "text": "Зависит от бюджета. Low - 1 цент, high - 25 центов."},
                            {"character": "Менеджер", "text": "Так дешево?", "note": "удивленно"}
                        ]
                    },
                    {
                        "description": "Менеджер делает заметки, робот стоит прямо.",
                        "dialog": [
                            {"character": "Менеджер", "text": "А что вы умеете лучше конкурентов?"},
                            {"character": "GPT-Image-1", "text": "Я более гибкий благодаря своей архитектуре!"},
                            {"character": "Менеджер", "text": "Все они так говорят...", "note": "в сторону"}
                        ]
                    },
                    {
                        "description": "Менеджер протягивает руку роботу.",
                        "dialog": [
                            {"character": "Менеджер", "text": "Поздравляю, вы приняты!"},
                            {"character": "Мысли менеджера", "text": "Может, стоило взять модель с руками..."}
                        ],
                        "narration": "GPT-Image-1 пытается пожать руку, но вместо этого выдает распечатку с изображением рукопожатия."
                    }
                ],
                "caption": "Даже с искусственным интеллектом собеседования всегда неловкие."
            }
        elif self.writer_type == "B":
            return {
                "title": "Последний художник",
                "description": "Мрачный взгляд на будущее искусства после появления GPT-Image-1.",
                "panels": [
                    {
                        "description": "Мрачная студия. Последний художник-человек сидит перед пустым холстом. На стене висит календарь с датой 2030.",
                        "dialog": [
                            {"character": "Художник", "text": "Еще один день без заказов..."}
                        ],
                        "narration": "С момента выхода GPT-Image-1 прошло 5 лет."
                    },
                    {
                        "description": "Художник смотрит на свой телефон с уведомлением.",
                        "dialog": [
                            {"character": "Уведомление", "text": "Новая модель GPT-Image-5 теперь создает картины, неотличимые от работ старых мастеров!"}
                        ]
                    },
                    {
                        "description": "Художник стоит у окна, смотрит на город, где все рекламные щиты показывают AI-искусство.",
                        "dialog": [
                            {"character": "Художник", "text": "Может, пора сдаться и стать промпт-инженером..."}
                        ]
                    },
                    {
                        "description": "Художник сидит за компьютером, вводит промпт. На экране надпись: 'Создать портрет отчаявшегося художника'.",
                        "dialog": [
                            {"character": "AI", "text": "Изображение готово! С вас 25 центов."},
                            {"character": "Художник", "text": "Даже моё отчаяние теперь стоит всего 25 центов."}
                        ]
                    }
                ],
                "caption": "Когда искусственный интеллект рисует лучше тебя, остаётся только рисовать своё отчаяние."
            }
        elif self.writer_type == "D":
            return {
                "title": "Эволюция ИИ-арта",
                "description": "Ироничный взгляд на развитие генерации изображений с помощью ИИ.",
                "panels": [
                    {
                        "description": "Художник-человек рисует картину, рядом стоит компьютер с надписью '2020'.",
                        "dialog": [
                            {"character": "Компьютер", "text": "Я тоже так могу!"},
                            {"character": "Художник", "text": "Ха-ха, мечтай!", "note": "смеется"}
                        ]
                    },
                    {
                        "description": "Тот же художник, но уже нервно смотрит на компьютер с надписью '2022'.",
                        "dialog": [
                            {"character": "Компьютер", "text": "Смотри, что я сгенерировал!"},
                            {"character": "Художник", "text": "Хм, неплохо, но всё равно видно, что это ИИ...", "note": "обеспокоенно"}
                        ]
                    },
                    {
                        "description": "Художник в панике смотрит на компьютер с надписью '2024'.",
                        "dialog": [
                            {"character": "Компьютер", "text": "Я теперь GPT-Image-1 и могу делать изображения любого качества!"},
                            {"character": "Художник", "text": "А как же моя уникальность?!", "note": "в ужасе"}
                        ]
                    },
                    {
                        "description": "Художник сидит за компьютером, вводит промпты.",
                        "dialog": [
                            {"character": "Художник", "text": "Если не можешь победить - возглавь...", "note": "смирившись"}
                        ],
                        "narration": "На экране: 'Подписка на GPT-Image-1: $99/месяц'"
                    }
                ],
                "caption": "Постирония в том, что этот комикс тоже нарисован искусственным интеллектом."
            }
        else:
            # Для остальных типов сценаристов возвращаем базовый шаблон
            return {
                "title": f"Комикс от сценариста {self.writer_type} о {news.get('title', 'новости дня')}",
                "description": f"Описание комикса от сценариста {self.writer_type} о новости: {news.get('title', '')}",
                "panels": [
                    {"description": "Панель 1", "dialog": [{"character": "Персонаж 1", "text": "Текст 1"}]},
                    {"description": "Панель 2", "dialog": [{"character": "Персонаж 2", "text": "Текст 2"}]},
                    {"description": "Панель 3", "dialog": [{"character": "Персонаж 3", "text": "Текст 3"}]},
                    {"description": "Панель 4", "dialog": [{"character": "Персонаж 4", "text": "Текст 4"}]}
                ],
                "caption": f"Подпись к комиксу от сценариста {self.writer_type}"
            }


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
    Создание сценария комикса.
    
    Args:
        writer_type (str): Тип сценариста (A, B, C, D, E).
        news (Dict[str, Any]): Информация о новости дня.
        script_id (Optional[str]): Идентификатор сценария. По умолчанию None.
        
    Returns:
        Dict[str, Any]: Сгенерированный сценарий.
    """
    scriptwriter = create_scriptwriter(writer_type)
    return scriptwriter.create_script(news, script_id)
