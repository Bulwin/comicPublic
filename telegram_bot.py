"""
Telegram бот для управления процессом создания комиксов DailyComicBot.
Автоматический workflow с возможностью перегенерации на каждом этапе.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Применяем nest_asyncio для решения проблемы с event loop (если доступен)
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass  # nest_asyncio не установлен, продолжаем без него

# Telegram Bot API
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Импорт модулей проекта
sys.path.append(str(Path(__file__).resolve().parent))
from agents.manager import get_manager
from utils import logger, important_logger
from tools.publishing_tools import publish_comic_to_channel
import config
from config import USE_JURY_EVALUATION
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Получение переменных из окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
SCRIPTWRITERS = config.SCRIPTWRITERS

# Получаем настройки времени из переменных окружения или используем значения по умолчанию
NEWS_COLLECTION_HOUR = int(os.getenv("NEWS_COLLECTION_HOUR", "13"))
NEWS_COLLECTION_MINUTE = int(os.getenv("NEWS_COLLECTION_MINUTE", "0"))
PUBLICATION_TIME_HOUR = int(os.getenv("PUBLICATION_TIME_HOUR", "13"))
PUBLICATION_TIME_MINUTE = int(os.getenv("PUBLICATION_TIME_MINUTE", "15"))

# Настройка логирования для Telegram бота
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
telegram_logger = logging.getLogger(__name__)

# Отключение подробного логирования HTTP-запросов
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)


class ComicBotTelegram:
    """Telegram бот для управления процессом создания комиксов."""
    
    def __init__(self):
        """Инициализация бота."""
        self.app = None
        self.manager = get_manager()
        self.admin_chat_id = TELEGRAM_ADMIN_CHAT_ID
        self.rejected_news_list = []  # Список отклоненных новостей в текущей сессии
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start - показать главное меню."""
        if not self._is_admin(update):
            await update.message.reply_text("❌ У вас нет прав для использования этого бота.")
            return
            
        keyboard = [
            [InlineKeyboardButton("🚀 Запустить процесс вручную", callback_data="manual_start")],
            [InlineKeyboardButton("🎭 Создать анекдот", callback_data="create_joke")],
            [InlineKeyboardButton("📊 Статус", callback_data="show_status")],
            [InlineKeyboardButton("🧪 Тест публикации", callback_data="test_publish")],
            [InlineKeyboardButton("⏰ Настройки расписания", callback_data="schedule_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎭 *DailyComicBot Control Panel*\n\n"
            f"🤖 Автоматический режим: Каждый день в {NEWS_COLLECTION_HOUR:02d}:{NEWS_COLLECTION_MINUTE:02d} создается пост, в {PUBLICATION_TIME_HOUR:02d}:{PUBLICATION_TIME_MINUTE:02d} публикуется\n"
            "🔧 Ручной режим: Для тестирования и отладки\n"
            "🎭 Анекдоты: Создание и публикация анекдотов на основе новости дня\n\n"
            "Выберите действие:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status - показать текущий статус."""
        if not self._is_admin(update):
            await update.message.reply_text("❌ У вас нет прав для использования этого бота.")
            return
            
        status_text = "📊 *Текущий статус:*\n\n"
        
        if hasattr(self.manager, 'news') and self.manager.news:
            status_text += "✅ Новость получена\n"
        else:
            status_text += "⭕ Новость не получена\n"
            
        if hasattr(self.manager, 'scripts') and self.manager.scripts:
            status_text += f"✅ Сценарии созданы ({len(self.manager.scripts)} шт.)\n"
        else:
            status_text += "⭕ Сценарии не созданы\n"
            
        if hasattr(self.manager, 'winner_script') and self.manager.winner_script:
            status_text += "✅ Лучший сценарий выбран\n"
        else:
            status_text += "⭕ Лучший сценарий не выбран\n"
            
        if hasattr(self.manager, 'image_path') and self.manager.image_path:
            status_text += "✅ Изображение создано\n"
        else:
            status_text += "⭕ Изображение не создано\n"
            
        if hasattr(self.manager, 'publication_results') and self.manager.publication_results:
            status_text += "✅ Комикс опубликован\n"
        else:
            status_text += "⭕ Комикс не опубликован\n"
            
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки."""
        query = update.callback_query
        await query.answer()
        
        if not self._is_admin_callback(query):
            await query.edit_message_text("❌ У вас нет прав для использования этого бота.")
            return
        
        action = query.data
        
        # Новые действия главного меню
        if action == "manual_start":
            await self._manual_start(query)
        elif action == "show_status":
            await self._show_status(query)
        elif action == "test_publish":
            await self._test_publish(query)
        elif action == "schedule_settings":
            await self._show_schedule_settings(query)
        
        # Существующие действия
        elif action == "regenerate_news":
            await self._regenerate_news(query)
        elif action == "continue_with_news":
            await self._continue_with_scripts(query)
        elif action == "regenerate_scripts":
            await self._regenerate_scripts(query)
        elif action == "continue_with_script":
            await self._continue_with_image(query)
        elif action == "regenerate_image":
            await self._regenerate_image(query)
        elif action == "regenerate_all_images":
            await self._regenerate_all_images(query)
        elif action == "approve_publication":
            await self._approve_publication(query)
        elif action == "restart_full":
            await self._restart_full_process(query)
        elif action == "back_to_menu":
            await self._back_to_menu(query)
        
        # Новые действия для выбора изображений
        elif action.startswith("select_image_"):
            rank = int(action.split("_")[-1])
            await self._select_image_by_rank(query, rank)
        
        # ===== НОВЫЕ ДЕЙСТВИЯ ДЛЯ АНЕКДОТОВ (НЕ ИЗМЕНЯЮТ СУЩЕСТВУЮЩИЙ ФУНКЦИОНАЛ) =====
        elif action == "create_joke":
            await self._create_joke(query)
        elif action == "regenerate_jokes":
            await self._regenerate_jokes(query)
        elif action.startswith("select_joke_"):
            author_type = action.split("_")[-1]
            await self._select_joke(query, author_type)
        elif action == "publish_joke_now":
            await self._publish_joke_now(query)
        elif action == "schedule_joke":
            await self._schedule_joke(query)
        elif action == "approve_joke_publication":
            await self._approve_joke_publication(query)
    
    
    async def _continue_with_scripts(self, query=None):
        """Продолжение с созданием сценариев."""
        try:
            if query:
                await query.edit_message_text("✍️ Создаю сценарии...")
            else:
                await self._send_status_message("✍️ Создаю сценарии...")
            
            # Очищаем список отклоненных новостей при одобрении
            if self.rejected_news_list:
                telegram_logger.info(f"🧹 Очищаю список отклоненных новостей ({len(self.rejected_news_list)} элементов)")
                self.rejected_news_list.clear()
            
            # Генерация сценариев (количество зависит от USE_JURY_EVALUATION)
            scripts = self.manager.generate_scripts()
            if not scripts:
                await self._send_error_message("❌ Не удалось создать сценарии")
                return
            
            # Логика зависит от режима жюри
            if USE_JURY_EVALUATION:
                # С жюри: оценка + выбор лучшего
                evaluations = self.manager.evaluate_scripts()
                if not evaluations:
                    await self._send_error_message("❌ Не удалось оценить сценарии")
                    return
                
                winner = self.manager.select_winner()
                if not winner:
                    await self._send_error_message("❌ Не удалось выбрать лучший сценарий")
                    return
                
                await self._send_status_message("🖼️ Создаю изображения для топ-4 сценариев...")
                top_scripts = self.manager.select_top_scripts(4)
            else:
                # Без жюри: случайный выбор, изображения для всех сценариев
                winner = self.manager.select_random_winner()
                if not winner:
                    await self._send_error_message("❌ Не удалось выбрать сценарий")
                    return
                
                await self._send_status_message(f"🖼️ Создаю изображения для всех {len(scripts)} сценариев...")
                # Формируем список всех сценариев как "топ" для создания изображений
                top_scripts = []
                for i, script in enumerate(scripts):
                    top_scripts.append({
                        "script_id": script.get("script_id", f"script_{i+1}"),
                        "script": script,
                        "average_score": 0,  # Без оценки
                        "std_dev": 0,
                        "rank": i + 1
                    })
            
            if not top_scripts:
                await self._send_error_message("❌ Не удалось выбрать сценарии для изображений")
                return
            
            # Создаем изображения для всех сценариев
            image_results = self.manager.create_images_for_top_scripts(top_scripts)
            if image_results and any(r["success"] for r in image_results):
                await self._send_multiple_images_result(image_results)
            else:
                await self._send_error_message("❌ Не удалось создать изображения")
                
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при создании сценариев: {str(e)}")
    
    async def _continue_with_image(self, query=None):
        """Продолжение с созданием изображений для топ-4 сценариев."""
        try:
            if query:
                await query.edit_message_text("🖼️ Создаю изображения для топ-4 сценариев...")
            else:
                await self._send_status_message("🖼️ Создаю изображения для топ-4 сценариев...")
            
            # Получаем топ-4 сценария
            top_scripts = self.manager.select_top_scripts(4)
            if not top_scripts:
                await self._send_error_message("❌ Не удалось выбрать топ сценарии")
                return
            
            # Создаем изображения для всех топ сценариев
            image_results = self.manager.create_images_for_top_scripts(top_scripts)
            if image_results:
                await self._send_multiple_images_result(image_results)
            else:
                await self._send_error_message("❌ Не удалось создать изображения")
                
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при создании изображений: {str(e)}")
    
    async def _send_news_result(self, news: Dict[str, Any]):
        """Отправка результата получения новости."""
        text = f"📰 *Новость дня получена:*\n\n"
        text += f"*{news.get('title', 'Без заголовка')}*\n\n"
        
        content = news.get('content', 'Нет содержания')
        if len(content) > 800:
            text += f"{content[:800]}...\n\n"
        else:
            text += f"{content}\n\n"
        
        text += "Что делать дальше?"
        
        keyboard = [
            [InlineKeyboardButton("✅ Продолжить с этой новостью", callback_data="continue_with_news")],
            [InlineKeyboardButton("🔄 Получить другую новость", callback_data="regenerate_news")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.app.bot.send_message(
            chat_id=self.admin_chat_id,
            text=text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _send_news_for_approval(self, news: Dict[str, Any]):
        """НОВАЯ ФИЧА: Отправка новости для одобрения перед созданием сценариев."""
        # Экранируем специальные символы для Markdown
        def escape_markdown(text):
            """Экранирование специальных символов для Telegram Markdown."""
            if not text:
                return ""
            # Заменяем проблемные символы
            text = str(text)
            # Убираем HTML теги
            import re
            text = re.sub(r'<[^>]+>', '', text)
            # Экранируем специальные символы Markdown
            special_chars = ['*', '_', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')
            return text
        
        title = escape_markdown(news.get('title', 'Без заголовка'))
        content = escape_markdown(news.get('content', 'Нет содержания'))
        
        text = f"📰 *Получена новость:*\n\n"
        text += f"*{title}*\n\n"
        
        if len(content) > 800:
            text += f"{content[:800]}\\.\\.\\.\n\n"
        else:
            text += f"{content}\n\n"
        
        text += "Нравится новость? Продолжить создание комикса или получить другую?"
        
        keyboard = [
            [InlineKeyboardButton("✅ Продолжить с этой новостью", callback_data="continue_with_news")],
            [InlineKeyboardButton("🔄 Перегенерировать новость", callback_data="regenerate_news")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.app.bot.send_message(
            chat_id=self.admin_chat_id,
            text=text,
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    
    async def _send_script_result(self, winner: Dict[str, Any]):
        """Отправка результата создания сценария."""
        script = winner['script']
        
        text = f"✍️ *Лучший сценарий выбран:*\n\n"
        text += f"*{script.get('title', 'Без заголовка')}*\n"
        text += f"Автор: {script.get('writer_name', 'Неизвестен')}\n"
        text += f"Оценка жюри: {winner.get('average_score', 0):.1f}/100\n\n"
        
        # Показываем содержание сценария
        if script.get('format') == 'text':
            content = script.get('content', '')
            if len(content) > 600:
                text += f"{content[:600]}...\n\n"
            else:
                text += f"{content}\n\n"
        else:
            description = script.get('description', 'Нет описания')
            if len(description) > 400:
                text += f"{description[:400]}...\n\n"
            else:
                text += f"{description}\n\n"
        
        text += "Что делать дальше?"
        
        keyboard = [
            [InlineKeyboardButton("✅ Создать изображение", callback_data="continue_with_script")],
            [InlineKeyboardButton("🔄 Пересоздать сценарии", callback_data="regenerate_scripts")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.app.bot.send_message(
            chat_id=self.admin_chat_id,
            text=text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _send_image_result(self, image_path: str):
        """Отправка результата создания изображения."""
        try:
            script = self.manager.winner_script
            
            caption = f"🖼️ *Изображение комикса готово!*\n\n"
            caption += f"*{script.get('title', 'Без заголовка')}*\n"
            caption += f"Автор: {script.get('writer_name', 'Неизвестен')}\n"
            caption += f"Оценка: {self.manager.winner_score:.1f}/100\n\n"
            caption += "Одобрить публикацию в запланированное время?"
            
            keyboard = [
                [InlineKeyboardButton("✅ Одобрить публикацию", callback_data="approve_publication")],
                [InlineKeyboardButton("🔄 Пересоздать изображение", callback_data="regenerate_image")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            with open(image_path, 'rb') as photo:
                await self.app.bot.send_photo(
                    chat_id=self.admin_chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при отправке изображения: {str(e)}")
    
    async def _regenerate_news(self, query):
        """Перегенерация новости с накопительным списком исключений."""
        try:
            await query.edit_message_text("🔄 Получаю новую новость...")
        except:
            # Если нет текста, пробуем caption
            try:
                await query.edit_message_caption("🔄 Получаю новую новость...")
            except:
                # Если ничего не получается, отправляем новое сообщение
                await self._send_status_message("🔄 Получаю новую новость...")
        
        try:
            # Добавляем текущую новость в список отклоненных
            current_news = self.manager.news if hasattr(self.manager, 'news') else None
            if current_news and current_news not in self.rejected_news_list:
                self.rejected_news_list.append(current_news)
                telegram_logger.info(f"📝 Добавлена в список отклоненных: {current_news.get('title', 'Без заголовка')}")
                telegram_logger.info(f"📋 Всего отклоненных новостей: {len(self.rejected_news_list)}")
            
            # Принудительно получаем новую новость, исключая ВСЕ отклоненные
            news = self.manager.collect_news(force_new_news=True, exclude_news_list=self.rejected_news_list)
            if not news:
                # Если не удалось получить новую новость, предлагаем использовать существующую
                await self._send_error_message(
                    f"❌ Не удалось получить новую новость (исключено {len(self.rejected_news_list)} тем).\n"
                    "Возможно, проблемы с Perplexity API или исчерпаны варианты новостей дня.\n"
                    "Попробуйте позже или продолжите с существующей новостью."
                )
                return
            
            telegram_logger.info(f"📰 Новая новость получена: {news.get('title', 'Без заголовка')}")
            telegram_logger.info(f"🚫 Исключено тем: {len(self.rejected_news_list)}")
            
            # Отправляем новую новость для одобрения
            await self._send_news_for_approval(news)
            
        except Exception as e:
            error_msg = str(e)
            if "500" in error_msg or "internal_server_error" in error_msg:
                await self._send_error_message(
                    "❌ Perplexity API временно недоступен (ошибка 500).\n"
                    "Попробуйте перегенерировать новость через несколько минут или продолжите с текущей."
                )
            else:
                await self._send_error_message(f"❌ Ошибка при получении новой новости: {error_msg}")
    
    async def _regenerate_scripts(self, query):
        """Перегенерация сценариев."""
        try:
            await query.edit_message_caption("🔄 Создаю новые сценарии и пересоздаю пост...")
        except:
            # Если нет caption, редактируем текст сообщения
            await query.edit_message_text("🔄 Создаю новые сценарии и пересоздаю пост...")
        
        try:
            # Сохраняем текущую новость
            current_news = self.manager.news
            
            # Создание новых сценариев
            scripts = self.manager.generate_scripts()
            if not scripts:
                await self._send_error_message("❌ Не удалось создать новые сценарии")
                return
            
            # Оценка сценариев
            evaluations = self.manager.evaluate_scripts()
            if not evaluations:
                await self._send_error_message("❌ Не удалось оценить новые сценарии")
                return
            
            # Выбор победителя
            winner = self.manager.select_winner()
            if not winner:
                await self._send_error_message("❌ Не удалось выбрать лучший сценарий")
                return
            
            # Создание изображений для топ-4 сценариев
            top_scripts = self.manager.select_top_scripts(4)
            if not top_scripts:
                await self._send_error_message("❌ Не удалось выбрать топ сценарии")
                return
            
            # Создаем изображения для всех топ сценариев
            image_results = self.manager.create_images_for_top_scripts(top_scripts)
            if not image_results or not any(r["success"] for r in image_results):
                await self._send_error_message("❌ Не удалось создать изображения")
                return
            
            # Отправляем все изображения для выбора
            await self._send_multiple_images_result(image_results)
            
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при пересоздании сценариев: {str(e)}")
    
    async def _regenerate_image(self, query):
        """Перегенерация изображения."""
        await query.edit_message_caption("🔄 Создаю новое изображение...")
        
        try:
            # Сохраняем текущие данные
            current_news = self.manager.news
            current_winner = {
                "script": self.manager.winner_script,
                "average_score": self.manager.winner_score
            }
            
            # Создание нового изображения
            image_path = self.manager.create_image()
            if not image_path:
                await self._send_error_message("❌ Не удалось создать новое изображение")
                return
            
            # Отправка обновленного поста
            await self._send_final_post_for_approval(current_news, current_winner, image_path)
            
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при пересоздании изображения: {str(e)}")
    
    async def _approve_publication(self, query):
        """Одобрение публикации."""
        await query.edit_message_caption("📤 Публикуя комикс в канал...")
        
        try:
            # Проверяем наличие необходимых данных
            if not hasattr(self.manager, 'image_path') or not self.manager.image_path:
                await self._send_error_message("❌ Изображение не найдено")
                return
                
            if not hasattr(self.manager, 'winner_script') or not self.manager.winner_script:
                await self._send_error_message("❌ Сценарий не найден")
                return
                
            if not hasattr(self.manager, 'news') or not self.manager.news:
                await self._send_error_message("❌ Новость не найдена")
                return
            
            # Публикация в канал с промптом
            publication_result = publish_comic_to_channel(
                image_path=self.manager.image_path,
                script=self.manager.winner_script,
                news_title=self.manager.news.get('title', 'Новость дня'),
                average_score=self.manager.winner_score
            )
            
            if publication_result.get('success'):
                # Сохранение истории
                self.manager.publication_results = publication_result
                self.manager.save_history()
                
                # Отправка подтверждения с результатами
                success_text = "✅ *Комикс успешно опубликован в канале!*\n\n"
                success_text += f"📺 Канал: {publication_result.get('channel_id', 'Не указан')}\n"
                success_text += f"📝 Пост ID: {publication_result.get('post_message_id', 'Не указан')}\n"
                success_text += f"💬 Комментарий ID: {publication_result.get('comment_message_id', 'Не указан')}\n"
                success_text += f"📅 Время: {publication_result.get('date', 'Не указано')}\n\n"
                success_text += "История сохранена."
                
                await self._send_status_message(success_text)
                
                # Логирование успешной публикации
                important_logger.log_publication_success(
                    channel_id=publication_result.get('channel_id'),
                    post_id=publication_result.get('post_message_id'),
                    script_title=self.manager.winner_script.get('title', 'Без заголовка'),
                    average_score=self.manager.winner_score
                )
                
            else:
                error_msg = publication_result.get('error', 'Неизвестная ошибка')
                await self._send_error_message(f"❌ Ошибка при публикации: {error_msg}")
            
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при одобрении публикации: {str(e)}")
    
    async def _run_full_automatic_process(self):
        """Запуск полного автоматического процесса до готового поста."""
        try:
            telegram_logger.info("🚀 Запуск автоматического процесса через планировщик")
            
            # Этап 1: Получение новости (ВСЕГДА получаем свежую новость для планировщика)
            await self._send_status_message("📰 Получаю свежие новости дня...")
            news = self.manager.collect_news(force_new_news=True)
            
            if not news:
                await self._send_error_message("❌ Не удалось получить новости дня")
                return
            
            telegram_logger.info(f"📰 Свежая новость получена: {news.get('title', 'Без заголовка')}")
            
            # Показываем новость с возможностью перегенерации
            await self._send_news_for_approval(news)
            
        except Exception as e:
            telegram_logger.error(f"❌ Ошибка в автоматическом процессе: {str(e)}")
            import traceback
            telegram_logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_error_message(f"❌ Ошибка в автоматическом процессе: {str(e)}")
    
    async def _send_final_post_for_approval(self, news: Dict[str, Any], winner: Dict[str, Any], image_path: str):
        """Отправка готового поста на одобрение."""
        try:
            script = winner['script']
            
            # Формируем подпись как в финальном посте
            caption = f"*{script.get('title', 'Без заголовка')}*\n\n"
            
            # Добавляем содержание сценария
            if script.get('format') == 'text':
                content = script.get('content', '')
                # Берем только первые 500 символов для подписи
                if len(content) > 500:
                    caption += f"{content[:500]}...\n\n"
                else:
                    caption += f"{content}\n\n"
            else:
                caption += f"{script.get('caption', '')}\n\n"
            
            # Добавляем информацию о процессе
            caption += f"📰 Новость: {news.get('title', '')}\n"
            caption += f"✍️ Автор: {script.get('writer_name', 'Неизвестен')}\n"
            caption += f"🏆 Оценка жюри: {winner.get('average_score', 0):.1f}/100\n\n"
            caption += "Одобрить публикацию?"
            
            keyboard = [
                [InlineKeyboardButton("✅ Одобрить публикацию", callback_data="approve_publication")],
                [InlineKeyboardButton("🔄 Пересоздать новость", callback_data="regenerate_news")],
                [InlineKeyboardButton("🔄 Пересоздать сценарии", callback_data="regenerate_scripts")],
                [InlineKeyboardButton("🔄 Пересоздать изображение", callback_data="regenerate_image")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            with open(image_path, 'rb') as photo:
                await self.app.bot.send_photo(
                    chat_id=self.admin_chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при отправке финального поста: {str(e)}")
    
    async def _manual_start(self, query):
        """Ручной запуск процесса для тестирования."""
        await query.edit_message_text("🚀 Запускаю процесс вручную для тестирования...")
        await self._run_full_automatic_process()
    
    async def _show_status(self, query):
        """Показать статус через callback."""
        status_text = "📊 *Текущий статус:*\n\n"
        
        if hasattr(self.manager, 'news') and self.manager.news:
            status_text += "✅ Новость получена\n"
        else:
            status_text += "⭕ Новость не получена\n"
            
        if hasattr(self.manager, 'scripts') and self.manager.scripts:
            status_text += f"✅ Сценарии созданы ({len(self.manager.scripts)} шт.)\n"
        else:
            status_text += "⭕ Сценарии не созданы\n"
            
        if hasattr(self.manager, 'winner_script') and self.manager.winner_script:
            status_text += "✅ Лучший сценарий выбран\n"
        else:
            status_text += "⭕ Лучший сценарий не выбран\n"
            
        if hasattr(self.manager, 'image_path') and self.manager.image_path:
            status_text += "✅ Изображение создано\n"
        else:
            status_text += "⭕ Изображение не создано\n"
            
        if hasattr(self.manager, 'publication_results') and self.manager.publication_results:
            status_text += "✅ Комикс опубликован\n"
        else:
            status_text += "⭕ Комикс не опубликован\n"
        
        await query.edit_message_text(status_text, parse_mode='Markdown')
    
    async def _test_publish(self, query):
        """Тест публикации с тестовым изображением."""
        await query.edit_message_text("🧪 Запускаю тест публикации...")
        
        try:
            # Импортируем функции из тестового модуля
            from test_publish_now import create_test_image, create_test_script
            
            # Создаем тестовое изображение
            await self._send_status_message("🖼️ Создаю тестовое изображение...")
            test_image_path = create_test_image()
            
            # Создаем тестовый сценарий
            test_script = create_test_script()
            
            # Отправляем тестовое изображение с кнопкой публикации
            caption = f"🧪 *Тестовое изображение готово!*\n\n"
            caption += f"*{test_script.get('title', 'Без заголовка')}*\n"
            caption += f"Автор: {test_script.get('writer_name', 'Неизвестен')}\n"
            caption += f"Оценка: 95.5/100 (тестовая)\n\n"
            caption += "Нажмите кнопку для тестовой публикации в канал:"
            
            # Сохраняем тестовые данные в manager для публикации
            self.manager.image_path = test_image_path
            self.manager.winner_script = test_script
            self.manager.winner_score = 95.5
            self.manager.news = {
                "title": "Тестовая новость для проверки публикации",
                "content": "Это тестовая новость для проверки функции публикации в Telegram канал"
            }
            
            keyboard = [
                [InlineKeyboardButton("📤 Опубликовать сейчас", callback_data="approve_publication")],
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            with open(test_image_path, 'rb') as photo:
                await self.app.bot.send_photo(
                    chat_id=self.admin_chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при создании тестового изображения: {str(e)}")
    
    async def _show_schedule_settings(self, query):
        """Показать настройки расписания."""
        settings_text = "⏰ *Настройки расписания:*\n\n"
        settings_text += "🤖 **Автоматический режим:**\n"
        settings_text += f"• {NEWS_COLLECTION_HOUR:02d}:{NEWS_COLLECTION_MINUTE:02d} - Создание поста и отправка на одобрение\n"
        settings_text += f"• {PUBLICATION_TIME_HOUR:02d}:{PUBLICATION_TIME_MINUTE:02d} - Автоматическая публикация (после одобрения)\n\n"
        settings_text += "📅 **Расписание:**\n"
        settings_text += "• Каждый день\n"
        settings_text += "• Часовой пояс: CET\n\n"
        settings_text += "🔧 **Для изменения настроек** обратитесь к разработчику"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            settings_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _back_to_menu(self, query):
        """Возврат в главное меню."""
        keyboard = [
            [InlineKeyboardButton("🚀 Запустить процесс вручную", callback_data="manual_start")],
            [InlineKeyboardButton("📊 Статус", callback_data="show_status")],
            [InlineKeyboardButton("⏰ Настройки расписания", callback_data="schedule_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎭 *DailyComicBot Control Panel*\n\n"
            f"🤖 Автоматический режим: Каждый день в {NEWS_COLLECTION_HOUR:02d}:{NEWS_COLLECTION_MINUTE:02d} создается пост, в {PUBLICATION_TIME_HOUR:02d}:{PUBLICATION_TIME_MINUTE:02d} публикуется\n"
            "🔧 Ручной режим: Для тестирования и отладки\n\n"
            "Выберите действие:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _restart_full_process(self, query):
        """Перезапуск всего процесса."""
        await query.edit_message_text("🔄 Перезапускаю весь процесс...")
        await self._run_full_automatic_process()
    
    async def _send_status_message(self, message: str):
        """Отправка статусного сообщения."""
        await self.app.bot.send_message(
            chat_id=self.admin_chat_id,
            text=message,
            parse_mode='Markdown'
        )
    
    async def _send_multiple_images_result(self, image_results: List[Dict[str, Any]]):
        """Отправка результатов создания множественных изображений."""
        try:
            # ИСПРАВЛЕНО: Сохраняем результаты изображений в manager для последующего использования
            self.manager.image_results = image_results
            
            # Отправляем сообщение с информацией о процессе
            info_text = f"🖼️ *Создано {len([r for r in image_results if r['success']])} из {len(image_results)} изображений*\n\n"
            info_text += "Выберите лучшее изображение для публикации:"
            
            await self.app.bot.send_message(
                chat_id=self.admin_chat_id,
                text=info_text,
                parse_mode='Markdown'
            )
            
            # Отправляем каждое изображение отдельно с информацией о сценарии
            for result in image_results:
                if result["success"] and result["image_path"]:
                    script_info = result["script_info"]
                    script = script_info["script"]
                    
                    caption = f"🏆 *Топ-{script_info['rank']} сценарий*\n\n"
                    caption += f"*{script.get('title', 'Без заголовка')}*\n"
                    caption += f"✍️ Автор: {script.get('writer_name', 'Неизвестен')}\n"
                    caption += f"🏆 Оценка жюри: {script_info['average_score']:.1f}/100\n\n"
                    
                    # Показываем краткое содержание
                    if script.get('format') == 'text':
                        content = script.get('content', '')
                        if len(content) > 300:
                            caption += f"{content[:300]}...\n\n"
                        else:
                            caption += f"{content}\n\n"
                    else:
                        description = script.get('description', 'Нет описания')
                        if len(description) > 200:
                            caption += f"{description[:200]}...\n\n"
                        else:
                            caption += f"{description}\n\n"
                    
                    # Кнопки для выбора этого изображения
                    keyboard = [
                        [InlineKeyboardButton(f"✅ Выбрать топ-{script_info['rank']}", callback_data=f"select_image_{script_info['rank']}")],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    with open(result["image_path"], 'rb') as photo:
                        await self.app.bot.send_photo(
                            chat_id=self.admin_chat_id,
                            photo=photo,
                            caption=caption,
                            parse_mode='Markdown',
                            reply_markup=reply_markup
                        )
            
            # Отправляем общие кнопки управления
            general_keyboard = [
                [InlineKeyboardButton("🔄 Пересоздать все изображения", callback_data="regenerate_all_images")],
                [InlineKeyboardButton("🔄 Пересоздать сценарии", callback_data="regenerate_scripts")],
                [InlineKeyboardButton("🔄 Начать заново", callback_data="restart_full")]
            ]
            general_reply_markup = InlineKeyboardMarkup(general_keyboard)
            
            await self.app.bot.send_message(
                chat_id=self.admin_chat_id,
                text="🎯 *Или выберите другое действие:*",
                parse_mode='Markdown',
                reply_markup=general_reply_markup
            )
            
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при отправке изображений: {str(e)}")

    async def _select_image_by_rank(self, query, rank: int):
        """Выбор изображения по рангу для публикации."""
        try:
            await query.edit_message_caption(f"✅ Выбрано изображение топ-{rank} сценария для публикации!")
            
            # Получаем топ сценарии
            top_scripts = self.manager.select_top_scripts(4)
            if not top_scripts or rank > len(top_scripts):
                await self._send_error_message("❌ Не удалось найти выбранный сценарий")
                return
            
            # Находим выбранный сценарий
            selected_script_info = None
            for script_info in top_scripts:
                if script_info["rank"] == rank:
                    selected_script_info = script_info
                    break
            
            if not selected_script_info:
                await self._send_error_message("❌ Не удалось найти выбранный сценарий")
                return
            
            # Устанавливаем выбранный сценарий как winner
            self.manager.winner_script = selected_script_info["script"]
            self.manager.winner_score = selected_script_info["average_score"]
            
            # ИСПРАВЛЕНО: Используем уже созданные изображения из manager
            selected_image_path = None
            if hasattr(self.manager, 'image_results') and self.manager.image_results:
                for result in self.manager.image_results:
                    if result["script_info"]["rank"] == rank and result["success"]:
                        selected_image_path = result["image_path"]
                        break
            
            if not selected_image_path:
                await self._send_error_message("❌ Не удалось найти изображение для выбранного сценария")
                return
            
            # Устанавливаем выбранное изображение как основное
            self.manager.image_path = selected_image_path
            
            # Сохраняем выбранное изображение для планировщика
            self.manager.approved_image = {
                "image_path": selected_image_path,
                "script": self.manager.winner_script,
                "average_score": self.manager.winner_score
            }
            
            # Отправляем финальный пост на одобрение
            await self._send_final_post_for_approval(
                self.manager.news,
                {
                    "script": self.manager.winner_script,
                    "average_score": self.manager.winner_score
                },
                selected_image_path
            )
            
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при выборе изображения: {str(e)}")

    async def _regenerate_all_images(self, query):
        """Перегенерация всех изображений для топ-4 сценариев."""
        try:
            await query.edit_message_text("🔄 Пересоздаю все изображения...")
            
            # Получаем топ сценарии
            top_scripts = self.manager.select_top_scripts(4)
            if not top_scripts:
                await self._send_error_message("❌ Не удалось получить топ сценарии")
                return
            
            # Создаем новые изображения
            image_results = self.manager.create_images_for_top_scripts(top_scripts)
            if image_results:
                await self._send_multiple_images_result(image_results)
            else:
                await self._send_error_message("❌ Не удалось пересоздать изображения")
                
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при пересоздании изображений: {str(e)}")

    async def _send_error_message(self, message: str):
        """Отправка сообщения об ошибке."""
        keyboard = [
            [InlineKeyboardButton("🔄 Начать заново", callback_data="restart_full")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.app.bot.send_message(
            chat_id=self.admin_chat_id,
            text=message,
            reply_markup=reply_markup
        )
    
    async def notify_images_ready(self):
        """Уведомление о готовности изображений."""
        try:
            if hasattr(self.manager, 'image_results') and self.manager.image_results:
                await self._send_multiple_images_result(self.manager.image_results)
            else:
                await self._send_status_message("🖼️ Изображения готовы, но не найдены результаты")
        except Exception as e:
            telegram_logger.error(f"Ошибка при отправке уведомления о готовности изображений: {e}")
    
    # ===== НОВЫЕ МЕТОДЫ ДЛЯ АНЕКДОТОВ (НЕ ИЗМЕНЯЮТ СУЩЕСТВУЮЩИЙ ФУНКЦИОНАЛ) =====
    
    async def _create_joke(self, query):
        """Создание анекдота на основе новости дня."""
        try:
            await query.edit_message_text("🎭 Создаю анекдоты на основе новости дня...")
            
            # Проверяем, есть ли уже новость
            if not hasattr(self.manager, 'news') or not self.manager.news:
                # Получаем новость автоматически
                await self._send_status_message("📰 Получаю новость дня для анекдотов...")
                news = self.manager.collect_news(force_new_news=False)
                if not news:
                    await self._send_error_message("❌ Не удалось получить новость для анекдотов")
                    return
            
            # Запускаем процесс создания анекдотов
            await self._send_status_message("🎭 Создаю анекдоты от всех авторов...")
            
            # Используем manager для создания анекдотов
            results = self.manager.run_joke_process()
            
            if not results.get("success"):
                await self._send_error_message("❌ Не удалось создать анекдоты")
                return
            
            # Отправляем анекдоты для выбора
            if hasattr(self.manager, 'jokes') and self.manager.jokes:
                await self._send_jokes_for_selection(self.manager.jokes)
            else:
                await self._send_error_message("❌ Анекдоты не найдены")
                
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при создании анекдотов: {str(e)}")
    
    async def _regenerate_jokes(self, query):
        """Перегенерация анекдотов."""
        try:
            await query.edit_message_text("🔄 Создаю новые анекдоты...")
            
            # Используем существующую новость для перегенерации
            if hasattr(self.manager, 'news') and self.manager.news:
                results = self.manager.run_joke_process(news=self.manager.news)
                
                if results.get("success") and hasattr(self.manager, 'jokes') and self.manager.jokes:
                    await self._send_jokes_for_selection(self.manager.jokes)
                else:
                    await self._send_error_message("❌ Не удалось пересоздать анекдоты")
            else:
                await self._send_error_message("❌ Нет новости для перегенерации анекдотов")
                
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при перегенерации анекдотов: {str(e)}")
    
    async def _send_jokes_for_selection(self, jokes: List[Dict[str, Any]]):
        """Отправка анекдотов для выбора."""
        try:
            # Отправляем информационное сообщение
            info_text = f"🎭 *Создано {len(jokes)} анекдотов*\n\n"
            info_text += f"📰 Новость: {self.manager.news.get('title', 'Без заголовка')}\n\n"
            info_text += "Выберите лучший анекдот для публикации:"
            
            await self.app.bot.send_message(
                chat_id=self.admin_chat_id,
                text=info_text,
                parse_mode='Markdown'
            )
            
            # Отправляем каждый анекдот отдельно
            for joke in jokes:
                author_name = joke.get('writer_name', 'Неизвестный автор')
                author_type = joke.get('writer_type', 'Unknown')
                joke_title = joke.get('title', 'Без заголовка')
                joke_content = joke.get('content', 'Нет содержания')
                
                # Формируем текст анекдота
                joke_text = f"🎭 *Анекдот от {author_name}*\n\n"
                
                # Ограничиваем длину содержания
                if len(joke_content) > 800:
                    joke_text += f"{joke_content[:800]}..."
                else:
                    joke_text += f"{joke_content}"
                
                # Кнопки для выбора этого анекдота
                keyboard = [
                    [InlineKeyboardButton(f"✅ Выбрать этот анекдот", callback_data=f"select_joke_{author_type}")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.app.bot.send_message(
                    chat_id=self.admin_chat_id,
                    text=joke_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            
            # Отправляем общие кнопки управления
            general_keyboard = [
                [InlineKeyboardButton("🔄 Пересоздать анекдоты", callback_data="regenerate_jokes")],
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
            ]
            general_reply_markup = InlineKeyboardMarkup(general_keyboard)
            
            await self.app.bot.send_message(
                chat_id=self.admin_chat_id,
                text="🎯 *Или выберите другое действие:*",
                parse_mode='Markdown',
                reply_markup=general_reply_markup
            )
            
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при отправке анекдотов: {str(e)}")
    
    async def _select_joke(self, query, author_type: str):
        """Выбор анекдота конкретного автора."""
        try:
            await query.edit_message_text(f"✅ Выбран анекдот от {SCRIPTWRITERS.get(author_type, {}).get('name', author_type)}!")
            
            # Получаем анекдот выбранного автора
            selected_joke = self.manager.get_joke_by_author(author_type)
            if not selected_joke:
                await self._send_error_message(f"❌ Не удалось найти анекдот автора {author_type}")
                return
            
            # Устанавливаем выбранный анекдот
            self.manager.selected_joke = selected_joke
            
            # Отправляем выбранный анекдот для финального одобрения
            await self._send_joke_for_approval(selected_joke)
            
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при выборе анекдота: {str(e)}")
    
    async def _send_joke_for_approval(self, joke: Dict[str, Any]):
        """Отправка выбранного анекдота для финального одобрения."""
        try:
            author_name = joke.get('writer_name', 'Неизвестный автор')
            joke_title = joke.get('title', 'Без заголовка')
            joke_content = joke.get('content', 'Нет содержания')
            
            # Формируем финальный текст
            final_text = f"🎭 *Выбранный анекдот готов к публикации!*\n\n"
            final_text += f"📰 Новость: {self.manager.news.get('title', '')}\n\n"
            final_text += f"*{joke_title}*\n\n"
            final_text += f"{joke_content}\n\n"
            final_text += f"✍️ Автор: {author_name}\n\n"
            final_text += "Выберите действие:"
            
            keyboard = [
                [InlineKeyboardButton("📤 Опубликовать сейчас", callback_data="publish_joke_now")],
                [InlineKeyboardButton("⏰ Запланировать публикацию", callback_data="schedule_joke")],
                [InlineKeyboardButton("🔄 Выбрать другой анекдот", callback_data="regenerate_jokes")],
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.app.bot.send_message(
                chat_id=self.admin_chat_id,
                text=final_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при отправке анекдота для одобрения: {str(e)}")
    
    async def _publish_joke_now(self, query):
        """Немедленная публикация выбранного анекдота."""
        try:
            await query.edit_message_text("📤 Публикую анекдот в канал...")
            
            # Проверяем наличие выбранного анекдота
            if not hasattr(self.manager, 'selected_joke') or not self.manager.selected_joke:
                await self._send_error_message("❌ Нет выбранного анекдота для публикации")
                return
            
            # Публикуем анекдот через manager
            publication_result = self.manager.publish_joke()
            
            if publication_result and publication_result.get("success"):
                # Отправка подтверждения с результатами
                success_text = "✅ *Анекдот успешно опубликован в канале!*\n\n"
                success_text += f"📺 Канал: {publication_result.get('platforms', {}).get('telegram', {}).get('channel_id', 'Не указан')}\n"
                success_text += f"📝 Сообщение ID: {publication_result.get('platforms', {}).get('telegram', {}).get('message_id', 'Не указан')}\n"
                success_text += f"📅 Время: {publication_result.get('date', 'Не указано')}\n\n"
                success_text += f"🎭 Анекдот: {publication_result.get('joke_title', 'Без заголовка')}\n"
                success_text += f"✍️ Автор: {publication_result.get('author_name', 'Неизвестен')}"
                
                await self._send_status_message(success_text)
                
                # Логирование успешной публикации анекдота
                telegram_logger.info(f"✅ Анекдот успешно опубликован: {publication_result.get('joke_title')}")
                
            else:
                error_msg = publication_result.get('error', 'Неизвестная ошибка') if publication_result else 'Нет результата'
                await self._send_error_message(f"❌ Ошибка при публикации анекдота: {error_msg}")
            
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при публикации анекдота: {str(e)}")
    
    async def _schedule_joke(self, query):
        """Планирование публикации анекдота."""
        try:
            await query.edit_message_text("⏰ Планирую публикацию анекдота...")
            
            # Проверяем наличие выбранного анекдота
            if not hasattr(self.manager, 'selected_joke') or not self.manager.selected_joke:
                await self._send_error_message("❌ Нет выбранного анекдота для планирования")
                return
            
            # Получаем время публикации анекдотов (по умолчанию 14:00)
            joke_hour = int(os.getenv("JOKE_PUBLICATION_HOUR", "14"))
            joke_minute = int(os.getenv("JOKE_PUBLICATION_MINUTE", "0"))
            
            # Сохраняем анекдот для планировщика
            self.manager.scheduled_joke = {
                "joke": self.manager.selected_joke,
                "news_title": self.manager.news.get('title', ''),
                "scheduled_time": f"{joke_hour:02d}:{joke_minute:02d}",
                "approved": True
            }
            
            success_text = f"⏰ *Анекдот запланирован к публикации!*\n\n"
            success_text += f"🎭 Анекдот: {self.manager.selected_joke.get('title', 'Без заголовка')}\n"
            success_text += f"✍️ Автор: {self.manager.selected_joke.get('writer_name', 'Неизвестен')}\n"
            success_text += f"📅 Время публикации: {joke_hour:02d}:{joke_minute:02d}\n\n"
            success_text += "Анекдот будет автоматически опубликован в запланированное время."
            
            keyboard = [
                [InlineKeyboardButton("📤 Опубликовать сейчас", callback_data="publish_joke_now")],
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.app.bot.send_message(
                chat_id=self.admin_chat_id,
                text=success_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            # Логирование планирования
            telegram_logger.info(f"⏰ Анекдот запланирован: {self.manager.selected_joke.get('title')} на {joke_hour:02d}:{joke_minute:02d}")
            
        except Exception as e:
            await self._send_error_message(f"❌ Ошибка при планировании анекдота: {str(e)}")
    
    async def _approve_joke_publication(self, query):
        """Одобрение публикации анекдота (альтернативный метод)."""
        # Перенаправляем на немедленную публикацию
        await self._publish_joke_now(query)
    
    def _is_admin(self, update: Update) -> bool:
        """Проверка, является ли пользователь администратором."""
        return str(update.effective_user.id) == str(self.admin_chat_id)
    
    def _is_admin_callback(self, query) -> bool:
        """Проверка, является ли пользователь администратором (для callback)."""
        return str(query.from_user.id) == str(self.admin_chat_id)
    
    def setup_handlers(self):
        """Настройка обработчиков команд."""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Добавляем обработчик ошибок
        self.app.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок Telegram бота."""
        error = context.error
        
        if "Conflict" in str(error) and "getUpdates" in str(error):
            telegram_logger.warning("⚠️ Обнаружен конфликт: другой экземпляр бота уже запущен")
            telegram_logger.warning("Остановите другие экземпляры бота перед запуском нового")
        else:
            telegram_logger.error(f"Ошибка в Telegram боте: {error}")
            
        # Не отправляем сообщение пользователю, так как update может быть None
    
    async def run(self):
        """Запуск бота."""
        if not TELEGRAM_BOT_TOKEN:
            telegram_logger.error("TELEGRAM_BOT_TOKEN не установлен")
            return
            
        if not self.admin_chat_id:
            telegram_logger.error("TELEGRAM_ADMIN_CHAT_ID не установлен")
            return
        
        # Создание приложения
        self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Настройка обработчиков
        self.setup_handlers()
        
        # Запуск бота
        telegram_logger.info("Запуск Telegram бота...")
        await self.app.run_polling()


def main():
    """Основная функция для запуска бота."""
    bot = ComicBotTelegram()
    
    # Проверяем токен и chat_id перед запуском
    if not TELEGRAM_BOT_TOKEN:
        telegram_logger.error("TELEGRAM_BOT_TOKEN не установлен в .env файле")
        return
        
    if not TELEGRAM_ADMIN_CHAT_ID:
        telegram_logger.error("TELEGRAM_ADMIN_CHAT_ID не установлен в .env файле")
        return
    
    telegram_logger.info(f"Запуск бота для админа: {TELEGRAM_ADMIN_CHAT_ID}")
    
    # Простой запуск
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        telegram_logger.info("Бот остановлен пользователем")
    except Exception as e:
        telegram_logger.error(f"Ошибка при запуске бота: {e}")


if __name__ == "__main__":
    main()
