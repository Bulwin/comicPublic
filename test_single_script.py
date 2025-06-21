#!/usr/bin/env python3
"""
Тест генерации сценария одним агентом.
Упрощенная версия для быстрой проверки работы GPT Assistants API.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).resolve().parent))

from tools.news_tools import get_top_news
from agents.scriptwriter import ScriptwriterAgent
from utils.logger import info, error, warning
from config import SCRIPTWRITERS

def test_single_scriptwriter():
    """Тест генерации сценария одним агентом."""
    
    print("=" * 80)
    print("ТЕСТ ОДНОГО АГЕНТА-СЦЕНАРИСТА")
    print("=" * 80)
    
    # 1. Получение новости
    print("🔄 Получение новости...")
    try:
        news = get_top_news()
        if not news:
            print("❌ Не удалось получить новость")
            return False
        
        print(f"✅ Новость получена: {news.get('title', '')[:50]}...")
        print(f"   Содержание: {news.get('content', '')[:100]}...")
        
    except Exception as e:
        print(f"❌ Ошибка при получении новости: {e}")
        return False
    
    # 2. Выбор агента для тестирования (тип A - классический)
    writer_type = "A"
    writer_name = SCRIPTWRITERS[writer_type]["name"]
    
    print(f"\n🎭 Тестирование агента: {writer_name} (тип {writer_type})")
    
    # 3. Создание агента
    try:
        agent = ScriptwriterAgent(writer_type)
        print(f"✅ Агент {writer_name} инициализирован")
        
    except Exception as e:
        print(f"❌ Ошибка при создании агента: {e}")
        return False
    
    # 4. Генерация сценария
    print(f"\n📝 Генерация сценария...")
    try:
        script = agent.create_script(news)
        
        if not script:
            print("❌ Сценарий не создан")
            return False
        
        print(f"✅ Сценарий создан!")
        print(f"   Заголовок: {script.get('title', 'Без заголовка')}")
        print(f"   Описание: {script.get('description', 'Без описания')[:100]}...")
        print(f"   Панелей: {len(script.get('panels', []))}")
        print(f"   Подпись: {script.get('caption', 'Без подписи')[:50]}...")
        
    except Exception as e:
        print(f"❌ Ошибка при генерации сценария: {e}")
        return False
    
    # 5. Проверка структуры сценария
    print(f"\n🔍 Проверка структуры сценария...")
    
    required_fields = ["title", "description", "panels", "caption"]
    missing_fields = []
    
    for field in required_fields:
        if field not in script:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ Отсутствуют поля: {missing_fields}")
        return False
    
    # Проверка панелей
    panels = script.get("panels", [])
    if len(panels) != 4:
        print(f"❌ Неверное количество панелей: {len(panels)} (ожидается 4)")
        return False
    
    # Проверка содержимого панелей
    empty_panels = []
    for i, panel in enumerate(panels):
        has_description = bool(panel.get('description', '').strip())
        has_dialog = bool(panel.get('dialog', []))
        has_narration = bool(panel.get('narration', '').strip())
        
        if not (has_description or has_dialog or has_narration):
            empty_panels.append(i + 1)
    
    if empty_panels:
        print(f"⚠️  Пустые панели: {empty_panels}")
    else:
        print("✅ Все панели содержат контент")
    
    # 6. Сохранение результата
    print(f"\n💾 Сохранение результата...")
    
    test_result = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "single_scriptwriter",
        "writer_type": writer_type,
        "writer_name": writer_name,
        "news": {
            "title": news.get("title", ""),
            "content": news.get("content", "")[:200] + "..." if len(news.get("content", "")) > 200 else news.get("content", "")
        },
        "script": script,
        "validation": {
            "has_all_fields": len(missing_fields) == 0,
            "correct_panel_count": len(panels) == 4,
            "empty_panels": empty_panels,
            "success": len(missing_fields) == 0 and len(panels) == 4
        }
    }
    
    # Создаем папку для результатов если её нет
    results_dir = Path("data/test_results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    result_file = results_dir / "test_single_script.json"
    
    try:
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Результат сохранен: {result_file}")
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {e}")
        return False
    
    # 7. Итоговый результат
    print(f"\n" + "=" * 80)
    if test_result["validation"]["success"]:
        print("🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print(f"   ✅ Агент {writer_name} корректно создал сценарий")
        print(f"   ✅ Все обязательные поля присутствуют")
        print(f"   ✅ Создано 4 панели")
        if not empty_panels:
            print(f"   ✅ Все панели содержат контент")
        else:
            print(f"   ⚠️  Некоторые панели пустые: {empty_panels}")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН")
        if missing_fields:
            print(f"   ❌ Отсутствуют поля: {missing_fields}")
        if len(panels) != 4:
            print(f"   ❌ Неверное количество панелей: {len(panels)}")
    
    print("=" * 80)
    
    return test_result["validation"]["success"]

if __name__ == "__main__":
    success = test_single_scriptwriter()
    sys.exit(0 if success else 1)
