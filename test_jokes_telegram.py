#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции анекдотов в Telegram бот.
Этап 4: Интеграция в Telegram бот.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import asyncio

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).resolve().parent))

def test_telegram_bot_import():
    """Тест импорта обновленного Telegram бота."""
    print("🧪 Тест 1: Импорт обновленного Telegram бота")
    try:
        from telegram_bot import ComicBotTelegram
        print("✅ Telegram бот успешно импортирован")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта Telegram бота: {e}")
        return False

def test_bot_initialization():
    """Тест инициализации бота."""
    print("\n🧪 Тест 2: Инициализация бота")
    try:
        from telegram_bot import ComicBotTelegram
        
        bot = ComicBotTelegram()
        
        # Проверяем наличие manager
        if hasattr(bot, 'manager'):
            print("✅ Manager инициализирован")
        else:
            print("❌ Manager не инициализирован")
            return False
        
        # Проверяем наличие admin_chat_id
        if hasattr(bot, 'admin_chat_id'):
            print("✅ Admin chat ID настроен")
        else:
            print("❌ Admin chat ID не настроен")
            return False
        
        print("✅ Бот успешно инициализирован")
        return True
    except Exception as e:
        print(f"❌ Ошибка при инициализации бота: {e}")
        return False

def test_new_joke_methods():
    """Тест наличия новых методов для анекдотов."""
    print("\n🧪 Тест 3: Наличие новых методов для анекдотов")
    try:
        from telegram_bot import ComicBotTelegram
        
        bot = ComicBotTelegram()
        
        # Список новых методов для анекдотов
        joke_methods = [
            '_create_joke',
            '_regenerate_jokes',
            '_send_jokes_for_selection',
            '_select_joke',
            '_send_joke_for_approval',
            '_publish_joke_now',
            '_schedule_joke',
            '_approve_joke_publication'
        ]
        
        missing_methods = []
        for method_name in joke_methods:
            if hasattr(bot, method_name):
                print(f"✅ Метод {method_name} найден")
            else:
                print(f"❌ Метод {method_name} отсутствует")
                missing_methods.append(method_name)
        
        if not missing_methods:
            print("✅ Все новые методы для анекдотов присутствуют")
            return True
        else:
            print(f"❌ Отсутствуют методы: {missing_methods}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при проверке методов: {e}")
        return False

def test_start_command_updated():
    """Тест обновленной команды /start с кнопкой анекдотов."""
    print("\n🧪 Тест 4: Обновленная команда /start")
    try:
        from telegram_bot import ComicBotTelegram
        
        bot = ComicBotTelegram()
        
        # Проверяем, что метод start_command существует
        if hasattr(bot, 'start_command'):
            print("✅ Метод start_command найден")
        else:
            print("❌ Метод start_command отсутствует")
            return False
        
        # Проверяем исходный код метода на наличие кнопки анекдотов
        import inspect
        source = inspect.getsource(bot.start_command)
        
        if "Создать анекдот" in source:
            print("✅ Кнопка 'Создать анекдот' найдена в start_command")
        else:
            print("❌ Кнопка 'Создать анекдот' не найдена в start_command")
            return False
        
        if "create_joke" in source:
            print("✅ Callback 'create_joke' найден в start_command")
        else:
            print("❌ Callback 'create_joke' не найден в start_command")
            return False
        
        print("✅ Команда /start обновлена корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке start_command: {e}")
        return False

def test_button_callback_updated():
    """Тест обновленного обработчика кнопок."""
    print("\n🧪 Тест 5: Обновленный обработчик кнопок")
    try:
        from telegram_bot import ComicBotTelegram
        
        bot = ComicBotTelegram()
        
        # Проверяем, что метод button_callback существует
        if hasattr(bot, 'button_callback'):
            print("✅ Метод button_callback найден")
        else:
            print("❌ Метод button_callback отсутствует")
            return False
        
        # Проверяем исходный код метода на наличие новых callback'ов
        import inspect
        source = inspect.getsource(bot.button_callback)
        
        joke_callbacks = [
            'create_joke',
            'regenerate_jokes',
            'select_joke_',
            'publish_joke_now',
            'schedule_joke',
            'approve_joke_publication'
        ]
        
        missing_callbacks = []
        for callback in joke_callbacks:
            if callback in source:
                print(f"✅ Callback '{callback}' найден в button_callback")
            else:
                print(f"❌ Callback '{callback}' не найден в button_callback")
                missing_callbacks.append(callback)
        
        if not missing_callbacks:
            print("✅ Все новые callback'ы для анекдотов присутствуют")
            return True
        else:
            print(f"❌ Отсутствуют callback'ы: {missing_callbacks}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при проверке button_callback: {e}")
        return False

