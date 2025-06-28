"""
Модуль для работы с OpenAI Assistants API.
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import time
import logging
from datetime import datetime

# Импорт модулей проекта
from tools.storage_tools import store_script
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.logger import info, error, warning, debug
from utils.error_handler import handle_exceptions
from utils.openai_api import measure_execution_time
from config import OPENAI_API_KEY

# Отключение подробного логирования HTTP-запросов OpenAI
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Импорт OpenAI API
try:
    from openai import OpenAI
except ImportError:
    error("Не удалось импортировать модуль OpenAI. Установите его с помощью команды: pip install openai")


def parse_text_evaluation(text: str) -> Dict[str, Any]:
    """
    Парсинг текстового формата оценки жюри.
    
    Args:
        text: Текстовая оценка жюри.
        
    Returns:
        Dict[str, Any]: Оценка в формате JSON.
    """
    info(f"Парсинг текстового формата оценки жюри")
    evaluation = {
        "scores": {},
        "comments": {},
        "total_score": 0,
        "overall_comment": ""
    }
    
    # Парсинг релевантности
    relevance_match = re.search(r'Релевантность:\s*(\d+)/20\s*(?:\n-\s*(.*?)(?=\n\w+:|$))?', text, re.DOTALL)
    if relevance_match:
        evaluation["scores"]["relevance"] = int(relevance_match.group(1))
        evaluation["comments"]["relevance"] = relevance_match.group(2).strip() if relevance_match.group(2) else ""
    
    # Парсинг оригинальности
    originality_match = re.search(r'Оригинальность:\s*(\d+)/20\s*(?:\n-\s*(.*?)(?=\n\w+:|$))?', text, re.DOTALL)
    if originality_match:
        evaluation["scores"]["originality"] = int(originality_match.group(1))
        evaluation["comments"]["originality"] = originality_match.group(2).strip() if originality_match.group(2) else ""
    
    # Парсинг юмористического потенциала
    humor_match = re.search(r'Юмористический потенциал:\s*(\d+)/30\s*(?:\n-\s*(.*?)(?=\n\w+:|$))?', text, re.DOTALL)
    if humor_match:
        evaluation["scores"]["humor"] = int(humor_match.group(1))
        evaluation["comments"]["humor"] = humor_match.group(2).strip() if humor_match.group(2) else ""
    
    # Парсинг структуры и логики
    structure_match = re.search(r'Структура и логика:\s*(\d+)/15\s*(?:\n-\s*(.*?)(?=\n\w+:|$))?', text, re.DOTALL)
    if structure_match:
        evaluation["scores"]["structure"] = int(structure_match.group(1))
        evaluation["comments"]["structure"] = structure_match.group(2).strip() if structure_match.group(2) else ""
    
    # Парсинг визуального потенциала
    visual_match = re.search(r'Визуальный потенциал:\s*(\d+)/15\s*(?:\n-\s*(.*?)(?=\n\w+:|$))?', text, re.DOTALL)
    if visual_match:
        evaluation["scores"]["visual"] = int(visual_match.group(1))
        evaluation["comments"]["visual"] = visual_match.group(2).strip() if visual_match.group(2) else ""
    
    # Парсинг итоговой оценки
    total_match = re.search(r'Итоговая оценка:\s*(\d+)/100', text)
    if total_match:
        evaluation["total_score"] = int(total_match.group(1))
    else:
        # Если итоговая оценка не найдена, вычисляем сумму
        total = sum(evaluation["scores"].values())
        evaluation["total_score"] = total
    
    # Парсинг общего комментария
    comment_match = re.search(r'Общий комментарий:\s*(.*?)(?=\n\n|$)', text, re.DOTALL)
    if comment_match:
        evaluation["overall_comment"] = comment_match.group(1).strip()
    
    debug(f"Результат парсинга оценки: {json.dumps(evaluation, ensure_ascii=False)[:200]}...")
    return evaluation


def parse_text_script(text: str) -> Dict[str, Any]:
    """
    Парсинг текстового формата сценария комикса.
    
    Args:
        text: Текстовый сценарий комикса.
        
    Returns:
        Dict[str, Any]: Сценарий комикса в формате JSON.
    """
    info(f"Парсинг текстового формата сценария")
    script = {}
    
    # Парсинг заголовка (поддержка обоих форматов: "Заголовок:" и "**Заголовок:**")
    title_match = re.search(r'\*{0,2}Заголовок:\*{0,2}\s*(.*?)(?:\n|$)', text)
    if title_match:
        script['title'] = title_match.group(1).strip()
    else:
        script['title'] = "Без заголовка"
    
    # Парсинг описания (поддержка обоих форматов: "Общее описание:" и "**Общее описание:**")
    description_match = re.search(r'\*{0,2}Общее описание:\*{0,2}\s*(.*?)(?=\n\n(?:###\s*)?Панель|\n(?:###\s*)?Панель)', text, re.DOTALL)
    if description_match:
        script['description'] = description_match.group(1).strip()
    else:
        script['description'] = "Без описания"
    
    # Парсинг панелей (поддержка форматов: "Панель 1:", "### Панель 1:")
    panels = []  # Инициализация списка панелей
    panel_matches = re.finditer(r'(?:###\s*)?Панель (\d+):(.*?)(?=\n(?:###\s*)?Панель \d+:|\*{0,2}Подпись под комиксом:|$)', text, re.DOTALL)
    
    for match in panel_matches:
        panel_num = int(match.group(1))
        panel_content = match.group(2).strip()
        
        panel = {
            'description': '',
            'dialog': [],
            'narration': ''
        }
        
        # Парсинг визуальной сцены (поддержка форматов: "- Визуальная сцена:" и "**Визуальная сцена:**")
        scene_match = re.search(r'(?:-\s*)?\*{0,2}Визуальная сцена:\*{0,2}\s*["\']?(.*?)["\']?(?=\n|$)', panel_content, re.DOTALL)
        if scene_match:
            panel['description'] = scene_match.group(1).strip()
        
        # Парсинг текста от автора (поддержка форматов: "Текст от автора:" и "**Текст от автора:**")
        author_text_match = re.search(r'\*{0,2}Текст от автора:\*{0,2}\s*(.*?)(?=\n|$)', panel_content, re.DOTALL)
        if author_text_match:
            panel['narration'] = author_text_match.group(1).strip()
        
        # Парсинг запоминающейся подписи (для последней панели)
        if panel_num == 4:
            caption_match = re.search(r'-\s*Запоминающаяся подпись в конце:\s*["\']?(.*?)["\']?(?=\n|$)', panel_content, re.DOTALL)
            if caption_match:
                panel['dialog'].append({
                    "character": "Подпись",
                    "text": caption_match.group(1).strip(),
                    "note": "запоминающаяся подпись"
                })
        
        # Парсинг других диалогов (если есть)
        dialog_lines = re.findall(r'(?:^|\n)(?:-\s*)?([^:\n]+?)(?:\s*\(([^)]+)\))?\s*:\s*["\']?(.+?)["\']?(?=\n|$)', panel_content)
        for dialog_match in dialog_lines:
            character = dialog_match[0].strip()
            note = dialog_match[1].strip() if dialog_match[1] else ""
            text = dialog_match[2].strip()
            
            # Пропускаем визуальную сцену и запоминающуюся подпись - они уже обработаны
            if character.lower() in ['визуальная сцена', 'запоминающаяся подпись в конце']:
                continue
            
            panel['dialog'].append({
                "character": character,
                "text": text,
                "note": note
            })
        
        panels.append(panel)
    
    script['panels'] = panels
    
    # Парсинг подписи под комиксом (поддержка форматов: "Подпись под комиксом:" и "**Подпись под комиксом:**")
    caption_match = re.search(r'\*{0,2}Подпись под комиксом:\*{0,2}\s*(.*?)(?=\n|$)', text, re.DOTALL)
    if caption_match:
        script['caption'] = caption_match.group(1).strip()
    else:
        script['caption'] = "Без подписи"
    
    debug(f"Результат парсинга: {json.dumps(script, ensure_ascii=False)[:200]}...")
    return script


class AssistantsManager:
    """
    Менеджер для работы с OpenAI Assistants API.
    """
    
    def __init__(self, api_key: str = None):
        """
        Инициализация менеджера.
        
        Args:
            api_key: API-ключ OpenAI. Если не указан, используется значение из конфигурации.
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("API-ключ OpenAI не указан")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Загрузка ID ассистентов из переменных окружения
        self.assistants = {}
        self.scriptwriter_assistants = []
        self.jury_assistants = []
        
        # Загрузка ID ассистентов-сценаристов
        for writer_type in ["A", "B", "C", "D", "E"]:
            assistant_id = os.getenv(f"SCRIPTWRITER_{writer_type}_ASSISTANT_ID")
            if assistant_id:
                self.assistants[f"scriptwriter_{writer_type}"] = assistant_id
                self.scriptwriter_assistants.append((writer_type, assistant_id))
        
        # Загрузка ID ассистентов-жюри
        for jury_type in ["A", "B", "C", "D", "E"]:
            assistant_id = os.getenv(f"JURY_{jury_type}_ASSISTANT_ID")
            if assistant_id:
                self.assistants[f"jury_{jury_type}"] = assistant_id
                self.jury_assistants.append((jury_type, assistant_id))
        
        self.threads = {}
        
        info(f"Менеджер ассистентов инициализирован с {len(self.assistants)} ассистентами")
    
    @measure_execution_time
    def create_assistant(self, name: str, instructions: str, tools: List[Dict[str, Any]] = None, model: str = "gpt-4") -> str:
        """
        Создание нового ассистента.
        
        Args:
            name: Имя ассистента.
            instructions: Инструкции для ассистента.
            tools: Список инструментов для ассистента.
            model: Модель для ассистента.
            
        Returns:
            str: Идентификатор ассистента.
        """
        info(f"Создание нового ассистента: {name}")
        
        try:
            assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                tools=tools or [],
                model=model
            )
            self.assistants[name] = assistant.id
            
            info(f"Ассистент {name} успешно создан с ID: {assistant.id}")
            return assistant.id
        
        except Exception as e:
            error(f"Ошибка при создании ассистента {name}: {str(e)}")
            raise
    
    @measure_execution_time
    def create_thread(self, name: str) -> str:
        """
        Создание нового потока.
        
        Args:
            name: Имя потока.
            
        Returns:
            str: Идентификатор потока.
        """
        info(f"Создание нового потока: {name}")
        
        try:
            thread = self.client.beta.threads.create()
            self.threads[name] = thread.id
            
            info(f"Поток {name} успешно создан с ID: {thread.id}")
            return thread.id
        
        except Exception as e:
            error(f"Ошибка при создании потока {name}: {str(e)}")
            raise
    
    @measure_execution_time
    def add_message(self, thread_name: str, content: str, role: str = "user") -> str:
        """
        Добавление сообщения в поток.
        
        Args:
            thread_name: Имя потока.
            content: Содержимое сообщения.
            role: Роль отправителя сообщения.
            
        Returns:
            str: Идентификатор сообщения.
        """
        info(f"Добавление сообщения в поток {thread_name}")
        
        try:
            thread_id = self.threads.get(thread_name)
            if not thread_id:
                info(f"Поток {thread_name} не найден, создание нового потока")
                thread_id = self.create_thread(thread_name)
            
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role=role,
                content=content
            )
            
            info(f"Сообщение успешно добавлено в поток {thread_name} с ID: {message.id}")
            return message.id
        
        except Exception as e:
            error(f"Ошибка при добавлении сообщения в поток {thread_name}: {str(e)}")
            raise
    
    @measure_execution_time
    def run_assistant(self, thread_name: str, assistant_name: str, instructions: str = None, max_retries: int = 3, retry_delay: int = 5) -> Dict[str, Any]:
        """
        Запуск ассистента для обработки потока.
        
        Args:
            thread_name: Имя потока.
            assistant_name: Имя ассистента.
            instructions: Дополнительные инструкции для запуска.
            max_retries: Максимальное количество попыток запуска.
            retry_delay: Задержка между попытками в секундах.
            
        Returns:
            Dict[str, Any]: Результат запуска ассистента.
        """
        info(f"Запуск ассистента {assistant_name} для обработки потока {thread_name}")
        
        thread_id = self.threads.get(thread_name)
        assistant_id = self.assistants.get(assistant_name)
        
        if not thread_id:
            error_msg = f"Поток '{thread_name}' не найден"
            error(error_msg)
            raise ValueError(error_msg)
        
        if not assistant_id:
            error_msg = f"Ассистент '{assistant_name}' не найден"
            error(error_msg)
            raise ValueError(error_msg)
        
        for attempt in range(max_retries):
            try:
                # Создание запуска
                run = self.client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                    instructions=instructions
                )
                
                info(f"Запуск создан с ID: {run.id}")
                
                # Ожидание завершения запуска
                wait_time = 3  # Начальное время ожидания в секундах
                max_wait_time = 15  # Максимальное время ожидания в секундах
                
                while True:
                    run_status = self.client.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    
                    if run_status.status == "completed":
                        info(f"Запуск {run.id} успешно завершен")
                        break
                    
                    if run_status.status in ["failed", "cancelled", "expired"]:
                        error_msg = f"Запуск {run.id} завершился с ошибкой: {run_status.status}"
                        error(error_msg)
                        
                        if attempt < max_retries - 1:
                            info(f"Повторная попытка через {retry_delay} секунд...")
                            time.sleep(retry_delay)
                            break
                        else:
                            raise Exception(error_msg)
                    
                    # Проверка наличия требуемых действий
                    if run_status.status == "requires_action":
                        info(f"Запуск {run.id} требует действий")
                        
                        # Обработка требуемых действий
                        required_actions = run_status.required_action
                        if required_actions and required_actions.type == "submit_tool_outputs":
                            tool_calls = required_actions.submit_tool_outputs.tool_calls
                            tool_outputs = []
                            
                            for tool_call in tool_calls:
                                tool_output = self._handle_tool_call(tool_call)
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps(tool_output)
                                })
                            
                            # Отправка результатов выполнения инструментов
                            self.client.beta.threads.runs.submit_tool_outputs(
                                thread_id=thread_id,
                                run_id=run.id,
                                tool_outputs=tool_outputs
                            )
                            
                            # Сбрасываем время ожидания после действия
                            wait_time = 3
                    
                    # Пауза перед следующей проверкой статуса с экспоненциальной задержкой
                    time.sleep(wait_time)
                    
                    # Увеличиваем время ожидания, но не больше максимального
                    wait_time = min(wait_time * 1.5, max_wait_time)
                
                # Если запуск не завершился успешно, переходим к следующей попытке
                if run_status.status != "completed":
                    continue
                
                # Получение сообщений
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                
                # Возврат последнего сообщения от ассистента
                for message in messages.data:
                    if message.role == "assistant":
                        content = message.content[0].text.value if message.content else ""
                        info("=== ПОЛНЫЙ ОТВЕТ ОТ GPT ASSISTANTS API ===")
                        info(f"Полный ответ от ассистента: {content}")
                        info(f"Длина ответа: {len(content)} символов")
                        info("==========================================")
                        return {
                            "role": message.role,
                            "content": content
                        }
                
                warning(f"Не найдено сообщений от ассистента в потоке {thread_name}")
                return None
            
            except Exception as e:
                error(f"Ошибка при запуске ассистента (попытка {attempt+1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    info(f"Повторная попытка через {retry_delay} секунд...")
                    time.sleep(retry_delay)
                else:
                    raise
    
    def _handle_tool_call(self, tool_call) -> Any:
        """
        Обработка вызова инструмента.
        
        Args:
            tool_call: Информация о вызове инструмента.
            
        Returns:
            Any: Результат выполнения инструмента.
        """
        info(f"Обработка вызова инструмента: {tool_call.function.name}")
        
        try:
            function_name = tool_call.function.name
            
            # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ АРГУМЕНТОВ ФУНКЦИИ
            info("=== ОТЛАДКА TOOL_CALL ===")
            info(f"Имя функции: {function_name}")
            info(f"Сырые аргументы: {tool_call.function.arguments}")
            info("========================")
            
            function_args = json.loads(tool_call.function.arguments)
            
            # ЛОГИРОВАНИЕ РАСПАРСЕННЫХ АРГУМЕНТОВ
            info("=== РАСПАРСЕННЫЕ АРГУМЕНТЫ ===")
            info(f"Аргументы функции: {function_args}")
            info(f"Ключи в аргументах: {list(function_args.keys())}")
            for key, value in function_args.items():
                info(f"  {key}: {type(value)} = {value}")
            info("=============================")
            
            # Обработка различных инструментов
            if function_name == "get_news_details":
                return self._get_news_details(function_args.get("date"))
            
            elif function_name == "get_script_details":
                return self._get_script_details(function_args.get("script_id"))
            
            elif function_name == "submit_script":
                return self._submit_script(function_args.get("script"))
            
            elif function_name == "submit_evaluation":
                return self._submit_evaluation(function_args.get("evaluation"))
            
            else:
                warning(f"Неизвестный инструмент: {function_name}")
                return {"error": f"Неизвестный инструмент: {function_name}"}
        
        except Exception as e:
            error(f"Ошибка при обработке вызова инструмента: {str(e)}")
            return {"error": str(e)}
    
    def _get_news_details(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Получение деталей новости дня.
        
        Args:
            date: Опциональная дата в формате YYYY-MM-DD. Если не указана, используется текущая дата.
            
        Returns:
            Dict[str, Any]: Информация о новости дня, включая заголовок и содержание.
        """
        info(f"Получение деталей новости для даты: {date or 'текущая'}")
        
        try:
            from tools.news_tools import get_top_news, extract_title, extract_news_content
            
            # ИСПРАВЛЕНИЕ: Всегда получаем текущую новость дня, игнорируя переданную дату
            # Это гарантирует, что ассистенты получат ту же новость, что и основная система
            news = get_top_news(force_new=False)  # Используем существующую новость
            
            if news:
                # ИСПРАВЛЕНИЕ: Применяем очистку содержания при каждом обращении
                # чтобы убрать дублирование заголовка, если оно есть в сохраненной новости
                raw_content = news.get('content', '')
                
                # Если в содержании есть дублирование заголовка, очищаем его
                if raw_content.startswith('**ЗАГОЛОВОК**') or 'ЗАГОЛОВОК:' in raw_content:
                    info("Обнаружено дублирование заголовка в содержании, применяем очистку")
                    cleaned_content = extract_news_content(raw_content)
                    news['content'] = cleaned_content
                
                info(f"Получена главная новость дня: {news.get('title', '')[:100]}...")
                info(f"Содержание новости: {news.get('content', '')[:100]}...")
                return news
            else:
                warning("Не удалось получить новость")
                return {
                    "title": "Заглушка для новости",
                    "content": "Это заглушка для новости, которую не удалось получить."
                }
        
        except Exception as e:
            error(f"Ошибка при получении деталей новости: {str(e)}")
            return {
                "title": "Ошибка при получении новости",
                "content": f"Произошла ошибка при получении новости: {str(e)}"
            }
    
    def _get_script_details(self, script_id: str) -> Dict[str, Any]:
        """
        Получение деталей сценария комикса.
        
        Args:
            script_id: Идентификатор сценария.
            
        Returns:
            Dict[str, Any]: Информация о сценарии комикса.
        """
        info(f"Получение деталей сценария с ID: {script_id}")
        
        try:
            from tools.storage_tools import load_script
            
            # Загрузка сценария
            script = load_script(script_id)
            
            if script:
                info(f"Получен сценарий: {script.get('title', '')}")
                return script
            else:
                warning(f"Не удалось найти сценарий с ID: {script_id}")
                return {
                    "error": f"Сценарий с ID {script_id} не найден"
                }
        
        except Exception as e:
            error(f"Ошибка при получении деталей сценария: {str(e)}")
            return {
                "error": f"Ошибка при получении сценария: {str(e)}"
            }
    
    def _submit_script(self, script: Any) -> Dict[str, Any]:
        """
        Отправка готового сценария.
        
        Args:
            script: Сценарий комикса в JSON-формате или строке.
            
        Returns:
            Dict[str, Any]: Результат отправки сценария, включая идентификатор сценария.
        """
        # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ВХОДЯЩИХ ДАННЫХ
        info("=== ОТЛАДКА SUBMIT_SCRIPT ===")
        info(f"Тип полученного script: {type(script)}")
        info(f"Значение script: {script}")
        info(f"Длина script (если строка): {len(script) if isinstance(script, str) else 'N/A'}")
        info("=============================")
        
        # Проверка на None
        if script is None:
            info("GPT Assistant вызвал функцию без аргументов (промежуточный шаг)")
            debug("Это нормальное поведение - Assistant может 'думать' и исправляться")
            return {
                "success": False,
                "message": "GPT Assistant вызвал функцию преждевременно (будет повторная попытка)"
            }
        
        try:
            from tools.storage_tools import store_script
            
            # Если получена строка, пытаемся распарсить как JSON
            if isinstance(script, str):
                info("Получена строка, пытаемся распарсить как JSON")
                try:
                    script = json.loads(script)
                except json.JSONDecodeError:
                    # Если не JSON, пытаемся распарсить как текст
                    info("Не JSON, пытаемся распарсить как текстовый сценарий")
                    script = parse_text_script(script)
                    if not script:
                        error("Не удалось распарсить текстовый сценарий")
                        return {
                            "success": False,
                            "message": "Не удалось распарсить текстовый сценарий"
                        }
            
            # Проверка базовой структуры сценария
            if not isinstance(script, dict):
                error(f"Сценарий должен быть словарем, получен: {type(script)}")
                return {
                    "success": False,
                    "message": f"Неверный формат сценария: {type(script)}"
                }
            
            info(f"Отправка сценария: {script.get('title', 'Без заголовка')}")
            
            # Генерация идентификатора сценария, если его нет
            if "script_id" not in script:
                writer_type = script.get("writer_type", "unknown")
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                script["script_id"] = f"{writer_type}_{timestamp}"
            
            # Сохранение сценария
            success = store_script(script)
            
            if success:
                info(f"Сценарий успешно сохранен с ID: {script['script_id']}")
                return {
                    "success": True,
                    "script_id": script["script_id"],
                    "message": "Сценарий успешно сохранен"
                }
            else:
                warning(f"Не удалось сохранить сценарий")
                return {
                    "success": False,
                    "message": "Не удалось сохранить сценарий"
                }
        
        except Exception as e:
            error(f"Ошибка при отправке сценария: {str(e)}")
            return {
                "success": False,
                "message": f"Ошибка при отправке сценария: {str(e)}"
            }
    
    def _submit_evaluation(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Отправка готовой оценки.
        
        Args:
            evaluation: Оценка сценария в JSON-формате.
            
        Returns:
            Dict[str, Any]: Результат отправки оценки.
        """
        info(f"Отправка оценки для сценария: {evaluation.get('script_id', '')}")
        
        try:
            from tools.storage_tools import store_evaluation
            
            # Сохранение оценки
            success = store_evaluation(evaluation)
            
            if success:
                info(f"Оценка успешно сохранена для сценария: {evaluation.get('script_id', '')}")
                return {
                    "success": True,
                    "message": "Оценка успешно сохранена"
                }
            else:
                warning(f"Не удалось сохранить оценку")
                return {
                    "success": False,
                    "message": "Не удалось сохранить оценку"
                }
        
        except Exception as e:
            error(f"Ошибка при отправке оценки: {str(e)}")
            return {
                "success": False,
                "message": f"Ошибка при отправке оценки: {str(e)}"
            }


# Функции для работы с ассистентами

@handle_exceptions
def create_scriptwriter_assistant(instructions: str = None, model: str = "gpt-4") -> str:
    """
    Создание ассистента-сценариста.
    
    Args:
        instructions: Инструкции для ассистента. НЕ ИСПОЛЬЗУЕТСЯ - промпты хранятся в UI OpenAI.
        model: Модель для ассистента.
        
    Returns:
        str: Идентификатор ассистента.
    """
    info("Создание ассистента-сценариста")
    
    # ВАЖНО: Промпты хранятся в UI OpenAI у каждого ассистента индивидуально
    # Инструкции НЕ отправляются из кода клиента
    instructions = "Базовые инструкции (реальные промпты в UI OpenAI)"
    
    # Создание инструментов
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_news_details",
                "description": "Получение деталей новости дня",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Дата в формате YYYY-MM-DD. Если не указана, используется текущая дата."
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "submit_script",
                "description": "Отправка готового сценария комикса. ОБЯЗАТЕЛЬНО вызови эту функцию с готовым сценарием в JSON формате.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "script": {
                            "type": "object",
                            "description": "Готовый сценарий комикса в JSON-формате с полями: title (заголовок), description (описание), panels (массив панелей), caption (подпись)",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Заголовок комикса"
                                },
                                "description": {
                                    "type": "string", 
                                    "description": "Общее описание комикса"
                                },
                                "panels": {
                                    "type": "array",
                                    "description": "Массив из 4 панелей комикса",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "description": {"type": "string"},
                                            "dialog": {"type": "array"},
                                            "narration": {"type": "string"}
                                        }
                                    }
                                },
                                "caption": {
                                    "type": "string",
                                    "description": "Подпись под комиксом"
                                }
                            },
                            "required": ["title", "description", "panels", "caption"]
                        }
                    },
                    "required": ["script"]
                }
            }
        }
    ]
    
    # Создание ассистента
    assistants_manager = AssistantsManager()
    assistant_id = assistants_manager.create_assistant(
        name="DailyComicBot Scriptwriter",
        instructions=instructions,
        tools=tools,
        model=model
    )
    
    info(f"Ассистент-сценарист успешно создан с ID: {assistant_id}")
    return assistant_id


