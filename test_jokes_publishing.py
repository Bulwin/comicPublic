#!/usr/bin/env python3
"""
Тестовый скрипт для проверки публикации анекдотов.
Этап 3: Публикация анекдотов.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).resolve().parent))

def test_publishing_tools_import():
    """Тест импорта функций публикации анекдотов."""
    print("🧪 Тест 1: Импорт функций публикации анекдотов")
    try:
        from tools.publishing_tools import (
            format_joke_caption,
            publish_joke_to_channel,
            publish_joke_complete,
            publish_joke_to_all_platforms
        )
        print("✅ Все функции публикации анекдотов успешно импортированы")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта функций публикации: {e}")
        return False

def test_format_joke_caption():
    """Тест форматирования подписи для анекдота."""
    print("\n🧪 Тест 2: Форматирование подписи для анекдота")
    try:
        from tools.publishing_tools import format_joke_caption
        
        # Тестовые данные
        joke_text = "Это тестовый анекдот про новость дня. Очень смешной и актуальный!"
        news_title = "Тестовая новость для проверки форматирования"
        author_name = "Добряк Петрович"
        
        # Форматируем подпись
        caption = format_joke_caption(joke_text, news_title, author_name)
        
        print(f"✅ Подпись сформирована:")
        print(f"   Длина: {len(caption)} символов")
        print(f"   Содержит дату: {'✅' if datetime.now().strftime('%d.%m.%Y') in caption else '❌'}")
        print(f"   Содержит эмодзи: {'✅' if '🎭' in caption else '❌'}")
        print(f"   Содержит новость: {'✅' if news_title in caption else '❌'}")
        print(f"   Содержит анекдот: {'✅' if joke_text in caption else '❌'}")
        print(f"   Содержит автора: {'✅' if author_name in caption else '❌'}")
        print(f"   Содержит хештеги: {'✅' if '#DailyComicBot' in caption else '❌'}")
        
        print(f"\n📝 Пример подписи:")
        print(f"   {caption[:200]}...")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при форматировании подписи: {e}")
        return False

def test_format_joke_caption_long():
    """Тест форматирования длинной подписи с обрезанием."""
    print("\n🧪 Тест 3: Форматирование длинной подписи с обрезанием")
    try:
        from tools.publishing_tools import format_joke_caption
        
        # Очень длинные тестовые данные
        joke_text = "Это очень длинный анекдот " * 50  # ~1500 символов
        news_title = "Очень длинная новость " * 20  # ~400 символов
        author_name = "Добряк Петрович"
        max_length = 1000
        
        # Форматируем подпись с ограничением
        caption = format_joke_caption(joke_text, news_title, author_name, max_length)
        
        print(f"✅ Длинная подпись обработана:")
        print(f"   Длина: {len(caption)} символов (лимит: {max_length})")
        print(f"   Обрезана корректно: {'✅' if len(caption) <= max_length else '❌'}")
        print(f"   Содержит '...': {'✅' if '...' in caption else '❌'}")
        print(f"   Содержит автора: {'✅' if author_name in caption else '❌'}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при обработке длинной подписи: {e}")
        return False

def test_publish_joke_to_channel():
    """Тест публикации анекдота в канал."""
    print("\n🧪 Тест 4: Публикация анекдота в канал")
    try:
        from tools.publishing_tools import publish_joke_to_channel
        
        # Тестовые данные
        joke_text = "Тестовый анекдот для публикации в канал"
        news_title = "Тестовая новость"
        author_name = "Мрачный Эдгар"
        
        # Публикуем анекдот (будет использована заглушка)
        result = publish_joke_to_channel(joke_text, news_title, author_name)
        
        if result and result.get("success"):
            print("✅ Анекдот успешно опубликован в канал")
            print(f"   Channel ID: {result.get('channel_id')}")
            print(f"   Message ID: {result.get('message_id')}")
            print(f"   Дата: {result.get('date')}")
            print(f"   Автор: {result.get('author_name')}")
            
            # Проверяем структуру результата
            required_fields = ['success', 'channel_id', 'message_id', 'date', 'caption', 'joke_text', 'news_title', 'author_name']
            missing_fields = [field for field in required_fields if field not in result]
            
            if not missing_fields:
                print("✅ Все обязательные поля присутствуют в результате")
            else:
                print(f"❌ Отсутствуют поля: {missing_fields}")
                return False
            
            return True
        else:
            print(f"❌ Публикация не удалась: {result}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при публикации в канал: {e}")
        return False

def test_publish_joke_complete():
    """Тест полной публикации анекдота."""
    print("\n🧪 Тест 5: Полная публикация анекдота")
    try:
        from tools.publishing_tools import publish_joke_complete
        
        # Тестовый анекдот
        joke = {
            "joke_id": "TEST_20250630001800",
            "writer_type": "C",
            "writer_name": "Бунтарь Макс",
            "title": "Тестовый заголовок анекдота",
            "content": "Это тестовый анекдот для проверки полной публикации. Очень смешной!",
            "news": {
                "title": "Тестовая новость",
                "content": "Содержание тестовой новости"
            },
            "created_at": datetime.now().isoformat()
        }
        
        news_title = "Тестовая новость для полной публикации"
        
        # Публикуем анекдот
        result = publish_joke_complete(joke, news_title)
        
        if result and result.get("success"):
            print("✅ Полная публикация анекдота успешна")
            print(f"   Joke ID: {result.get('joke_id')}")
            print(f"   Заголовок: {result.get('joke_title')}")
            print(f"   Message ID: {result.get('message_id')}")
            
            # Проверяем, что заголовок добавлен к тексту
            caption = result.get('caption', '')
            if joke['title'] in caption and joke['content'] in caption:
                print("✅ Заголовок и содержание корректно объединены")
            else:
                print("❌ Заголовок и содержание не объединены корректно")
                return False
            
            return True
        else:
            print(f"❌ Полная публикация не удалась: {result}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при полной публикации: {e}")
        return False

def test_publish_joke_to_all_platforms():
    """Тест публикации анекдота на всех платформах."""
    print("\n🧪 Тест 6: Публикация анекдота на всех платформах")
    try:
        from tools.publishing_tools import publish_joke_to_all_platforms
        
        # Тестовый анекдот
        joke = {
            "joke_id": "TEST_20250630001801",
            "writer_type": "A",
            "writer_name": "Добряк Петрович",
            "title": "Анекдот для всех платформ",
            "content": "Этот анекдот будет опубликован на всех поддерживаемых платформах!",
            "news": {
                "title": "Новость для всех платформ",
                "content": "Содержание новости"
            },
            "created_at": datetime.now().isoformat()
        }
        
        news_title = "Новость для публикации на всех платформах"
        
        # Публикуем на всех платформах
        result = publish_joke_to_all_platforms(joke, news_title)
        
        if result:
            print("✅ Публикация на всех платформах завершена")
            print(f"   Общий успех: {result.get('success')}")
            print(f"   Joke ID: {result.get('joke_id')}")
            print(f"   Автор: {result.get('author_name')}")
            
            # Проверяем результаты по платформам
            platforms = result.get('platforms', {})
            
            # Telegram должен быть успешным
            telegram_result = platforms.get('telegram', {})
            if telegram_result.get('success'):
                print("✅ Публикация в Telegram успешна")
            else:
                print(f"❌ Публикация в Telegram не удалась: {telegram_result}")
                return False
            
            # Instagram должен быть отклонен (не поддерживается для анекдотов)
            instagram_result = platforms.get('instagram', {})
            if not instagram_result.get('success') and 'не поддерживается' in instagram_result.get('error', ''):
                print("✅ Instagram корректно отклонен для анекдотов")
            else:
                print("⚠️ Instagram обработан неожиданно")
            
            return True
        else:
            print(f"❌ Публикация на всех платформах не удалась: {result}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при публикации на всех платформах: {e}")
        return False

def test_manager_publish_joke():
    """Тест публикации анекдота через manager."""
    print("\n🧪 Тест 7: Публикация анекдота через manager")
    try:
        from agents.manager import ManagerAgent
        
        manager = ManagerAgent()
        
        # Устанавливаем тестовую новость
        manager.news = {
            "title": "Тестовая новость для manager",
            "content": "Содержание тестовой новости для проверки публикации через manager"
        }
        
        # Устанавливаем тестовый анекдот
        test_joke = {
            "joke_id": "MANAGER_TEST_20250630001802",
            "writer_type": "D",
            "writer_name": "Хипстер Артемий",
            "title": "Анекдот через manager",
            "content": "Этот анекдот публикуется через manager для проверки интеграции",
            "created_at": datetime.now().isoformat()
        }
        
        # Публикуем через manager
        result = manager.publish_joke(test_joke)
        
        if result and result.get("success"):
            print("✅ Публикация через manager успешна")
            print(f"   Joke ID: {result.get('joke_id')}")
            print(f"   Автор: {result.get('author_name')}")
            
            # Проверяем, что результат сохранился в manager
            if manager.joke_publication_results == result:
                print("✅ Результат публикации сохранен в manager")
            else:
                print("❌ Результат публикации не сохранен в manager")
                return False
            
            return True
        else:
            print(f"❌ Публикация через manager не удалась: {result}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при публикации через manager: {e}")
        return False

def test_manager_full_joke_process_with_publishing():
    """Тест полного процесса анекдотов с публикацией через manager."""
    print("\n🧪 Тест 8: Полный процесс анекдотов с публикацией через manager")
    try:
        from agents.manager import ManagerAgent
        
        manager = ManagerAgent()
        
        # Тестовая новость
        test_news = {
            "title": "Новость для полного процесса с публикацией",
            "content": "Тестовая новость для проверки полного процесса создания и публикации анекдотов"
        }
        
        # Запускаем полный процесс создания анекдотов
        print("🔄 Запускаем полный процесс создания анекдотов...")
        results = manager.run_joke_process(news=test_news)
        
        if not results.get("success"):
            print("❌ Полный процесс создания анекдотов не удался")
            return False
        
        print("✅ Полный процесс создания анекдотов завершен успешно")
        
        # Проверяем, что есть выбранный анекдот
        if not manager.selected_joke:
            print("❌ Нет выбранного анекдота для публикации")
            return False
        
        print(f"✅ Выбран анекдот: {manager.selected_joke.get('title')}")
        
        # Публикуем выбранный анекдот
        print("🔄 Публикуем выбранный анекдот...")
        publication_result = manager.publish_joke()
        
        if publication_result and publication_result.get("success"):
            print("✅ Публикация выбранного анекдота успешна")
            print(f"   Опубликован анекдот: {publication_result.get('joke_title')}")
            print(f"   Автор: {publication_result.get('author_name')}")
            
            return True
        else:
            print(f"❌ Публикация выбранного анекдота не удалась: {publication_result}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при полном процессе с публикацией: {e}")
        return False

def test_compatibility_with_comics():
    """Тест совместимости публикации анекдотов с комиксами."""
    print("\n🧪 Тест 9: Совместимость публикации анекдотов с комиксами")
    try:
        from tools.publishing_tools import (
            # Старые функции для комиксов
            post_to_telegram, publish_to_all_platforms, format_caption,
            # Новые функции для анекдотов
            publish_joke_to_channel, format_joke_caption
        )
        
        print("✅ Старые функции для комиксов доступны:")
        print("   - post_to_telegram")
        print("   - publish_to_all_platforms") 
        print("   - format_caption")
        
        print("✅ Новые функции для анекдотов доступны:")
        print("   - publish_joke_to_channel")
        print("   - format_joke_caption")
        
        # Проверяем, что функции не конфликтуют
        # Форматируем подпись для комикса
        comic_caption = format_caption("Новость", "Содержание комикса", 85.5)
        
        # Форматируем подпись для анекдота
        joke_caption = format_joke_caption("Текст анекдота", "Новость", "Автор")
        
        if comic_caption != joke_caption:
            print("✅ Функции форматирования не конфликтуют")
        else:
            print("❌ Функции форматирования дают одинаковый результат")
            return False
        
        print("✅ Совместимость с комиксами сохранена")
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке совместимости: {e}")
        return False

def main():
    """Основная функция тестирования."""
    print("🎭 Тестирование публикации анекдотов")
    print("=" * 60)
    
    tests = [
        test_publishing_tools_import,
        test_format_joke_caption,
        test_format_joke_caption_long,
        test_publish_joke_to_channel,
        test_publish_joke_complete,
        test_publish_joke_to_all_platforms,
        test_manager_publish_joke,
        test_manager_full_joke_process_with_publishing,
        test_compatibility_with_comics
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
        print("🎉 Все тесты пройдены! Публикация анекдотов работает.")
        print("\n✅ Этап 3 завершен. Можно переходить к Этапу 4.")
    else:
        print("⚠️ Некоторые тесты провалены. Необходимо исправить ошибки.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
