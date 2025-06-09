"""
Модуль агента-менеджера для проекта DailyComicBot.
Отвечает за координацию всего процесса создания и публикации комикса.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import statistics

# Импорт модулей проекта
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import logger, handle_exceptions, measure_execution_time, important_logger
from tools import (
    get_top_news, generate_comic_image, store_daily_data, load_daily_data,
    publish_to_all_platforms, format_caption, store_news
)
import config
from config import SCRIPTWRITERS, COMIC_PANELS


class ManagerAgent:
    """
    Агент-менеджер, координирующий весь процесс создания и публикации комикса.
    """
    
    def __init__(self):
        """Инициализация агента-менеджера."""
        self.news = None
        self.scripts = []
        self.evaluations = {}
        self.winner_script = None
        self.winner_score = 0
        self.image_path = None
        self.publication_results = None
        
        logger.info("Агент-менеджер инициализирован")
    
    @measure_execution_time
    def collect_news(self, force_new_news=False) -> Dict[str, Any]:
        """
        Сбор главной новости дня.
        
        Args:
            force_new_news (bool): Принудительно получить новую новость, игнорируя существующую.
        
        Returns:
            Dict[str, Any]: Информация о главной новости дня.
        """
        logger.info("Начало сбора новостей")
        
        try:
            # Логирование запроса в Perplexity
            important_logger.log_perplexity_request()
            
            # Получение главной новости дня
            self.news = get_top_news(force_new=force_new_news)
            
            # Проверка, что новость получена успешно
            if self.news and isinstance(self.news, dict) and 'title' in self.news:
                # Сохранение новости в файл
                store_news(self.news)
                
                # Логирование выбранной темы
                logger.log_theme(self.news['title'])
                
                # Логирование получения ответа от Perplexity
                important_logger.log_perplexity_response(self.news)
                
                return self.news
            else:
                logger.error("Получена некорректная новость")
                return None
        except Exception as e:
            logger.error(f"Ошибка при сборе новостей: {str(e)}")
            self.news = None
            return None
    
    @measure_execution_time
    def generate_scripts(self) -> List[Dict[str, Any]]:
        """
        Генерация сценариев комиксов.
        
        Returns:
            List[Dict[str, Any]]: Список сгенерированных сценариев.
        """
        logger.info("Начало генерации сценариев")
        
        # Проверка наличия новости
        if not self.news:
            logger.error("Невозможно сгенерировать сценарии: новость не получена")
            return []
        
        self.scripts = []
        
        # Параллельная генерация сценариев
        import concurrent.futures
        
        # Создаем список задач для параллельного выполнения
        script_tasks = []
        for writer_type, writer_info in SCRIPTWRITERS.items():
            logger.info(f"Подготовка генерации сценариев для сценариста {writer_type}: {writer_info['name']}")
            
            # Создаем две задачи для каждого сценариста
            for i in range(2):
                script_id = f"{writer_type}_{i+1}"
                script_tasks.append((writer_type, writer_info, script_id, i+1))
                
                # Логирование запроса к сценаристу
                important_logger.log_scriptwriter_request(writer_type, writer_info["name"])
        
        # Выполняем задачи параллельно
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(SCRIPTWRITERS)) as executor:
            # Запускаем задачи на выполнение
            future_to_task = {
                executor.submit(self.invoke_scriptwriter, self.news, task[0]): task
                for task in script_tasks
            }
            
            # Получаем результаты по мере их готовности
            for future in concurrent.futures.as_completed(future_to_task):
                writer_type, writer_info, script_id, script_num = future_to_task[future]
                try:
                    script = future.result()
                    if script:
                        # Добавление метаданных к сценарию
                        script["writer_type"] = writer_type
                        script["writer_name"] = writer_info["name"]
                        script["script_id"] = script_id
                        
                        # Добавление сценария в список
                        self.scripts.append(script)
                        
                        # Логирование создания сценария
                        logger.log_script_creation(
                            writer_info["name"],
                            script['script_id'],
                            script.get('title', 'Без названия')
                        )
                        
                        # Логирование получения ответа от сценариста
                        important_logger.log_scriptwriter_response(writer_type, writer_info["name"], script)
                    else:
                        logger.warning(f"Не удалось создать сценарий {script_num} для сценариста {writer_type}")
                except Exception as e:
                    logger.error(f"Ошибка при генерации сценария {script_num} для сценариста {writer_type}: {str(e)}")
        
        logger.info(f"Сгенерировано {len(self.scripts)} сценариев")
        return self.scripts
    
    def invoke_scriptwriter(self, news: Dict[str, Any], writer_type: str) -> Optional[Dict[str, Any]]:
        """
        Вызов агента-сценариста для создания варианта комикса.
        
        Args:
            news (Dict[str, Any]): Информация о новости дня.
            writer_type (str): Тип сценариста (A, B, C, D, E).
            
        Returns:
            Optional[Dict[str, Any]]: Сгенерированный сценарий или None в случае ошибки.
        """
        try:
            # Проверка, использовать ли Assistants API
            if hasattr(config, 'USE_ASSISTANTS_API') and config.USE_ASSISTANTS_API:
                # Импорт функции для работы с Assistants API
                from utils.assistants_api import invoke_scriptwriter as assistants_invoke_scriptwriter
                
                # Вызов сценариста через Assistants API
                logger.info(f"Вызов агента-сценариста типа {writer_type} через Assistants API")
                return assistants_invoke_scriptwriter(news, writer_type)
            
            # Если Assistants API не используется, используем generate_jokes.py
            logger.info(f"Вызов агента-сценариста типа {writer_type} через generate_jokes.py")
            
            # Импортируем функцию main из модуля generate_jokes
            sys.path.append(str(Path(__file__).resolve().parent.parent))
            from generate_jokes import main as generate_jokes_main
            
            # Вызываем функцию generate_jokes_main с указанным типом сценариста
            script = generate_jokes_main(writer_type=writer_type)
            
            if not script:
                error_msg = f"Не удалось сгенерировать сценарий через generate_jokes.py для сценариста типа {writer_type}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            return script
        
        except Exception as e:
            error_msg = f"Ошибка при вызове агента-сценариста {writer_type}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    @measure_execution_time
    def evaluate_scripts(self) -> Dict[str, Dict[str, Any]]:
        """
        Оценка сценариев комиксов.
        
        Returns:
            Dict[str, Dict[str, Any]]: Словарь с оценками сценариев.
        """
        logger.info("Начало оценки сценариев")
        
        # Проверка наличия сценариев
        if not self.scripts:
            logger.error("Невозможно оценить сценарии: список сценариев пуст")
            return {}
        
        self.evaluations = {}
        
        # Подготовка структуры для оценок
        for script in self.scripts:
            # Генерация идентификатора сценария, если его нет
            if "script_id" not in script:
                script["script_id"] = f"script_{len(self.evaluations) + 1}"
            
            script_id = script["script_id"]
            self.evaluations[script_id] = {
                "script": script,
                "evaluations": {},
                "average_score": 0,
                "scores_std_dev": 0
            }
        
        # Параллельная оценка сценариев
        import concurrent.futures
        
        # Создаем список задач для параллельного выполнения
        evaluation_tasks = []
        for script in self.scripts:
            script_id = script["script_id"]
            for jury_type in SCRIPTWRITERS.keys():
                # Логирование запроса к жюри
                important_logger.log_jury_request(
                    jury_type, 
                    SCRIPTWRITERS[jury_type]["name"], 
                    script_id, 
                    script["writer_name"]
                )
                
                # Добавляем задачу в список
                evaluation_tasks.append((script, jury_type, script_id))
        
        # Выполняем задачи параллельно
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(SCRIPTWRITERS)) as executor:
            # Запускаем задачи на выполнение
            future_to_task = {
                executor.submit(self.invoke_jury, task[0], task[1]): task
                for task in evaluation_tasks
            }
            
            # Получаем результаты по мере их готовности
            for future in concurrent.futures.as_completed(future_to_task):
                script, jury_type, script_id = future_to_task[future]
                try:
                    evaluation = future.result()
                    if evaluation:
                        self.evaluations[script_id]["evaluations"][jury_type] = evaluation
                        # Логирование оценки сценария
                        logger.log_script_evaluation(
                            SCRIPTWRITERS[jury_type]["name"],
                            script_id,
                            evaluation['total_score']
                        )
                        
                        # Логирование получения оценки от жюри
                        important_logger.log_jury_response(
                            jury_type, 
                            SCRIPTWRITERS[jury_type]["name"], 
                            script_id, 
                            script["writer_name"], 
                            evaluation['total_score']
                        )
                    else:
                        logger.warning(f"Не удалось получить оценку сценария {script_id} от жюри {jury_type}")
                except Exception as e:
                    logger.error(f"Ошибка при получении оценки от жюри {jury_type} для сценария {script_id}: {str(e)}")
        
        # Вычисление средней оценки и стандартного отклонения для каждого сценария
        for script_id, data in self.evaluations.items():
            scores = [e["total_score"] for e in data["evaluations"].values()]
            if scores:
                data["average_score"] = sum(scores) / len(scores)
                data["scores_std_dev"] = statistics.stdev(scores) if len(scores) > 1 else 0
                
                logger.info(f"Сценарий {script_id} получил среднюю оценку {data['average_score']:.2f}/100")
            else:
                logger.warning(f"Сценарий {script_id} не получил ни одной оценки")
        
        logger.info(f"Оценено {len(self.evaluations)} сценариев")
        return self.evaluations
    
    def invoke_jury(self, script: Dict[str, Any], jury_type: str) -> Optional[Dict[str, Any]]:
        """
        Вызов агента-жюри для оценки сценария.
        
        Args:
            script (Dict[str, Any]): Сценарий для оценки.
            jury_type (str): Тип жюри (A, B, C, D, E).
            
        Returns:
            Optional[Dict[str, Any]]: Результат оценки или None в случае ошибки.
        """
        try:
            # Проверка, использовать ли Assistants API
            if hasattr(config, 'USE_ASSISTANTS_API') and config.USE_ASSISTANTS_API:
                # Импорт функции для работы с Assistants API
                from utils.assistants_api import invoke_jury as assistants_invoke_jury
                
                # Вызов жюри через Assistants API
                logger.info(f"Вызов агента-жюри типа {jury_type} через Assistants API")
                return assistants_invoke_jury(script, jury_type, self.news)
            
            # Если Assistants API не используется, используем OpenAI API напрямую
            logger.info(f"Вызов агента-жюри типа {jury_type} через OpenAI API")
            
            # Проверка наличия API-ключа OpenAI
            api_key_path = Path(__file__).resolve().parent.parent / ".env"
            api_key = None
            
            # Пытаемся загрузить API-ключ из .env файла
            if api_key_path.exists():
                with open(api_key_path, "r") as f:
                    for line in f:
                        if line.startswith("OPENAI_API_KEY="):
                            api_key = line.strip().split("=")[1].strip('"').strip("'")
                            break
            
            # Если API-ключ не найден, пытаемся получить его из переменной окружения
            if not api_key:
                api_key = os.environ.get("OPENAI_API_KEY")
            
            # Если API-ключ найден, используем официальный API
            if api_key:
                try:
                    # Импортируем библиотеку OpenAI
                    import openai
                    
                    # Настраиваем клиент OpenAI
                    client = openai.OpenAI(api_key=api_key)
                    
                    # Формирование системного промпта
                    system_prompt = f"""Ты - член жюри комиксов с именем {SCRIPTWRITERS[jury_type]['name']}. 
{SCRIPTWRITERS[jury_type]['description']}
Твоя задача - оценить сценарий комикса по следующим критериям:
1. Релевантность (0-20 баллов): Насколько комикс связан с новостью дня.
2. Оригинальность (0-20 баллов): Насколько идея комикса оригинальна и креативна.
3. Юмористический потенциал (0-30 баллов): Насколько комикс смешной и остроумный.
4. Структура и логика (0-15 баллов): Насколько хорошо выстроен сюжет комикса.
5. Визуальный потенциал (0-15 баллов): Насколько хорошо комикс можно представить визуально.