def test_manager_integration():
    """Тест интеграции с manager для анекдотов."""
    print("\n🧪 Тест 6: Интеграция с manager для анекдотов")
    try:
        from telegram_bot import ComicBotTelegram
        from agents.manager import get_manager
        
        bot = ComicBotTelegram()
        manager = get_manager()
        
        # Проверяем, что manager имеет методы для анекдотов
        joke_manager_methods = [
            'generate_jokes',
            'select_best_joke',
            'get_joke_by_author',
            'publish_joke',
            'run_joke_process'
        ]
        
        missing_methods = []
        for method_name in joke_manager_methods:
            if hasattr(manager, method_name):
                print(f"✅ Manager метод {method_name} найден")
            else:
                print(f"❌ Manager метод {method_name} отсутствует")
                missing_methods.append(method_name)
        
        if not missing_methods:
            print("✅ Все методы manager для анекдотов присутствуют")
        else:
            print(f"❌ Отсутствуют методы manager: {missing_methods}")
            return False
        
        # Проверяем, что manager имеет атрибуты для анекдотов
        joke_attributes = ['jokes', 'selected_joke', 'joke_publication_results']
        
        missing_attributes = []
        for attr_name in joke_attributes:
            if hasattr(manager, attr_name):
                print(f"✅ Manager атрибут {attr_name} найден")
            else:
                print(f"❌ Manager атрибут {attr_name} отсутствует")
                missing_attributes.append(attr_name)
        
        if not missing_attributes:
            print("✅ Все атрибуты manager для анекдотов присутствуют")
            return True
        else:
            print(f"❌ Отсутствуют атрибуты manager: {missing_attributes}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при проверке интеграции с manager: {e}")
        return False

def test_joke_workflow_simulation():
    """Тест симуляции workflow анекдотов."""
    print("\n🧪 Тест 7: Симуляция workflow анекдотов")
    try:
        from telegram_bot import ComicBotTelegram
        from agents.manager import get_manager
        
        bot = ComicBotTelegram()
        manager = get_manager()
        
        # Симулируем создание анекдотов
        print("🔄 Симулируем создание анекдотов...")
        
        # Тестовая новость
        test_news = {
            "title": "Тестовая новость для Telegram бота",
            "content": "Это тестовая новость для проверки workflow анекдотов в Telegram боте"
        }
        
        # Устанавливаем новость в manager
        manager.news = test_news
        
        # Запускаем процесс создания анекдотов
        results = manager.run_joke_process(news=test_news)
        
        if results.get("success"):
            print("✅ Процесс создания анекдотов успешен")
        else:
            print("❌ Процесс создания анекдотов не удался")
            return False
        
        # Проверяем, что анекдоты созданы
        if hasattr(manager, 'jokes') and manager.jokes:
            print(f"✅ Создано {len(manager.jokes)} анекдотов")
        else:
            print("❌ Анекдоты не созданы")
            return False
        
        # Проверяем выбор лучшего анекдота
        best_joke = manager.select_best_joke()
        if best_joke:
            print(f"✅ Выбран лучший анекдот: {best_joke.get('title', 'Без заголовка')}")
        else:
            print("❌ Не удалось выбрать лучший анекдот")
            return False
        
        # Проверяем получение анекдота по автору
        joke_by_author = manager.get_joke_by_author('A')
        if joke_by_author:
            print(f"✅ Получен анекдот автора A: {joke_by_author.get('title', 'Без заголовка')}")
        else:
            print("❌ Не удалось получить анекдот автора A")
            return False
        
        print("✅ Симуляция workflow анекдотов успешна")
        return True
    except Exception as e:
        print(f"❌ Ошибка при симуляции workflow: {e}")
        return False

def test_publishing_integration():
    """Тест интеграции публикации анекдотов."""
    print("\n🧪 Тест 8: Интеграция публикации анекдотов")
    try:
        from telegram_bot import ComicBotTelegram
        from agents.manager import get_manager
        from tools.publishing_tools import publish_joke_to_all_platforms
        
        bot = ComicBotTelegram()
        manager = get_manager()
        
        # Тестовый анекдот
        test_joke = {
            "joke_id": "TELEGRAM_TEST_20250630002316",
            "writer_type": "A",
            "writer_name": "Добряк Петрович",
            "title": "Тестовый анекдот для Telegram",
            "content": "Это тестовый анекдот для проверки интеграции публикации в Telegram боте",
            "created_at": datetime.now().isoformat()
        }
        
        test_news_title = "Тестовая новость для публикации"
        
        # Проверяем функцию публикации
        publication_result = publish_joke_to_all_platforms(test_joke, test_news_title)
        
        if publication_result and publication_result.get("success"):
            print("✅ Функция публикации анекдотов работает")
            print(f"   Joke ID: {publication_result.get('joke_id')}")
            print(f"   Автор: {publication_result.get('author_name')}")
        else:
            print("❌ Функция публикации анекдотов не работает")
            return False
        
        # Проверяем интеграцию с manager
        manager.news = {"title": test_news_title}
        manager.selected_joke = test_joke
        
        manager_result = manager.publish_joke()
        
        if manager_result and manager_result.get("success"):
            print("✅ Публикация через manager работает")
        else:
            print("❌ Публикация через manager не работает")
            return False
        
        print("✅ Интеграция публикации анекдотов успешна")
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке интеграции публикации: {e}")
        return False

