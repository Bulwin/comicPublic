"""
Полноценный сервер DailyComicBot с планировщиком и Telegram ботом.
Использует время из переменных окружения.
"""

import os
import sys
import asyncio
import signal
import threading
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Импорт модулей проекта
sys.path.append(str(Path(__file__).resolve().parent))
from agents.manager import get_manager
from utils import logger, important_logger
from utils.scheduler import scheduler, start_scheduler, shutdown_scheduler
from telegram_bot import ComicBotTelegram
from tools.publishing_tools import publish_comic_to_channel

# Получаем настройки времени из переменных окружения или используем значения по умолчанию
TIMEZONE = os.getenv("TIMEZONE", "Europe/Nicosia")
NEWS_COLLECTION_HOUR = int(os.getenv("NEWS_COLLECTION_HOUR", "13"))
NEWS_COLLECTION_MINUTE = int(os.getenv("NEWS_COLLECTION_MINUTE", "0"))
PUBLICATION_TIME_HOUR = int(os.getenv("PUBLICATION_TIME_HOUR", "13"))
PUBLICATION_TIME_MINUTE = int(os.getenv("PUBLICATION_TIME_MINUTE", "15"))

class DailyComicBotServer:
    """Полноценный сервер DailyComicBot с планировщиком и Telegram ботом."""
    
    def __init__(self):
        """Инициализация сервера."""
        self.manager = get_manager()
        self.telegram_bot = None
        self.running = False
        self.bot_event_loop = None
        
    def scheduled_news_collection(self):
        """Запланированный сбор новостей - запускает тот же процесс, что и ручной запуск в боте."""
        try:
            logger.info("🕐 Запланированный сбор новостей начат")
            important_logger.log_scheduled_task_start("news_collection")
            
            # Отправляем уведомление в Telegram бот для запуска автоматического процесса
            if self.telegram_bot and self.telegram_bot.app:
                try:
                    # Используем сохраненный event loop
                    if hasattr(self, 'bot_event_loop') and self.bot_event_loop:
                        loop = self.bot_event_loop
                        logger.info("📍 Используем сохраненный event loop бота")
                    else:
                        logger.error("❌ Event loop бота не найден")
                        self._run_direct_process()
                        return
                    
                    # Запускаем корутину в event loop бота
                    future = asyncio.run_coroutine_threadsafe(
                        self.telegram_bot._run_full_automatic_process(),
                        loop
                    )
                    
                    logger.info("✅ Автоматический процесс запущен через Telegram бот")
                    
                    # Ждем немного, чтобы убедиться, что задача начала выполняться
                    try:
                        future.result(timeout=1.0)
                    except asyncio.TimeoutError:
                        # Это нормально - задача еще выполняется
                        logger.info("📍 Задача запущена и выполняется")
                    except Exception as e:
                        logger.error(f"❌ Ошибка в автоматическом процессе: {e}")
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка запуска через Telegram бот: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    # Fallback - запускаем напрямую через manager
                    self._run_direct_process()
            else:
                logger.error("❌ Telegram бот не инициализирован, запускаю напрямую")
                self._run_direct_process()
            
            important_logger.log_scheduled_task_complete("news_collection")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в запланированном сборе новостей: {str(e)}")
            important_logger.log_error("scheduled_news_collection", str(e))
    
    def _run_direct_process(self):
        """Fallback - запуск процесса напрямую через manager без Telegram бота."""
        try:
            logger.info("🔄 Запуск процесса напрямую через manager...")
            
            # Сбор новостей
            news = self.manager.collect_news()
            if not news:
                logger.error("❌ Не удалось собрать новости")
                return
            
            # Генерация сценариев
            scripts = self.manager.generate_scripts()
            if not scripts:
                logger.error("❌ Не удалось создать сценарии")
                return
            
            # Оценка сценариев
            evaluations = self.manager.evaluate_scripts()
            if not evaluations:
                logger.error("❌ Не удалось оценить сценарии")
                return
            
            # Выбор победителя
            winner = self.manager.select_winner()
            if not winner:
                logger.error("❌ Не удалось выбрать лучший сценарий")
                return
            
            # Создание изображения для лучшего сценария
            image_path = self.manager.create_image()
            if not image_path:
                logger.error("❌ Не удалось создать изображение")
                return
            
            # НЕ автоматически одобряем - ждем решения пользователя
            logger.info("✅ Процесс завершен, изображение готово к одобрению пользователя")
            logger.info("⏳ Ожидается одобрение пользователя через Telegram бот")
            logger.info(f"🏆 Лучший сценарий: {self.manager.winner_script.get('title', 'Без заголовка')}")
            logger.info(f"📊 Оценка: {self.manager.winner_score:.1f}/100")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в прямом процессе: {str(e)}")
    
    def scheduled_publication(self):
        """Запланированная проверка готовности к публикации (БЕЗ автоматической публикации)."""
        try:
            logger.info("🕐 Запланированная проверка готовности к публикации")
            important_logger.log_scheduled_task_start("publication_check")
            
            # Проверяем, выбрал ли пользователь изображение для публикации
            if not hasattr(self.manager, 'approved_image') or not self.manager.approved_image:
                logger.info("⏳ Пользователь еще не одобрил изображение для публикации")
                logger.info("📅 Автоматическая публикация НЕ выполняется - ждем одобрения пользователя")
                
                # Отправляем напоминание в Telegram бот (если есть готовый контент)
                if hasattr(self.manager, 'generated_image') and self.manager.generated_image:
                    self._send_publication_reminder()
                else:
                    logger.info("📝 Контент еще не готов для публикации")
                
                important_logger.log_scheduled_task_complete("publication_check")
                return
            
            # Если пользователь одобрил - выполняем публикацию
            logger.info("✅ Пользователь одобрил изображение - выполняем публикацию")
            
            # Получаем данные выбранного изображения
            approved_image = self.manager.approved_image
            
            # Проверяем наличие готового контента
            if not approved_image.get('image_path'):
                logger.error("❌ Путь к изображению не найден")
                return
                
            if not approved_image.get('script'):
                logger.error("❌ Сценарий не найден")
                return
                
            if not hasattr(self.manager, 'news') or not self.manager.news:
                logger.error("❌ Новость не готова для публикации")
                return
            
            # Публикация в канал
            publication_result = publish_comic_to_channel(
                image_path=approved_image['image_path'],
                script=approved_image['script'],
                news_title=self.manager.news.get('title', 'Новость дня'),
                average_score=approved_image.get('average_score', 0)
            )
            
            if publication_result.get('success'):
                # Сохранение результатов
                self.manager.publication_results = publication_result
                self.manager.save_history()
                
                logger.info("✅ Публикация одобренного изображения завершена успешно")
                logger.info(f"📺 Канал: {publication_result.get('channel_id')}")
                logger.info(f"📝 Пост ID: {publication_result.get('post_message_id')}")
                logger.info(f"🏆 Опубликован сценарий: {approved_image['script'].get('title', 'Без заголовка')}")
                
                important_logger.log_publication_success(
                    channel_id=publication_result.get('channel_id'),
                    post_id=publication_result.get('post_message_id'),
                    script_title=approved_image['script'].get('title', 'Без заголовка'),
                    average_score=approved_image.get('average_score', 0)
                )
                
                # Очищаем выбор после успешной публикации
                self.manager.approved_image = None
                
                important_logger.log_scheduled_task_complete("publication_check")
                
            else:
                error_msg = publication_result.get('error', 'Неизвестная ошибка')
                logger.error(f"❌ Ошибка при публикации: {error_msg}")
                important_logger.log_error("scheduled_publication", error_msg)
            
        except Exception as e:
            logger.error(f"❌ Ошибка в запланированной проверке публикации: {str(e)}")
            important_logger.log_error("scheduled_publication_check", str(e))
    
    def _send_publication_reminder(self):
        """Отправка напоминания о необходимости одобрить публикацию."""
        try:
            if self.telegram_bot and hasattr(self.telegram_bot, 'send_publication_reminder'):
                logger.info("📢 Отправка напоминания о публикации в Telegram")
                # Запускаем в event loop бота
                if hasattr(self, 'bot_event_loop') and self.bot_event_loop:
                    future = asyncio.run_coroutine_threadsafe(
                        self.telegram_bot.send_publication_reminder(),
                        self.bot_event_loop
                    )
                    try:
                        future.result(timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning("⏰ Таймаут при отправке напоминания")
                    except Exception as e:
                        logger.error(f"❌ Ошибка при отправке напоминания: {e}")
            else:
                logger.info("📝 Telegram бот недоступен для отправки напоминания")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке напоминания: {str(e)}")
    
    def publish_immediately(self, approved_image):
        """Немедленная публикация выбранного изображения."""
        try:
            logger.info("🚀 Немедленная публикация начата")
            
            # Проверяем наличие готового контента
            if not approved_image.get('image_path'):
                logger.error("❌ Путь к изображению не найден")
                return False
                
            if not approved_image.get('script'):
                logger.error("❌ Сценарий не найден")
                return False
                
            if not hasattr(self.manager, 'news') or not self.manager.news:
                logger.error("❌ Новость не готова для публикации")
                return False
            
            # Публикация в канал
            publication_result = publish_comic_to_channel(
                image_path=approved_image['image_path'],
                script=approved_image['script'],
                news_title=self.manager.news.get('title', 'Новость дня'),
                average_score=approved_image.get('average_score', 0)
            )
            
            if publication_result.get('success'):
                # Сохранение результатов
                self.manager.publication_results = publication_result
                self.manager.save_history()
                
                logger.info("✅ Немедленная публикация завершена успешно")
                logger.info(f"📺 Канал: {publication_result.get('channel_id')}")
                logger.info(f"📝 Пост ID: {publication_result.get('post_message_id')}")
                logger.info(f"🏆 Опубликован сценарий: {approved_image['script'].get('title', 'Без заголовка')}")
                
                important_logger.log_publication_success(
                    channel_id=publication_result.get('channel_id'),
                    post_id=publication_result.get('post_message_id'),
                    script_title=approved_image['script'].get('title', 'Без заголовка'),
                    average_score=approved_image.get('average_score', 0)
                )
                
                # Очищаем выбор после успешной публикации
                self.manager.approved_image = None
                
                return True
                
            else:
                error_msg = publication_result.get('error', 'Неизвестная ошибка')
                logger.error(f"❌ Ошибка при немедленной публикации: {error_msg}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка в немедленной публикации: {str(e)}")
            return False
    
    def setup_scheduler(self):
        """Настройка планировщика задач."""
        logger.info("⚙️ Настройка планировщика задач...")
        
        # Добавляем задачу сбора новостей
        scheduler.add_daily_task(
            self.scheduled_news_collection,
            NEWS_COLLECTION_HOUR,
            NEWS_COLLECTION_MINUTE,
            job_id="news_collection"
        )
        
        # Добавляем задачу публикации
        scheduler.add_daily_task(
            self.scheduled_publication,
            PUBLICATION_TIME_HOUR,
            PUBLICATION_TIME_MINUTE,
            job_id="publication"
        )
        
        # Показываем запланированные задачи
        jobs = scheduler.get_jobs()
        logger.info(f"📅 Запланировано задач: {len(jobs)}")
        for job in jobs:
            logger.info(f"  - {job.id}: запланировано")
    
    async def run_telegram_bot(self):
        """Запуск Telegram бота."""
        try:
            logger.info("🤖 Инициализация Telegram бота...")
            self.telegram_bot = ComicBotTelegram()
            # Связываем бота с сервером для доступа к manager
            self.telegram_bot.server = self
            self.telegram_bot.manager = self.manager
            
            # Сохраняем текущий event loop для использования в планировщике
            self.bot_event_loop = asyncio.get_running_loop()
            
            logger.info("🤖 Запуск Telegram бота...")
            await self.telegram_bot.run()
        except Exception as e:
            logger.error(f"❌ Ошибка Telegram бота: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения."""
        logger.info(f"📡 Получен сигнал {signum}, завершение работы...")
        self.shutdown()
    
    def shutdown(self):
        """Корректное завершение работы сервера."""
        if self.running:
            logger.info("🛑 Завершение работы сервера...")
            self.running = False
            shutdown_scheduler()
            logger.info("✅ Сервер остановлен")
    
    def run(self):
        """Запуск сервера."""
        try:
            logger.info("🚀 Запуск DailyComicBot Server (ПОЛНАЯ ВЕРСИЯ)")
            logger.info(f"⏰ Часовой пояс: {TIMEZONE}")
            logger.info(f"📰 Сбор новостей: {NEWS_COLLECTION_HOUR:02d}:{NEWS_COLLECTION_MINUTE:02d}")
            logger.info(f"📤 Публикация: {PUBLICATION_TIME_HOUR:02d}:{PUBLICATION_TIME_MINUTE:02d}")
            
            # Настройка обработчиков сигналов
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            # Настройка планировщика
            logger.info("⚙️ Настройка планировщика...")
            self.setup_scheduler()
            
            # Запуск планировщика
            logger.info("📅 Запуск планировщика...")
            start_scheduler()
            
            self.running = True
            logger.info("✅ Планировщик инициализирован успешно")
            
            # Запуск Telegram бота
            try:
                asyncio.run(self.run_telegram_bot())
            except Exception as e:
                logger.error(f"❌ Ошибка Telegram бота: {str(e)}")
                logger.info("🔄 Сервер продолжает работу без Telegram бота...")
                logger.info("⏰ Планировщик остается активным")
                logger.info("🛑 Нажмите Ctrl+C для остановки")
                
                # Если Telegram бот не запустился, продолжаем работу только с планировщиком
                try:
                    while self.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("⌨️ Получен сигнал прерывания от клавиатуры")
            
        except KeyboardInterrupt:
            logger.info("⌨️ Получен сигнал прерывания от клавиатуры")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка сервера: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            self.shutdown()

def main():
    """Основная функция."""
    # Показываем текущее время
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"� Текущее время: {current_time}")
    
    # Проверяем обязательные переменные окружения
    required_vars = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_ADMIN_CHAT_ID", "OPENAI_API_KEY", "PERPLEXITY_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
        return
    
    # Запуск сервера
    server = DailyComicBotServer()
    server.run()

if __name__ == "__main__":
    main()