Оцени сценарий по каждому критерию и дай общую оценку от 0 до 100 баллов."""
                    
                    # Формирование пользовательского промпта
                    news_title = self.news.get("title", "")
                    news_content = self.news.get("content", "")
                    
                    user_prompt = f"""Новость дня:
Заголовок: {news_title}
Содержание: {news_content}

Сценарий комикса:
Заголовок: {script.get('title', 'Без заголовка')}
Автор: {script.get('writer_name', 'Неизвестный автор')}
Описание: {script.get('description', 'Нет описания')}

Панели:
"""
                    
                    # Проверяем формат сценария
                    if script.get('format') == 'text':
                        # Если сценарий в текстовом формате, используем его напрямую
                        user_prompt += script.get('content', '')
                    else:
                        # Если сценарий в JSON формате, форматируем его
                        # Добавление панелей
                        for i, panel in enumerate(script.get('panels', [])):
                            user_prompt += f"Панель {i+1}:\n"
                            
                            # Проверка наличия описания
                            description = panel.get('description', '')
                            if not description or description == 'Нет описания':
                                # Если описания нет, добавляем предупреждение
                                user_prompt += "Описание: [Описание панели отсутствует или не предоставлено]\n"
                                
                                # Проверяем, есть ли диалоги или нарративы
                                has_dialog = bool(panel.get('dialog'))
                                has_narration = bool(panel.get('narration'))
                                
                                if not has_dialog and not has_narration:
                                    # Если нет ни описания, ни диалогов, ни нарративов, добавляем предупреждение
                                    user_prompt += "ВНИМАНИЕ: Для этой панели не предоставлено ни описания, ни диалогов, ни текста от автора.\n"
                                    user_prompt += "Это может затруднить оценку сценария. Пожалуйста, учтите это при выставлении оценок.\n"
                            else:
                                # Если описание есть, добавляем его
                                user_prompt += f"Описание: {description}\n"
                            
                            # Добавление диалогов (пропускаем служебные записи)
                            if panel.get('dialog'):
                                real_dialogs = []
                                for dialog in panel['dialog']:
                                    character = dialog.get('character', '')
                                    text = dialog.get('text', '')
                                    note = dialog.get('note', '')
                                    
                                    # Пропускаем служебные записи
                                    if character in ['Изображение', 'Диалоги', 'Текст от автора']:
                                        continue
                                    
                                    real_dialogs.append(dialog)
                                
                                if real_dialogs:
                                    user_prompt += "Диалоги:\n"
                                    for dialog in real_dialogs:
                                        character = dialog.get('character', '')
                                        text = dialog.get('text', '')
                                        note = dialog.get('note', '')
                                        
                                        if note:
                                            user_prompt += f"- {character} ({note}): \"{text}\"\n"
                                        else:
                                            user_prompt += f"- {character}: \"{text}\"\n"
                            
                            # Добавление текста от автора
                            if panel.get('narration'):
                                user_prompt += f"Текст от автора: {panel['narration']}\n"
                            
                            user_prompt += "\n"
                    
                    # Добавление подписи
                    user_prompt += f"Подпись: {script.get('caption', 'Нет подписи')}\n\n"
                    
                    user_prompt += """Оцени этот сценарий по указанным критериям. 