def test_compatibility_with_comics():
    """Тест совместимости с функциями комиксов."""
    print("\n🧪 Тест 9: Совместимость с функциями комиксов")
    try:
        from telegram_bot import ComicBotTelegram
        
        bot = ComicBotTelegram()
        
        # Проверяем, что старые методы для комиксов остались
        comic_methods = [
            '_continue_with_scripts',
            '_continue_with_image',
            '_send_news_for_approval',
            '_send_script_result',
            '_send_image_result',
            '_regenerate_news',
            '_regenerate_scripts',
            '_regenerate_image',
            '_approve_publication',
            '_run_full_automatic_process'
        ]
        
        missing_methods = []
        for method_name in comic_methods:
            if hasattr(bot, method_name):
                print(f"✅ Старый метод {method_name} сохранен")
            else:
                print(f"❌ Старый метод {method_name} отсутствует")
                missing_methods.append(method_name)
        
        if not missing_methods:
            print("✅ Все старые методы для комиксов сохранены")
        else:
            print(f"❌ Отсутствуют старые методы: {missing_methods}")
            return False
        
        # Проверяем, что старые callback'ы остались
        import inspect
        source = inspect.getsource(bot.button_callback)
        
        comic_callbacks = [
            'manual_start',
            'regenerate_news',
            'continue_with_news',
            'regenerate_scripts',
            'continue_with_script',
            'regenerate_image',
            'approve_publication'
        ]
        
        missing_callbacks = []
        for callback in comic_callbacks:
            if callback in source:
                print(f"✅ Старый callback '{callback}' сохранен")
            else:
                print(f"❌ Старый callback '{callback}' отсутствует")
                missing_callbacks.append(callback)
        
        if not missing_callbacks:
            print("✅ Все старые callback'ы для комиксов сохранены")
            return True
        else:
            print(f"❌ Отсутствуют старые callback'ы: {missing_callbacks}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при проверке совместимости: {e}")
        return False

def test_environment_variables():
    """Тест переменных окружения для анекдотов."""
    print("\n🧪 Тест 10: Переменные окружения для анекдотов")
    try:
        # Проверяем, что код корректно обрабатывает переменные окружения
        joke_hour = int(os.getenv("JOKE_PUBLICATION_HOUR", "14"))
        joke_minute = int(os.getenv("JOKE_PUBLICATION_MINUTE", "0"))
        
        print(f"✅ JOKE_PUBLICATION_HOUR: {joke_hour}")
        print(f"✅ JOKE_PUBLICATION_MINUTE: {joke_minute}")
        
        # Проверяем, что значения разумные
        if 0 <= joke_hour <= 23:
            print("✅ JOKE_PUBLICATION_HOUR в допустимом диапазоне")
        else:
            print("❌ JOKE_PUBLICATION_HOUR вне допустимого диапазона")
            return False
        
        if 0 <= joke_minute <= 59:
            print("✅ JOKE_PUBLICATION_MINUTE в допустимом диапазоне")
        else:
            print("❌ JOKE_PUBLICATION_MINUTE вне допустимого диапазона")
            return False
        
        print("✅ Переменные окружения для анекдотов настроены корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке переменных окружения: {e}")
        return False

def main():
    """Основная функция тестирования."""
    print("🎭 Тестирование интеграции анекдотов в Telegram бот")
    print("=" * 60)
    
    tests = [
        test_telegram_bot_import,
        test_bot_initialization,
        test_new_joke_methods,
        test_start_command_updated,
        test_button_callback_updated,
        test_manager_integration,
        test_joke_workflow_simulation,
        test_publishing_integration,
        test_compatibility_with_comics,
        test_environment_variables
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("❌ Тест провален")
        except Exception as e:
            print(f"❌ Тест завершился с ошибкой: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Интеграция анекдотов в Telegram бот работает.")
        print("\n✅ Этап 4 завершен. Можно переходить к Этапу 4.5 (настройка GPT Assistants).")
    else:
        print("⚠️ Некоторые тесты провалены. Необходимо исправить ошибки.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
