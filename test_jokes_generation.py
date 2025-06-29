#!/usr/bin/env python3
"""
Тестовый скрипт для проверки генерации анекдотов.
Этап 1: Базовая инфраструктура.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).resolve().parent))

def test_joke_writer_import():
    """Тест импорта модуля joke_writer."""
    print("🧪 Тест 1: Импорт модуля joke_writer")
    try:
        from agents.joke_writer import JokeWriterAgent, get_joke_writer
        print("✅ Модуль joke_writer успешно импортирован")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта joke_writer: {e}")
        return False

def test_storage_functions():
    """Тест функций хранения анекдотов."""
    print("\n🧪 Тест 2: Функции хранения анекдотов")
    try:
        from tools.storage_tools import store_joke, store_jokes, load_jokes
        print("✅ Функции хранения анекдотов успешно импортированы")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта функций хранения: {e}")
        return False

def test_assistants_api_functions():
    """Тест функций assistants_api для анекдотов."""
    print("\n🧪 Тест 3: Функции assistants_api для анекдотов")
    try:
        from utils.assistants_api import invoke_joke_writer
        print("✅ Функция invoke_joke_writer успешно импортирована")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта функций assistants_api: {e}")
        return False

def test_joke_writer_initialization():
    """Тест инициализации JokeWriterAgent."""
    print("\n🧪 Тест 4: Инициализация JokeWriterAgent")
    try:
        from agents.joke_writer import JokeWriterAgent
        agent = JokeWriterAgent()
        print(f"✅ JokeWriterAgent успешно инициализирован")
        print(f"   - news: {agent.news}")
        print(f"   - jokes: {len(agent.jokes)} анекдотов")
        print(f"   - selected_joke: {agent.selected_joke}")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации JokeWriterAgent: {e}")
        return False

def test_joke_storage():
    """Тест сохранения и загрузки анекдотов."""
    print("\n🧪 Тест 5: Сохранение и загрузка анекдотов")
    try:
        from tools.storage_tools import store_joke, load_jokes
        
        # Создаем тестовый анекдот
        test_joke = {
            "joke_id": "TEST_20250630000000",
            "writer_type": "A",
            "writer_name": "Тестовый автор",
            "title": "Тестовый анекдот",
            "content": "Это тестовый анекдот для проверки функциональности.",
            "news": {
                "title": "Тестовая новость",
                "content": "Содержание тестовой новости"
            },
            "created_at": datetime.now().isoformat()
        }
        
        # Сохраняем анекдот
        success = store_joke(test_joke)
        if not success:
            print("❌ Не удалось сохранить тестовый анекдот")
            return False
        
        print("✅ Тестовый анекдот успешно сохранен")
        
        # Загружаем анекдоты
        jokes = load_jokes()
        print(f"✅ Загружено {len(jokes)} анекдотов")
        
        # Проверяем, что наш анекдот есть в списке
        found = False
        for joke in jokes:
            if joke.get("joke_id") == "TEST_20250630000000":
                found = True
                print(f"✅ Тестовый анекдот найден: {joke.get('title')}")
                break
        
        if not found:
            print("❌ Тестовый анекдот не найден в загруженных данных")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при тестировании хранения: {e}")
        return False

def test_joke_generation_with_stub():
    """Тест генерации анекдотов с заглушкой."""
    print("\n🧪 Тест 6: Генерация анекдотов с заглушкой")
    try:
        from agents.joke_writer import JokeWriterAgent
        
        # Создаем тестовую новость
        test_news = {
            "title": "Тестовая новость для анекдота",
            "content": "Это тестовая новость для проверки генерации анекдотов. В ней нет ничего особенного, но она должна вдохновить на создание смешного анекдота."
        }
        
        # Инициализируем агента
        agent = JokeWriterAgent()
        
        # Генерируем анекдоты
        print("🔄 Генерируем анекдоты...")
        jokes = agent.generate_jokes(test_news)
        
        if not jokes:
            print("❌ Не удалось сгенерировать анекдоты")
            return False
        
        print(f"✅ Сгенерировано {len(jokes)} анекдотов")
        
        # Проверяем каждый анекдот
        for i, joke in enumerate(jokes):
            print(f"   Анекдот {i+1}:")
            print(f"     - ID: {joke.get('joke_id', 'Нет ID')}")
            print(f"     - Автор: {joke.get('writer_name', 'Неизвестен')}")
            print(f"     - Заголовок: {joke.get('title', 'Без заголовка')}")
            print(f"     - Содержание: {joke.get('content', 'Нет содержания')[:100]}...")
        
        # Тестируем выбор лучшего анекдота
        best_joke = agent.select_best_joke()
        if best_joke:
            print(f"✅ Выбран лучший анекдот: {best_joke.get('title')}")
        else:
            print("❌ Не удалось выбрать лучший анекдот")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при генерации анекдотов: {e}")
        return False

def test_joke_writer_by_author():
    """Тест получения анекдота конкретного автора."""
    print("\n🧪 Тест 7: Получение анекдота по автору")
    try:
        from agents.joke_writer import JokeWriterAgent
        
        # Создаем тестовую новость
        test_news = {
            "title": "Новость для теста авторов",
            "content": "Тестовая новость для проверки получения анекдотов по авторам."
        }
        
        # Инициализируем агента и генерируем анекдоты
        agent = JokeWriterAgent()
        jokes = agent.generate_jokes(test_news)
        
        if not jokes:
            print("❌ Не удалось сгенерировать анекдоты для теста")
            return False
        
        # Тестируем получение анекдота по автору
        for author_type in ["A", "B", "C", "D", "E"]:
            joke = agent.get_joke_by_author(author_type)
            if joke:
                print(f"✅ Анекдот автора {author_type}: {joke.get('title')}")
            else:
                print(f"⚠️ Анекдот автора {author_type} не найден")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при тестировании получения по автору: {e}")
        return False

def main():
    """Основная функция тестирования."""
    print("🎭 Тестирование базовой инфраструктуры анекдотов")
    print("=" * 60)
    
    tests = [
        test_joke_writer_import,
        test_storage_functions,
        test_assistants_api_functions,
        test_joke_writer_initialization,
        test_joke_storage,
        test_joke_generation_with_stub,
        test_joke_writer_by_author
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
        print("🎉 Все тесты пройдены! Базовая инфраструктура анекдотов работает.")
        print("\n✅ Этап 1 завершен. Можно переходить к Этапу 2.")
    else:
        print("⚠️ Некоторые тесты провалены. Необходимо исправить ошибки.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
