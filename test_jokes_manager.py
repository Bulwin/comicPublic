#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции анекдотов в manager.
Этап 2: Интеграция в manager.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).resolve().parent))

def test_manager_import():
    """Тест импорта обновленного manager."""
    print("🧪 Тест 1: Импорт обновленного manager")
    try:
        from agents.manager import ManagerAgent, get_manager
        print("✅ Обновленный manager успешно импортирован")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта manager: {e}")
        return False

def test_manager_initialization():
    """Тест инициализации manager с новыми атрибутами."""
    print("\n🧪 Тест 2: Инициализация manager с новыми атрибутами")
    try:
        from agents.manager import ManagerAgent
        manager = ManagerAgent()
        
        # Проверяем старые атрибуты (не должны сломаться)
        print(f"✅ Старые атрибуты:")
        print(f"   - news: {manager.news}")
        print(f"   - scripts: {len(manager.scripts)} сценариев")
        print(f"   - evaluations: {len(manager.evaluations)} оценок")
        print(f"   - winner_script: {manager.winner_script}")
        print(f"   - image_path: {manager.image_path}")
        print(f"   - publication_results: {manager.publication_results}")
        
        # Проверяем новые атрибуты для анекдотов
        print(f"✅ Новые атрибуты для анекдотов:")
        print(f"   - jokes: {len(manager.jokes)} анекдотов")
        print(f"   - selected_joke: {manager.selected_joke}")
        print(f"   - joke_publication_results: {manager.joke_publication_results}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации manager: {e}")
        return False

def test_manager_joke_methods():
    """Тест наличия новых методов для анекдотов."""
    print("\n🧪 Тест 3: Наличие новых методов для анекдотов")
    try:
        from agents.manager import ManagerAgent
        manager = ManagerAgent()
        
        # Проверяем наличие новых методов
        methods_to_check = [
            'generate_jokes',
            'select_best_joke',
            'get_joke_by_author',
            'publish_joke',
            'run_joke_process'
        ]
        
        for method_name in methods_to_check:
            if hasattr(manager, method_name):
                method = getattr(manager, method_name)
                if callable(method):
                    print(f"✅ Метод {method_name} найден и вызываемый")
                else:
                    print(f"❌ {method_name} найден, но не является методом")
                    return False
            else:
                print(f"❌ Метод {method_name} не найден")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке методов: {e}")
        return False

def test_manager_joke_generation():
    """Тест генерации анекдотов через manager."""
    print("\n🧪 Тест 4: Генерация анекдотов через manager")
    try:
        from agents.manager import ManagerAgent
        manager = ManagerAgent()
        
        # Создаем тестовую новость
        test_news = {
            "title": "Тестовая новость для manager",
            "content": "Это тестовая новость для проверки генерации анекдотов через manager. Она должна вдохновить на создание смешных анекдотов."
        }
        
        # Генерируем анекдоты через manager
        print("🔄 Генерируем анекдоты через manager...")
        jokes = manager.generate_jokes(test_news)
        
        if not jokes:
            print("❌ Не удалось сгенерировать анекдоты через manager")
            return False
        
        print(f"✅ Сгенерировано {len(jokes)} анекдотов через manager")
        
        # Проверяем, что анекдоты сохранились в manager
        if len(manager.jokes) != len(jokes):
            print(f"❌ Анекдоты не сохранились в manager: {len(manager.jokes)} != {len(jokes)}")
            return False
        
        print(f"✅ Анекдоты сохранены в manager: {len(manager.jokes)} анекдотов")
        
        # Проверяем каждый анекдот
        for i, joke in enumerate(jokes):
            print(f"   Анекдот {i+1}:")
            print(f"     - ID: {joke.get('joke_id', 'Нет ID')}")
            print(f"     - Автор: {joke.get('writer_name', 'Неизвестен')}")
            print(f"     - Заголовок: {joke.get('title', 'Без заголовка')}")
            print(f"     - Содержание: {joke.get('content', 'Нет содержания')[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при генерации анекдотов через manager: {e}")
        return False

def test_manager_joke_selection():
    """Тест выбора лучшего анекдота через manager."""
    print("\n🧪 Тест 5: Выбор лучшего анекдота через manager")
    try:
        from agents.manager import ManagerAgent
        manager = ManagerAgent()
        
        # Создаем тестовую новость и генерируем анекдоты
        test_news = {
            "title": "Новость для теста выбора",
            "content": "Тестовая новость для проверки выбора лучшего анекдота через manager."
        }
        
        jokes = manager.generate_jokes(test_news)
        if not jokes:
            print("❌ Не удалось сгенерировать анекдоты для теста выбора")
            return False
        
        # Выбираем лучший анекдот
        print("🔄 Выбираем лучший анекдот...")
        best_joke = manager.select_best_joke()
        
        if not best_joke:
            print("❌ Не удалось выбрать лучший анекдот")
            return False
        
        print(f"✅ Выбран лучший анекдот: {best_joke.get('title')} от {best_joke.get('writer_name')}")
        
        # Проверяем, что анекдот сохранился в manager
        if manager.selected_joke != best_joke:
            print("❌ Выбранный анекдот не сохранился в manager")
            return False
        
        print("✅ Выбранный анекдот сохранен в manager")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при выборе лучшего анекдота: {e}")
        return False

