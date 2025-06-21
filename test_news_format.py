#!/usr/bin/env python3
"""
Тестирование этапа получения новостей с проверкой формата.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).resolve().parent))

from tools.news_tools import get_top_news, extract_title, extract_news_content
from utils.logger import info, error, warning
from utils.important_logger import log_perplexity_response

def test_news_format():
    """Тестирование получения новости и проверка формата."""
    
    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ ЭТАПА 1: ПОЛУЧЕНИЕ НОВОСТИ")
    print("="*80 + "\n")
    
    # Получаем новость
    print("🔄 Получение новости дня...")
    news = get_top_news(force_new=True)
    
    if not news:
        print("❌ ОШИБКА: Не удалось получить новость!")
        return False
    
    # Проверяем формат
    print("\n📋 ПРОВЕРКА ФОРМАТА НОВОСТИ:")
    print("-" * 40)
    
    # Проверка обязательных полей
    required_fields = ['title', 'content', 'date', 'source']
    missing_fields = []
    
    for field in required_fields:
        if field not in news:
            missing_fields.append(field)
            print(f"❌ Отсутствует поле: {field}")
        else:
            print(f"✅ Поле '{field}' присутствует")
    
    if missing_fields:
        print(f"\n❌ ОШИБКА: Отсутствуют обязательные поля: {missing_fields}")
        return False
    
    # Детальная проверка содержимого
    print("\n📊 ДЕТАЛЬНАЯ ПРОВЕРКА СОДЕРЖИМОГО:")
    print("-" * 40)
    
    # Проверка заголовка
    title = news.get('title', '')
    print(f"\n🔍 ЗАГОЛОВОК:")
    print(f"   Длина: {len(title)} символов")
    print(f"   Содержимое: {title}")
    
    if not title:
        print("   ❌ ОШИБКА: Заголовок пустой!")
        return False
    elif len(title) < 10:
        print("   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Заголовок слишком короткий!")
    else:
        print("   ✅ Заголовок корректный")
    
    # Проверка содержания
    content = news.get('content', '')
    print(f"\n🔍 СОДЕРЖАНИЕ:")
    print(f"   Длина: {len(content)} символов")
    print(f"   Первые 200 символов: {content[:200]}...")
    
    if not content:
        print("   ❌ ОШИБКА: Содержание пустое!")
        return False
    elif len(content) < 50:
        print("   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Содержание слишком короткое!")
    else:
        print("   ✅ Содержание корректное")
    
    # Проверка на дублирование заголовка в содержании
    print(f"\n🔍 ПРОВЕРКА НА ДУБЛИРОВАНИЕ:")
    if content.startswith('**ЗАГОЛОВОК**') or 'ЗАГОЛОВОК:' in content[:100]:
        print("   ⚠️  ОБНАРУЖЕНО дублирование заголовка в содержании")
        print("   🔧 Применяем очистку...")
        cleaned_content = extract_news_content(content)
        news['content'] = cleaned_content
        print(f"   ✅ Очищенное содержание: {cleaned_content[:100]}...")
    else:
        print("   ✅ Дублирования не обнаружено")
    
    # Проверка даты
    date = news.get('date', '')
    print(f"\n🔍 ДАТА:")
    print(f"   Значение: {date}")
    try:
        parsed_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        print(f"   ✅ Дата в корректном формате ISO")
    except:
        print(f"   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Дата не в формате ISO")
    
    # Проверка источника
    source = news.get('source', '')
    print(f"\n🔍 ИСТОЧНИК:")
    print(f"   Значение: {source}")
    if source == 'perplexity':
        print(f"   ✅ Источник корректный")
    else:
        print(f"   ⚠️  Неожиданный источник")
    
    # Сохранение для проверки
    print("\n💾 СОХРАНЕНИЕ РЕЗУЛЬТАТА:")
    print("-" * 40)
    
    test_file = Path("data/test_results/test_news_format.json")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'news': news,
            'validation': {
                'has_all_fields': len(missing_fields) == 0,
                'title_length': len(title),
                'content_length': len(content),
                'has_duplication': content.startswith('**ЗАГОЛОВОК**') or 'ЗАГОЛОВОК:' in content[:100]
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Результат сохранен в: {test_file}")
    
    # Итоговый результат
    print("\n" + "="*80)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print("="*80)
    print(f"\n✅ НОВОСТЬ ПОЛУЧЕНА И ПРОВЕРЕНА УСПЕШНО!")
    print(f"\nФормат новости для передачи в GPT:")
    print(f"- Заголовок: {title[:50]}...")
    print(f"- Содержание: {len(content)} символов")
    print(f"- Дата: {date}")
    print(f"- Источник: {source}")
    
    # Логирование в important_logger
    log_perplexity_response(news)
    
    return True

if __name__ == "__main__":
    try:
        success = test_news_format()
        if success:
            print("\n✅ Тест пройден успешно!")
            sys.exit(0)
        else:
            print("\n❌ Тест провален!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