@handle_exceptions
def create_jury_assistant(instructions: str = None, model: str = "gpt-4") -> str:
    """
    Создание ассистента-жюри.
    
    Args:
        instructions: Инструкции для ассистента. НЕ ИСПОЛЬЗУЕТСЯ - промпты хранятся в UI OpenAI.
        model: Модель для ассистента.
        
    Returns:
        str: Идентификатор ассистента.
    """
    info("Создание ассистента-жюри")
    
    # ВАЖНО: Промпты хранятся в UI OpenAI у каждого ассистента индивидуально
    # Инструкции НЕ отправляются из кода клиента
    instructions = "Базовые инструкции (реальные промпты в UI OpenAI)"
    
    # Создание инструментов
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_news_details",
                "description": "Получение деталей новости дня",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Дата в формате YYYY-MM-DD. Если не указана, используется текущая дата."
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_script_details",
                "description": "Получение деталей сценария комикса",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "script_id": {
                            "type": "string",
                            "description": "Идентификатор сценария"
                        }
                    },
                    "required": ["script_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "submit_evaluation",
                "description": "Отправка готовой оценки",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "evaluation": {
                            "type": "object",
                            "description": "Оценка сценария в JSON-формате"
                        }
                    },
                    "required": ["evaluation"]
                }
            }
        }
    ]
    
    # Создание ассистента
    assistants_manager = AssistantsManager()
    assistant_id = assistants_manager.create_assistant(
        name="DailyComicBot Jury",
        instructions=instructions,
        tools=tools,
        model=model
    )
    
    info(f"Ассистент-жюри успешно создан с ID: {assistant_id}")
    return assistant_id