ВАЖНО: Используй ТОЧНО этот формат для ответа (как в твоих инструкциях):

Релевантность: [X/20]
- [Комментарий]

Оригинальность: [X/20]
- [Комментарий]

Юмористический потенциал: [X/30]
- [Комментарий]

Структура и логика: [X/15]
- [Комментарий]

Визуальный потенциал: [X/15]
- [Комментарий]

Итоговая оценка: [Сумма/100]

Общий комментарий: [Краткое обоснование итоговой оценки]"""
                    
                    # Логирование отправляемых данных
                    logger.info(f"=== ОТПРАВКА ЗАПРОСА К ЖЮРИ {jury_type} ===")
                    logger.info(f"Системный промпт (первые 200 символов): {system_prompt[:200]}...")
                    logger.info(f"Пользовательский промпт (первые 500 символов): {user_prompt[:500]}...")
                    logger.info(f"Длина пользовательского промпта: {len(user_prompt)} символов")
                    
                    # Отправляем запрос к API
                    response = client.chat.completions.create(
                        model="gpt-4",  # Используем GPT-4 для лучшего качества
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    # Получаем ответ от API
                    response_text = response.choices[0].message.content
                    
                    # Логирование полученного ответа
                    logger.info(f"=== ОТВЕТ ОТ ЖЮРИ {jury_type} ===")
                    logger.info(f"Полный ответ: {response_text}")
                    logger.info(f"Длина ответа: {len(response_text)} символов")
                    
                    # Парсим ответ для извлечения оценок
                    scores = {
                        "relevance": 0,
                        "originality": 0,
                        "humor": 0,
                        "structure": 0,
                        "visual": 0
                    }
                    
                    total_score = 0
                    comment = ""
                    
                    # Улучшенный поиск оценок в тексте с использованием регулярных выражений
                    import re
                    
                    logger.info(f"=== ПАРСИНГ ОЦЕНОК ОТ ЖЮРИ {jury_type} ===")
                    
                    # Поиск всех числовых оценок в формате из инструкций жюри (включая квадратные скобки)
                    score_patterns = [
                        r'релевантность[:\s]*\[?(\d+)(?:/\d+)?\]?',
                        r'оригинальность[:\s]*\[?(\d+)(?:/\d+)?\]?',
                        r'юмор(?:истический\s+потенциал)?[:\s]*\[?(\d+)(?:/\d+)?\]?',
                        r'структура(?:\s+и\s+логика)?[:\s]*\[?(\d+)(?:/\d+)?\]?',
                        r'визуал(?:ьный\s+потенциал)?[:\s]*\[?(\d+)(?:/\d+)?\]?'
                    ]
                    
                    score_keys = ["relevance", "originality", "humor", "structure", "visual"]
                    
                    for i, pattern in enumerate(score_patterns):
                        match = re.search(pattern, response_text, re.IGNORECASE)
                        if match:
                            try:
                                score = int(match.group(1))
                                scores[score_keys[i]] = min(max(score, 0), 20 if i < 2 else (30 if i == 2 else 15))
                                logger.info(f"Найдена оценка {score_keys[i]}: {score} -> {scores[score_keys[i]]}")
                            except Exception as e:
                                logger.warning(f"Ошибка при парсинге оценки {score_keys[i]}: {str(e)}")
                        else:
                            logger.warning(f"Не найдена оценка для {score_keys[i]} по паттерну: {pattern}")
                    
                    # Поиск итоговой оценки (включая квадратные скобки)
                    total_patterns = [
                        r'итоговая оценка[:\s]*\[?(\d+)(?:/\d+)?\]?',
                        r'общая оценка[:\s]*\[?(\d+)(?:/\d+)?\]?',
                        r'итого[:\s]*\[?(\d+)(?:/\d+)?\]?',
                        r'всего[:\s]*\[?(\d+)(?:/\d+)?\]?'
                    ]
                    
                    for pattern in total_patterns:
                        match = re.search(pattern, response_text, re.IGNORECASE)
                        if match:
                            try:
                                total_score = int(match.group(1))
                                logger.info(f"Найдена итоговая оценка: {total_score}")
                                break
                            except Exception as e:
                                logger.warning(f"Ошибка при парсинге итоговой оценки: {str(e)}")
                        else:
                            logger.warning(f"Не найдена итоговая оценка по паттерну: {pattern}")
                    
                    # Поиск общего комментария
                    comment_patterns = [
                        r'общий комментарий[:\s]*(.+?)(?:\n|$)',
                        r'комментарий[:\s]*(.+?)(?:\n|$)',
                        r'заключение[:\s]*(.+?)(?:\n|$)'
                    ]
                    
                    for pattern in comment_patterns:
                        match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
                        if match:
                            comment = match.group(1).strip()
                            logger.info(f"Найден комментарий: {comment[:100]}...")
                            break
                    
                    # Если итоговая оценка не найдена, вычисляем ее как сумму оценок по критериям
                    if total_score == 0:
                        total_score = sum(scores.values())
                        logger.info(f"Итоговая оценка вычислена как сумма: {total_score} = {scores}")
                    
                    # Если комментарий не найден, используем весь текст ответа
                    if not comment:
                        comment = response_text
                        logger.info("Комментарий не найден, используется весь ответ")
                    
                    logger.info(f"=== ФИНАЛЬНЫЕ ОЦЕНКИ ОТ ЖЮРИ {jury_type} ===")
                    logger.info(f"Оценки по критериям: {scores}")
                    logger.info(f"Итоговая оценка: {total_score}")
                    
                    # Создание объекта оценки
                    evaluation = {
                        "jury_type": jury_type,
                        "script_id": script["script_id"],
                        "scores": scores,
                        "total_score": total_score,
                        "comment": comment
                    }
                    
                    # Сохранение оценки в файл
                    from tools.storage_tools import store_evaluation
                    store_evaluation(evaluation, script["script_id"])
                    
                    return evaluation
                    
                except ImportError:
                    error_msg = "Библиотека OpenAI не установлена. Установите ее с помощью команды: pip install openai"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                    
                except Exception as e:
                    error_msg = f"Ошибка при вызове OpenAI API: {str(e)}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
            else:
                error_msg = "API-ключ OpenAI не найден. Добавьте его в файл .env или переменную окружения OPENAI_API_KEY"
                logger.error(error_msg)
                raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"Ошибка при вызове агента-жюри {jury_type}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    @measure_execution_time
    def select_top_scripts(self, top_count: int = 4) -> List[Dict[str, Any]]:
        """
        Выбор топ сценариев для генерации изображений.
        
        Args:
            top_count (int): Количество лучших сценариев для выбора.
        
        Returns:
            List[Dict[str, Any]]: Список лучших сценариев.
        """
        logger.info(f"Начало выбора топ-{top_count} сценариев")
        
        # Проверка наличия оценок
        if not self.evaluations:
            logger.error("Невозможно выбрать лучшие сценарии: нет оценок")
            return []
        
        # Сортировка сценариев по средней оценке (по убыванию)
        sorted_scripts = sorted(
            self.evaluations.items(),
            key=lambda x: (x[1]["average_score"], -x[1]["scores_std_dev"]),
            reverse=True
        )
        
        # Выбор топ сценариев
        top_scripts = []
        for i, (script_id, data) in enumerate(sorted_scripts[:top_count]):
            script_info = {
                "script_id": script_id,
                "script": data["script"],
                "average_score": data["average_score"],
                "std_dev": data["scores_std_dev"],
                "rank": i + 1
            }
            top_scripts.append(script_info)
            
            # Логирование выбора топ сценария
            logger.info(f"Топ-{i+1} сценарий: {script_id} ({data['average_score']:.1f}/100)")
        
        # Устанавливаем лучший сценарий как winner для совместимости
        if top_scripts:
            self.winner_script = top_scripts[0]["script"]
            self.winner_score = top_scripts[0]["average_score"]
            
            # Логирование выбора лучшего сценария
            important_logger.log_winner_selection(
                top_scripts[0]["script_id"],
                top_scripts[0]["script"]["writer_name"],
                top_scripts[0]["script"]["title"],
                top_scripts[0]["average_score"]
            )
        
        return top_scripts

    def select_winner(self) -> Optional[Dict[str, Any]]:
        """
        Выбор сценария-победителя (для совместимости со старым API).
        
        Returns:
            Optional[Dict[str, Any]]: Информация о сценарии-победителе или None в случае ошибки.
        """
        top_scripts = self.select_top_scripts(1)
        return top_scripts[0] if top_scripts else None
    
    @measure_execution_time
    def create_images_for_top_scripts(self, top_scripts: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Создание изображений для топ сценариев параллельно.
        
        Args:
            top_scripts (List[Dict[str, Any]], optional): Список топ сценариев. 
                Если None, будет вызван select_top_scripts().
        
        Returns:
            List[Dict[str, Any]]: Список результатов с путями к изображениям.
        """
        logger.info("Начало создания изображений для топ сценариев")
        
        # Получаем топ сценарии, если не переданы
        if top_scripts is None:
            top_scripts = self.select_top_scripts(4)
        
        if not top_scripts:
            logger.error("Невозможно создать изображения: нет топ сценариев")
            return []
        
        # Параллельная генерация изображений
        import concurrent.futures
        
        results = []
        
        # Создаем список задач для параллельного выполнения
        image_tasks = []
        for script_info in top_scripts:
            script = script_info["script"]
            script_id = script_info["script_id"]
            rank = script_info["rank"]
            
            # Формирование промпта для генерации изображения
            prompt = self._create_image_prompt(script)
            filename = f"comic_{datetime.now().strftime('%Y%m%d')}_top{rank}_{script_id}.png"
            
            image_tasks.append((script_info, prompt, filename))
        
        # Выполняем задачи параллельно
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Запускаем задачи на выполнение
            future_to_task = {
                executor.submit(self._generate_single_image, task[1], task[2]): task
                for task in image_tasks
            }
            
            # Получаем результаты по мере их готовности
            for future in concurrent.futures.as_completed(future_to_task):
                script_info, prompt, filename = future_to_task[future]
                try:
                    image_path = future.result()
                    
                    result = {
                        "script_info": script_info,
                        "image_path": image_path,
                        "success": bool(image_path)
                    }
                    
                    if image_path:
                        # Логирование создания изображения
                        logger.log_image_creation(
                            script_info["script_id"],
                            image_path
                        )
                        
                        # Логирование создания изображения в важных событиях
                        important_logger.log_image_creation(
                            script_info["script_id"],
                            script_info["script"]["writer_name"],
                            image_path
                        )
                        
                        logger.info(f"Изображение для топ-{script_info['rank']} сценария создано: {image_path}")
                    else:
                        logger.error(f"Не удалось создать изображение для топ-{script_info['rank']} сценария")
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Ошибка при создании изображения для сценария {script_info['script_id']}: {str(e)}")
                    results.append({
                        "script_info": script_info,
                        "image_path": None,
                        "success": False,
                        "error": str(e)
                    })
        
        # Сортируем результаты по рангу
        results.sort(key=lambda x: x["script_info"]["rank"])
        
        # Устанавливаем лучшее изображение как основное для совместимости
        if results and results[0]["success"]:
            self.image_path = results[0]["image_path"]
        
        logger.info(f"Создано {len([r for r in results if r['success']])} из {len(results)} изображений")
        return results

    def _generate_single_image(self, prompt: str, filename: str) -> Optional[str]:
        """
        Генерация одного изображения.
        
        Args:
            prompt (str): Промпт для генерации.
            filename (str): Имя файла.
        
        Returns:
            Optional[str]: Путь к созданному изображению или None.
        """
        try:
            return generate_comic_image(
                prompt=prompt,
                num_panels=COMIC_PANELS,
                quality="high",
                filename=filename
            )
        except Exception as e:
            logger.error(f"Ошибка при генерации изображения {filename}: {str(e)}")
            return None

    @measure_execution_time
    def create_image(self) -> Optional[str]:
        """
        Создание изображения на основе сценария-победителя (для совместимости).
        
        Returns:
            Optional[str]: Путь к созданному изображению или None в случае ошибки.
        """
        logger.info("Начало создания изображения")
        
        # Проверка наличия сценария-победителя
        if not self.winner_script:
            logger.error("Невозможно создать изображение: нет сценария-победителя")
            return None
        
        try:
            # Формирование промпта для генерации изображения
            prompt = self._create_image_prompt(self.winner_script)
            
            # Генерация изображения
            self.image_path = generate_comic_image(
                prompt=prompt,
                num_panels=COMIC_PANELS,
                quality="high",
                filename=f"comic_{datetime.now().strftime('%Y%m%d')}.png"
            )
            
            # Логирование создания изображения
            logger.log_image_creation(
                self.winner_script["script_id"],
                self.image_path
            )
            
            # Логирование создания изображения в важных событиях
            important_logger.log_image_creation(
                self.winner_script["script_id"],
                self.winner_script["writer_name"],
                self.image_path
            )
            return self.image_path
        
        except Exception as e:
            logger.error(f"Ошибка при создании изображения: {str(e)}")
            return None
    
    def _create_image_prompt(self, script: Dict[str, Any]) -> str:
        """
        Создание промпта для генерации изображения на основе сценария.
        
        Args:
            script (Dict[str, Any]): Сценарий комикса.
            
        Returns:
            str: Промпт для генерации изображения.
        """
        # Проверяем формат сценария
        if script.get('format') == 'text':
            # Если сценарий в текстовом формате, используем его напрямую
            # Базовая информация
            title = script.get("title", "Комикс")
            
            # Формирование промпта
            prompt = f"Создай комикс на тему: {title}\n\n"
            prompt += script.get('content', '')
        else:
            # Если сценарий в JSON формате, форматируем его
            # Базовая информация
            title = script.get("title", "Комикс")
            description = script.get("description", "")
            panels = script.get("panels", [])
            caption = script.get("caption", "")
            
            # Формирование промпта
            prompt = f"Создай комикс из {len(panels)} панелей на тему: {title}\n\n"
            prompt += f"Общее описание: {description}\n\n"
            
            # Добавление описания каждой панели
            for i, panel in enumerate(panels):
                prompt += f"Панель {i+1}:\n"
                prompt += f"Изображение: {panel.get('description', '')}\n"
                
                # Добавление диалогов (пропускаем служебные записи)
                dialogs = panel.get("dialog", [])
                if dialogs:
                    real_dialogs = []
                    for dialog in dialogs:
                        character = dialog.get("character", "")
                        text = dialog.get("text", "")
                        note = dialog.get("note", "")
                        
                        # Пропускаем служебные записи
                        if character in ['Изображение', 'Диалоги', 'Текст от автора']:
                            continue
                        
                        real_dialogs.append(dialog)
                    
                    if real_dialogs:
                        prompt += "Диалоги:\n"
                        for dialog in real_dialogs:
                            character = dialog.get("character", "")
                            text = dialog.get("text", "")
                            note = dialog.get("note", "")
                            
                            if note:
                                prompt += f"- {character} ({note}): \"{text}\"\n"
                            else:
                                prompt += f"- {character}: \"{text}\"\n"
                
                # Текст от автора не добавляется в промпт для изображения
                # так как он уже включен в диалоги и не должен отображаться на комиксе
                
                prompt += "\n"
            
            # Добавление подписи
            prompt += f"Подпись под комиксом: {caption}\n\n"
        
        # Добавление инструкций по стилю и формату
        prompt += """
    Стиль: Современный комикс с четкими линиями и яркими цветами.
    Формат: Изображение должно быть разделено на 4 равные панели, расположенные в сетке 2x2.
    Каждая панель должна иметь четкую рамку и содержать часть истории.
    Добавь текстовые пузыри с диалогами персонажей, где это необходимо.
    ОЧЕНЬ ВАЖНО: Оставь как минимум 20% высоты изображения внизу для подписи с текстом комикса.
    Панели комикса должны занимать только верхние 80% изображения, нижние 20% должны быть пустыми для размещения подписи.
    Не размещай никаких элементов комикса в нижней части изображения, где будет располагаться подпись.
    """
        
        return prompt
    
    @measure_execution_time
    def publish_comic(self) -> Optional[Dict[str, Any]]:
        """
        Публикация комикса в социальные сети.
        
        Returns:
            Optional[Dict[str, Any]]: Результаты публикации или None в случае ошибки.
        """
        logger.info("Начало публикации комикса")
        
        # Проверка наличия изображения и сценария-победителя
        if not self.image_path or not self.winner_script:
            logger.error("Невозможно опубликовать комикс: нет изображения или сценария-победителя")
            return None
        
        try:
            # Формирование подписи для публикации
            caption = format_caption(
                title=self.news["title"],
                content=self.winner_script["caption"],
                average_score=self.winner_score
            )
            
            # Публикация на всех платформах
            self.publication_results = publish_to_all_platforms(
                image_path=self.image_path,
                caption=caption
            )
            
            # Логирование публикации
            platforms = []
            if self.publication_results.get("platforms", {}).get("telegram", {}).get("success", False):
                platforms.append("Telegram")
            if self.publication_results.get("platforms", {}).get("instagram", {}).get("success", False):
                platforms.append("Instagram")
            
            logger.log_publication(platforms, self.image_path)
            
            # Логирование публикации в важных событиях
            important_logger.log_publication(platforms, self.image_path)
            return self.publication_results
        
        except Exception as e:
            logger.error(f"Ошибка при публикации комикса: {str(e)}")
            return None
    
    @measure_execution_time
    def save_history(self) -> bool:
        """
        Сохранение истории публикации.
        
        Returns:
            bool: True, если история успешно сохранена, иначе False.
        """
        logger.info("Начало сохранения истории")
        
        # Проверка наличия необходимых данных
        if not self.news or not self.scripts or not self.evaluations or not self.winner_script:
            logger.error("Невозможно сохранить историю: недостаточно данных")
            return False
        
        try:
            # Формирование данных для сохранения
            history_data = {
                "date": datetime.now().isoformat(),
                "news": self.news,
                "scripts": self.scripts,
                "evaluations": {k: {
                    "average_score": v["average_score"],
                    "scores_std_dev": v["scores_std_dev"],
                    "evaluations": v["evaluations"]
                } for k, v in self.evaluations.items()},
                "winner": {
                    "script_id": self.winner_script["script_id"],
                    "title": self.winner_script["title"],
                    "average_score": self.winner_score
                },
                "image_path": self.image_path,
                "publication_results": self.publication_results
            }
            
            # Сохранение данных
            success = store_daily_data(history_data)
            
            if success:
                logger.info("История успешно сохранена")
            else:
                logger.error("Не удалось сохранить историю")
            
            return success
        
        except Exception as e:
            logger.error(f"Ошибка при сохранении истории: {str(e)}")
            return False
    
    @measure_execution_time
    def run_full_process(self, force_new_news=False) -> Dict[str, Any]:
        """
        Запуск полного процесса создания и публикации комикса.
        
        Args:
            force_new_news (bool): Принудительно получить новую новость.
        
        Returns:
            Dict[str, Any]: Результаты выполнения процесса.
        """
        logger.info("Запуск полного процесса создания и публикации комикса")
        
        results = {
            "success": False,
            "steps": {}
        }
        
        # Шаг 1: Сбор новостей
        try:
            news = self.collect_news(force_new_news=force_new_news)
            results["steps"]["collect_news"] = {"success": bool(news), "data": news}
            
            if not news:
                logger.error("Процесс остановлен: не удалось получить новость дня")
                return results
        except Exception as e:
            logger.error(f"Ошибка при сборе новостей: {str(e)}")
            results["steps"]["collect_news"] = {"success": False, "error": str(e)}
            return results
        
        # Шаг 2: Генерация сценариев
        try:
            scripts = self.generate_scripts()
            results["steps"]["generate_scripts"] = {"success": bool(scripts), "count": len(scripts)}
            
            if not scripts:
                logger.error("Процесс остановлен: не удалось сгенерировать сценарии")
                return results
        except Exception as e:
            logger.error(f"Ошибка при генерации сценариев: {str(e)}")
            results["steps"]["generate_scripts"] = {"success": False, "error": str(e)}
            return results
        
        # Шаг 3: Оценка сценариев
        try:
            evaluations = self.evaluate_scripts()
            results["steps"]["evaluate_scripts"] = {"success": bool(evaluations), "count": len(evaluations)}
            
            if not evaluations:
                logger.error("Процесс остановлен: не удалось оценить сценарии")
                return results
        except Exception as e:
            logger.error(f"Ошибка при оценке сценариев: {str(e)}")
            results["steps"]["evaluate_scripts"] = {"success": False, "error": str(e)}
            return results
        
        # Шаг 4: Выбор победителя
        try:
            winner = self.select_winner()
            results["steps"]["select_winner"] = {"success": bool(winner), "data": winner}
            
            if not winner:
                logger.error("Процесс остановлен: не удалось выбрать победителя")
                return results
        except Exception as e:
            logger.error(f"Ошибка при выборе победителя: {str(e)}")
            results["steps"]["select_winner"] = {"success": False, "error": str(e)}
            return results
        
        # Шаг 5: Создание изображения
        try:
            image_path = self.create_image()
            results["steps"]["create_image"] = {"success": bool(image_path), "path": image_path}
            
            if not image_path:
                logger.error("Процесс остановлен: не удалось создать изображение")
                return results
        except Exception as e:
            logger.error(f"Ошибка при создании изображения: {str(e)}")
            results["steps"]["create_image"] = {"success": False, "error": str(e)}
            return results
        
        # Шаг 6: Публикация комикса
        try:
            publication = self.publish_comic()
            results["steps"]["publish_comic"] = {"success": bool(publication), "data": publication}
            
            if not publication:
                logger.warning("Не удалось опубликовать комикс, но процесс продолжается")
        except Exception as e:
            logger.error(f"Ошибка при публикации комикса: {str(e)}")
            results["steps"]["publish_comic"] = {"success": False, "error": str(e)}
        
        # Шаг 7: Сохранение истории
        try:
            history_saved = self.save_history()
            results["steps"]["save_history"] = {"success": history_saved}
        except Exception as e:
            logger.error(f"Ошибка при сохранении истории: {str(e)}")
            results["steps"]["save_history"] = {"success": False, "error": str(e)}
        
        # Определение общего результата
        results["success"] = all(
            step.get("success", False) 
            for step_name, step in results["steps"].items() 
            if step_name != "publish_comic"  # Публикация не критична для успеха
        )
        
        if results["success"]:
            logger.info("Полный процесс успешно завершен")
        else:
            logger.error("Полный процесс завершен с ошибками")
        
        return results


# Создание экземпляра агента-менеджера
# Используем синглтон-паттерн, чтобы избежать создания нового экземпляра при каждом импорте
_manager_instance = None

def get_manager():
    """
    Получение экземпляра агента-менеджера.
    Используется синглтон-паттерн, чтобы избежать создания нового экземпляра при каждом импорте.
    
    Returns:
        ManagerAgent: Экземпляр агента-менеджера.
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ManagerAgent()
    return _manager_instance

manager = get_manager()
