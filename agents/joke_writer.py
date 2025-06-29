"""
Модуль агента для генерации анекдотов DailyComicBot.
Отвечает за создание анекдотов на основе новости дня.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import concurrent.futures

# Импорт модулей проекта
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import logger, handle_exceptions, measure_execution_time, important_logger
from tools.storage_tools import store_jokes
import config
from config import SCRIPTWRITERS


class JokeWriterAgent:
    """
    Агент для генерации анекдотов на основе новости дня.
    """
    
    def __init__(self):
        """Инициализация агента для анекдотов."""
        self.news = None
        self.jokes = []
        self.selected_joke = None
        
        logger.info("Агент для генерации анекдотов инициализирован")
    
    @measure_execution_time
    def generate_jokes(self, news: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Генерация анекдотов всеми авторами.
        
        Args:
            news (Dict[str, Any]): Информация о новости дня.
        
        Returns:
            List[Dict[str, Any]]: Список сгенерированных анекдотов.
        """
        logger.info("Начало генерации анекдотов")
        
        # Проверка наличия новости
        if not news:
            logger.error("Невозможно сгенерировать анекдоты: новость не получена")
            return []
        
        self.news = news
        self.jokes = []
        
        # Параллельная генерация анекдотов
        joke_tasks = []
        for writer_type, writer_info in SCRIPTWRITERS.items():
            logger.info(f"Подготовка генерации анекдота для автора {writer_type}: {writer_info['name']}")
            
            # Создаем задачу для каждого автора
            joke_id = f"{writer_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            joke_tasks.append((writer_type, writer_info, joke_id))
            
            # Логирование запроса к автору
            important_logger.log_scriptwriter_request(writer_type, writer_info["name"])
        
        # Выполняем задачи параллельно
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(SCRIPTWRITERS)) as executor:
            # Запускаем задачи на выполнение
            future_to_task = {
                executor.submit(self.invoke_joke_writer, self.news, task[0]): task
                for task in joke_tasks
            }
            
            # Получаем результаты по мере их готовности
            for future in concurrent.futures.as_completed(future_to_task):
                writer_type, writer_info, joke_id = future_to_task[future]
                try:
                    joke = future.result()
                    if joke:
                        # Добавление метаданных к анекдоту
                        joke["writer_type"] = writer_type
                        joke["writer_name"] = writer_info["name"]
                        joke["joke_id"] = joke_id
                        joke["news"] = {
                            "title": news.get("title", ""),
                            "content": news.get("content", "")
                        }
                        joke["created_at"] = datetime.now().isoformat()
                        
                        # Добавление анекдота в список
                        self.jokes.append(joke)
                        
                        # Логирование создания анекдота
                        logger.info(f"Анекдот создан: {joke_id} от {writer_info['name']}")
                        
                        # Логирование получения ответа от автора
                        important_logger.log_scriptwriter_response(writer_type, writer_info["name"], joke)
                    else:
                        logger.warning(f"Не удалось создать анекдот для автора {writer_type}")
                except Exception as e:
                    logger.error(f"Ошибка при генерации анекдота для автора {writer_type}: {str(e)}")
        
        logger.info(f"Сгенерировано {len(self.jokes)} анекдотов")
        
        # Сохранение анекдотов в файл
        if self.jokes:
            try:
                store_jokes(self.jokes)
                logger.info("Анекдоты успешно сохранены в файл")
            except Exception as e:
                logger.error(f"Ошибка при сохранении анекдотов: {str(e)}")
        
        return self.jokes
    
    def invoke_joke_writer(self, news: Dict[str, Any], writer_type: str) -> Optional[Dict[str, Any]]:
        """
        Вызов автора для создания анекдота.
        
        Args:
            news (Dict[str, Any]): Информация о новости дня.
            writer_type (str): Тип автора (A, B, C, D, E).
            
        Returns:
            Optional[Dict[str, Any]]: Сгенерированный анекдот или None в случае ошибки.
        """
        try:
            # Проверка, использовать ли Assistants API
            if hasattr(config, 'USE_ASSISTANTS_API') and config.USE_ASSISTANTS_API:
                # Импорт функции для работы с Assistants API
                from utils.assistants_api import invoke_joke_writer as assistants_invoke_joke_writer
                
                # Вызов автора через Assistants API
                logger.info(f"Вызов автора анекдотов типа {writer_type} через Assistants API")
                return assistants_invoke_joke_writer(news, writer_type)
            
            # Если Assistants API не используется, используем заглушку
            logger.warning(f"Assistants API не настроен, используется заглушка для автора {writer_type}")
            
            # Заглушка для тестирования
            joke = {
                "title": f"Анекдот от {SCRIPTWRITERS[writer_type]['name']}",
                "content": f"Это тестовый анекдот от {SCRIPTWRITERS[writer_type]['name']} на тему: {news.get('title', 'новость дня')}. "
                          f"В стиле {SCRIPTWRITERS[writer_type]['description']}."
            }
            
            return joke
        
        except Exception as e:
            error_msg = f"Ошибка при вызове автора анекдотов {writer_type}: {str(e)}"
            logger.error(error_msg)
            return None
    
    def select_best_joke(self, jokes: List[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Выбор лучшего анекдота (по умолчанию первый).
        
        Args:
            jokes (List[Dict[str, Any]], optional): Список анекдотов. 
                Если None, используется self.jokes.
        
        Returns:
            Optional[Dict[str, Any]]: Лучший анекдот или None.
        """
        if jokes is None:
            jokes = self.jokes
        
        if not jokes:
            logger.warning("Нет анекдотов для выбора")
            return None
        
        # Пока просто берем первый анекдот
        # В будущем можно добавить логику оценки
        best_joke = jokes[0]
        self.selected_joke = best_joke
        
        logger.info(f"Выбран лучший анекдот: {best_joke.get('joke_id', 'unknown')} от {best_joke.get('writer_name', 'unknown')}")
        
        return best_joke
    
    def get_joke_by_author(self, author_type: str) -> Optional[Dict[str, Any]]:
        """
        Получение анекдота конкретного автора.
        
        Args:
            author_type (str): Тип автора (A, B, C, D, E).
        
        Returns:
            Optional[Dict[str, Any]]: Анекдот автора или None.
        """
        for joke in self.jokes:
            if joke.get("writer_type") == author_type:
                return joke
        
        logger.warning(f"Анекдот от автора {author_type} не найден")
        return None
    
    @measure_execution_time
    def run_joke_generation_process(self, news: Dict[str, Any] = None, force_new_news: bool = False) -> Dict[str, Any]:
        """
        Запуск полного процесса генерации анекдотов.
        
        Args:
            news (Dict[str, Any], optional): Новость для анекдотов. Если None, получается автоматически.
            force_new_news (bool): Принудительно получить новую новость.
        
        Returns:
            Dict[str, Any]: Результаты выполнения процесса.
        """
        logger.info("Запуск полного процесса генерации анекдотов")
        
        results = {
            "success": False,
            "steps": {}
        }
        
        # Шаг 1: Получение новости (если не передана)
        if news is None:
            try:
                from tools.news_tools import get_top_news
                news = get_top_news(force_new=force_new_news)
                results["steps"]["get_news"] = {"success": bool(news), "data": news}
                
                if not news:
                    logger.error("Процесс остановлен: не удалось получить новость дня")
                    return results
            except Exception as e:
                logger.error(f"Ошибка при получении новости: {str(e)}")
                results["steps"]["get_news"] = {"success": False, "error": str(e)}
                return results
        else:
            results["steps"]["get_news"] = {"success": True, "data": news}
        
        # Шаг 2: Генерация анекдотов
        try:
            jokes = self.generate_jokes(news)
            results["steps"]["generate_jokes"] = {"success": bool(jokes), "count": len(jokes)}
            
            if not jokes:
                logger.error("Процесс остановлен: не удалось сгенерировать анекдоты")
                return results
        except Exception as e:
            logger.error(f"Ошибка при генерации анекдотов: {str(e)}")
            results["steps"]["generate_jokes"] = {"success": False, "error": str(e)}
            return results
        
        # Шаг 3: Выбор лучшего анекдота
        try:
            best_joke = self.select_best_joke(jokes)
            results["steps"]["select_best"] = {"success": bool(best_joke), "data": best_joke}
            
            if not best_joke:
                logger.warning("Не удалось выбрать лучший анекдот")
        except Exception as e:
            logger.error(f"Ошибка при выборе лучшего анекдота: {str(e)}")
            results["steps"]["select_best"] = {"success": False, "error": str(e)}
        
        # Определение общего результата
        results["success"] = all(
            step.get("success", False) 
            for step_name, step in results["steps"].items()
            if step_name != "select_best"  # Выбор лучшего не критичен
        )
        
        if results["success"]:
            logger.info("Процесс генерации анекдотов успешно завершен")
        else:
            logger.error("Процесс генерации анекдотов завершен с ошибками")
        
        return results


# Создание экземпляра агента для анекдотов
# Используем синглтон-паттерн, чтобы избежать создания нового экземпляра при каждом импорте
_joke_writer_instance = None

def get_joke_writer():
    """
    Получение экземпляра агента для анекдотов.
    Используется синглтон-паттерн.
    
    Returns:
        JokeWriterAgent: Экземпляр агента для анекдотов.
    """
    global _joke_writer_instance
    if _joke_writer_instance is None:
        _joke_writer_instance = JokeWriterAgent()
    return _joke_writer_instance

joke_writer = get_joke_writer()