@handle_exceptions
def invoke_scriptwriter(news: Dict[str, Any], writer_type: str) -> Optional[Dict[str, Any]]:
    """
    Вызов агента-сценариста для создания варианта комикса.
    
    Args:
        news: Информация о новости дня.
        writer_type: Тип сценариста (A, B, C, D, E).
        
    Returns:
        Optional[Dict[str, Any]]: Сгенерированный сценарий или None в случае ошибки.
    """
    info(f"Вызов агента-сценариста типа {writer_type}")
    
    try:
        # Инициализация менеджера ассистентов
        assistants_manager = AssistantsManager()
        
        # Создание потока для сценариста
        thread_name = f"scriptwriter_{writer_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        assistants_manager.create_thread(thread_name)
        
        # Формирование запроса - отправляем только текст новости
        news_text = f"Заголовок: {news.get('title', '')}\n\nСодержание: {news.get('content', '')}"
        
        # Добавление сообщения в поток
        assistants_manager.add_message(
            thread_name=thread_name,
            content=news_text
        )
        
        # Определение имени ассистента
        assistant_name = f"scriptwriter_{writer_type}"
        instructions = None
        
        # Проверка наличия специфичного ассистента для данного типа
        if assistant_name not in assistants_manager.assistants:
            # Если специфичного ассистента нет, используем любого доступного
            if assistants_manager.scriptwriter_assistants:
                # Берем первого доступного ассистента-сценариста
                assistant_type, assistant_id = assistants_manager.scriptwriter_assistants[0]
                assistant_name = f"scriptwriter_{assistant_type}"
                info(f"Используем ассистента-сценариста типа {assistant_type} вместо {writer_type}")
            else:
                error(f"Не найдено ни одного ассистента-сценариста")
                return None
            
            # Добавляем инструкции для переключения на нужный тип
            instructions = f"Ты - сценарист типа {writer_type}. Создай сценарий комикса на основе предоставленной новости. КРИТИЧЕСКИ ВАЖНО: Весь сценарий должен быть написан ТОЛЬКО на русском языке! Заголовки, описания, диалоги, подписи - всё на русском!"
        
        # Запуск ассистента
        response = assistants_manager.run_assistant(
            thread_name=thread_name,
            assistant_name=assistant_name,
            instructions=instructions
        )
        
        # Парсинг ответа
        if response and "content" in response:
            try:
                # Сначала пробуем распарсить как JSON
                script = json.loads(response["content"])
            except json.JSONDecodeError:
                # Если не удалось, парсим как текст
                info(f"Ответ не в формате JSON, пробуем парсить как текст")
                script = parse_text_script(response["content"])
                
                if not script:
                    error(f"Не удалось распарсить ответ от ассистента: {response['content']}")
                    return None
            
            # Проверка наличия всех необходимых полей
            required_fields = ["title", "description", "panels", "caption"]
            for field in required_fields:
                if field not in script:
                    warning(f"В сценарии отсутствует поле '{field}'")
                    if field == "title":
                        script[field] = "Без заголовка"
                    elif field == "description":
                        script[field] = "Без описания"
                    elif field == "panels":
                        script[field] = []
                    elif field == "caption":
                        script[field] = "Без подписи"
            
            # Добавление метаданных
            script["writer_type"] = writer_type
            from config import SCRIPTWRITERS
            script["writer_name"] = SCRIPTWRITERS[writer_type]["name"]
            
            return script
        
        warning(f"Не удалось получить ответ от ассистента")
        return None
    
    except Exception as e:
        error(f"Ошибка при вызове агента-сценариста {writer_type}: {str(e)}")
        return None