def test_manager_joke_by_author():
    """Тест получения анекдота по автору через manager."""
    print("\n🧪 Тест 6: Получение анекдота по автору через manager")
    try:
        from agents.manager import ManagerAgent
        manager = ManagerAgent()
        
        # Создаем тестовую новость и генерируем анекдоты
        test_news = {
            "title": "Новость для теста авторов",
            "content": "Тестовая новость для проверки получения анекдотов по авторам через manager."
        }
        
        jokes = manager.generate_jokes(test_news)
        if not jokes:
            print("❌ Не удалось сгенерировать анекдоты для теста авторов")
            return False
        
        # Тестируем получение анекдота по автору
        for author_type in ["A", "B", "C", "D", "E"]:
            joke = manager.get_joke_by_author(author_type)
            if joke:
                print(f"✅ Анекдот автора {author_type}: {joke.get('title')}")
            else:
                print(f"⚠️ Анекдот автора {author_type} не найден")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при получении анекдотов по автору: {e}")
        return False

def test_manager_joke_process():
    """Тест полного процесса создания анекдотов через manager."""
    print("\n🧪 Тест 7: Полный процесс создания анекдотов через manager")
    try:
        from agents.manager import ManagerAgent
        manager = ManagerAgent()
        
        # Создаем тестовую новость
        test_news = {
            "title": "Новость для полного процесса",
            "content": "Тестовая новость для проверки полного процесса создания анекдотов через manager."
        }
        
        # Запускаем полный процесс
        print("🔄 Запускаем полный процесс создания анекдотов...")
        results = manager.run_joke_process(news=test_news)
        
        if not results.get("success"):
            print("❌ Полный процесс завершился неуспешно")
            print(f"   Результаты: {results}")
            return False
        
        print("✅ Полный процесс создания анекдотов завершен успешно")
        
        # Проверяем результаты каждого шага
        steps = results.get("steps", {})
        for step_name, step_data in steps.items():
            success = step_data.get("success", False)
            status = "✅" if success else "❌"
            print(f"   {status} {step_name}: {step_data}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при выполнении полного процесса: {e}")
        return False

def test_manager_news_reuse():
    """Тест переиспользования новости между комиксами и анекдотами."""
    print("\n🧪 Тест 8: Переиспользование новости между комиксами и анекдотами")
    try:
        from agents.manager import ManagerAgent
        manager = ManagerAgent()
        
        # Устанавливаем новость в manager (имитируем получение для комиксов)
        test_news = {
            "title": "Общая новость для комиксов и анекдотов",
            "content": "Эта новость будет использована и для комиксов, и для анекдотов."
        }
        manager.news = test_news
        
        print(f"✅ Новость установлена в manager: {test_news['title']}")
        
        # Генерируем анекдоты без передачи новости (должна использоваться существующая)
        print("🔄 Генерируем анекдоты без передачи новости...")
        jokes = manager.generate_jokes()
        
        if not jokes:
            print("❌ Не удалось сгенерировать анекдоты с существующей новостью")
            return False
        
        print(f"✅ Анекдоты сгенерированы с использованием существующей новости")
        print(f"   Количество анекдотов: {len(jokes)}")
        
        # Проверяем, что новость в анекдотах соответствует установленной
        for joke in jokes:
            joke_news = joke.get("news", {})
            if joke_news.get("title") != test_news["title"]:
                print(f"❌ Новость в анекдоте не соответствует установленной")
                return False
        
        print("✅ Новость корректно переиспользована в анекдотах")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при тестировании переиспользования новости: {e}")
        return False

def test_manager_compatibility():
    """Тест совместимости - старые методы manager должны работать."""
    print("\n🧪 Тест 9: Совместимость - старые методы manager")
    try:
        from agents.manager import ManagerAgent
        manager = ManagerAgent()
        
        # Проверяем, что старые методы все еще существуют
        old_methods = [
            'collect_news',
            'generate_scripts',
            'evaluate_scripts',
            'select_winner',
            'create_image',
            'publish_comic',
            'run_full_process'
        ]
        
        for method_name in old_methods:
            if hasattr(manager, method_name):
                method = getattr(manager, method_name)
                if callable(method):
                    print(f"✅ Старый метод {method_name} доступен")
                else:
                    print(f"❌ {method_name} найден, но не является методом")
                    return False
            else:
                print(f"❌ Старый метод {method_name} не найден")
                return False
        
        print("✅ Все старые методы manager доступны - совместимость сохранена")
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке совместимости: {e}")
        return False

def main():
    """Основная функция тестирования."""
    print("🎭 Тестирование интеграции анекдотов в manager")
    print("=" * 60)
    
    tests = [
        test_manager_import,
        test_manager_initialization,
        test_manager_joke_methods,
        test_manager_joke_generation,
        test_manager_joke_selection,
        test_manager_joke_by_author,
        test_manager_joke_process,
        test_manager_news_reuse,
        test_manager_compatibility
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
        print("🎉 Все тесты пройдены! Интеграция анекдотов в manager работает.")
        print("\n✅ Этап 2 завершен. Можно переходить к Этапу 3.")
    else:
        print("⚠️ Некоторые тесты провалены. Необходимо исправить ошибки.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