@handle_exceptions
def invoke_jury(script: Dict[str, Any], jury_type: str, news: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Вызов агента-жюри для оценки сценария.
    
    Args:
        script: Сценарий для оценки.
        jury_type: Тип жюри (A, B, C, D, E).
        news: Информация о новости дня.
        
    Returns:
        Optional[Dict[str, Any]]: Результат оценки или None в случае ошибки.
    """
    info(f"Вызов агента-жюри типа {jury_type} для оценки сценария {script.get('script_id', 'без ID')}")
    
    try:
        # Инициализация менеджера ассистентов
        assistants_manager = AssistantsManager()
        
        # Создание потока для жюри
        thread_name = f"jury_{jury_type}_{script.get('script_id', 'unknown')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        assistants_manager.create_thread(thread_name)
        
        # Формирование запроса
        # Проверяем и модифицируем сценарий, чтобы добавить предупреждения для панелей без описания
        script_copy = script.copy()
        
        # Проверяем панели
        if "panels" in script_copy:
            for i, panel in enumerate(script_copy["panels"]):
                # Проверка наличия описания
                description = panel.get('description', '')
                if not description or description == 'Нет описания':
                    # Если описания нет, добавляем предупреждение
                    panel['description'] = "[Описание панели отсутствует или не предоставлено]"
                    
                    # Проверяем, есть ли диалоги или нарративы
                    has_dialog = bool(panel.get('dialog'))
                    has_narration = bool(panel.get('narration'))
                    
                    if not has_dialog and not has_narration:
                        # Если нет ни описания, ни диалогов, ни нарративов, добавляем предупреждение
                        panel['warning'] = "ВНИМАНИЕ: Для этой панели не предоставлено ни описания, ни диалогов, ни текста от автора. Это может затруднить оценку сценария. Пожалуйста, учтите это при выставлении оценок."
        
        request = {
            "jury_type": jury_type,
            "script": script_copy,
            "news": news
        }
        
        # Добавление сообщения в поток
        assistants_manager.add_message(
            thread_name=thread_name,
            content=json.dumps(request)
        )
        
        # Определение имени ассистента
        assistant_name = f"jury_{jury_type}"
        instructions = None
        
        # Проверка наличия специфичного ассистента для данного типа
        if assistant_name not in assistants_manager.assistants:
            # Если специфичного ассистента нет, используем любого доступного
            if assistants_manager.jury_assistants:
                # Берем первого доступного ассистента-жюри
                assistant_type, assistant_id = assistants_manager.jury_assistants[0]
                assistant_name = f"jury_{assistant_type}"
                info(f"Используем ассистента-жюри типа {assistant_type} вместо {jury_type}")
            else:
                error(f"Не найдено ни одного ассистента-жюри")
                return None
            
            # Добавляем инструкции для переключения на нужный тип
            instructions = f"Ты - член жюри типа {jury_type}. Оцени предоставленный сценарий комикса."
        
        # Запуск ассистента
        response = assistants_manager.run_assistant(
            thread_name=thread_name,
            assistant_name=assistant_name,
            instructions=instructions
        )
        
        # Парсинг ответа
        if response and "content" in response:
            try:
                # Сначала пробуем распарсить как JSON
                evaluation = json.loads(response["content"])
            except json.JSONDecodeError:
                # Если не удалось, пробуем распарсить как текстовый формат
                info(f"Ответ не в формате JSON, пробуем парсить как текстовую оценку")
                evaluation = parse_text_evaluation(response["content"])
                
                if not evaluation or not evaluation.get("scores"):
                    error(f"Не удалось распарсить ответ от ассистента-жюри: {response['content'][:500]}...")
                    return None
                
                info(f"Успешно распарсена текстовая оценка с итоговым баллом: {evaluation.get('total_score', 0)}")
            
            # Проверка наличия всех необходимых полей
            required_fields = ["scores", "comments", "total_score", "overall_comment"]
            for field in required_fields:
                if field not in evaluation:
                    warning(f"В оценке отсутствует поле '{field}'")
                    if field == "scores":
                        evaluation[field] = {
                            "relevance": 0,
                            "originality": 0,
                            "humor": 0,
                            "structure": 0,
                            "visual": 0
                        }
                    elif field == "comments":
                        evaluation[field] = {
                            "relevance": "",
                            "originality": "",
                            "humor": "",
                            "structure": "",
                            "visual": ""
                        }
                    elif field == "total_score":
                        evaluation[field] = 0
                    else:
                        evaluation[field] = f"Поле '{field}' отсутствует"
            
            # Добавление метаданных
            evaluation["jury_type"] = jury_type
            from config import SCRIPTWRITERS
            evaluation["jury_name"] = SCRIPTWRITERS[jury_type]["name"]
            evaluation["script_id"] = script.get("script_id", "unknown")
            
            return evaluation
        
        warning(f"Не удалось получить ответ от ассистента")
        return None
    
    except Exception as e:
        error(f"Ошибка при вызове агента-жюри {jury_type}: {str(e)}")
        return None
