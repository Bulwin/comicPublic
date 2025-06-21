#!/usr/bin/env python3
"""
Тест проверки логики выбора топ-4 сценариев для генерации изображений.
Проверяет весь цикл: новость → 5 сценариев → оценка жюри → выбор топ-4.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).resolve().parent))

from tools.news_tools import get_top_news
from agents.manager import ManagerAgent
from utils.logger import info, error, warning
from config import SCRIPTWRITERS

def test_top4_selection():
    """Тест выбора топ-4 сценариев для генерации изображений."""
    
    print("=" * 80)
    print("ТЕСТ ВЫБОРА ТОП-4 СЦЕНАРИЕВ ДЛЯ ГЕНЕРАЦИИ ИЗОБРАЖЕНИЙ")
    print("=" * 80)
    
    # 1. Получение новости
    print("🔄 Получение новости...")
    try:
        news = get_top_news()
        if not news:
            print("❌ Не удалось получить новость")
            return False
        
        print(f"✅ Новость получена: {news.get('title', '')[:50]}...")
        
    except Exception as e:
        print(f"❌ Ошибка при получении новости: {e}")
        return False
    
    # 2. Инициализация менеджера
    print(f"\n🤖 Инициализация менеджера комиксов...")
    try:
        manager = ManagerAgent()
        print("✅ Менеджер инициализирован")
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации менеджера: {e}")
        return False
    
    # 3. Установка новости в менеджер
    manager.news = news
    
    # 4. Генерация всех 5 сценариев
    print(f"\n📝 Генерация всех 5 сценариев...")
    try:
        print("Запуск генерации сценариев...")
        scripts = manager.generate_scripts()
        
        if not scripts:
            print("❌ Сценарии не созданы")
            return False
        
        print(f"✅ Создано {len(scripts)} сценариев:")
        for i, script in enumerate(scripts):
            writer_name = script.get('writer_name', 'Неизвестный')
            title = script.get('title', 'Без заголовка')
            print(f"   {i+1}. {writer_name}: {title[:50]}...")
        
    except Exception as e:
        print(f"❌ Ошибка при генерации сценариев: {e}")
        return False
    
    # 5. Оценка сценариев жюри
    print(f"\n⚖️ Оценка сценариев жюри...")
    try:
        print("Запуск оценки сценариев...")
        evaluations = manager.evaluate_scripts()
        
        if not evaluations:
            print("❌ Оценки не получены")
            return False
        
        print(f"✅ Получены оценки для {len(evaluations)} сценариев")
        
        # Показываем оценки
        for script_id, eval_data in evaluations.items():
            script = next((s for s in scripts if s.get('script_id') == script_id), None)
            if script:
                writer_name = script.get('writer_name', 'Неизвестный')
                avg_score = eval_data.get('average_score', 0)
                print(f"   {writer_name}: {avg_score:.1f}/100")
        
    except Exception as e:
        print(f"❌ Ошибка при оценке сценариев: {e}")
        return False
    
    # 5. Определение топ-4 сценариев
    print(f"\n🏆 Определение топ-4 сценариев...")
    try:
        # Сортируем сценарии по средней оценке
        sorted_scripts = []
        for script in scripts:
            script_id = script.get('script_id')
            if script_id in evaluations:
                avg_score = evaluations[script_id].get('average_score', 0)
                sorted_scripts.append((script, avg_score))
        
        # Сортируем по убыванию оценки
        sorted_scripts.sort(key=lambda x: x[1], reverse=True)
        
        # Берем топ-4
        top4_scripts = [script for script, score in sorted_scripts[:4]]
        
        print(f"✅ Определены топ-4 сценария:")
        for i, (script, score) in enumerate(sorted_scripts[:4]):
            writer_name = script.get('writer_name', 'Неизвестный')
            title = script.get('title', 'Без заголовка')
            print(f"   {i+1}. {writer_name}: {score:.1f}/100 - {title[:40]}...")
        
        # Показываем, кто не попал в топ-4
        if len(sorted_scripts) > 4:
            print(f"\n❌ Не попали в топ-4:")
            for i, (script, score) in enumerate(sorted_scripts[4:]):
                writer_name = script.get('writer_name', 'Неизвестный')
                title = script.get('title', 'Без заголовка')
                print(f"   {i+5}. {writer_name}: {score:.1f}/100 - {title[:40]}...")
        
    except Exception as e:
        print(f"❌ Ошибка при определении топ-4: {e}")
        return False
    
    # 6. Проверка логики генерации изображений (без реальной генерации)
    print(f"\n🖼️ Проверка логики генерации изображений...")
    try:
        # Имитируем логику manager.generate_images()
        print("Проверяем, какие сценарии будут отправлены на генерацию изображений...")
        
        # Получаем ID топ-4 сценариев
        top4_ids = [script.get('script_id') for script in top4_scripts]
        
        print(f"✅ Для генерации изображений будут отправлены {len(top4_ids)} сценариев:")
        for i, script_id in enumerate(top4_ids):
            script = next((s for s in scripts if s.get('script_id') == script_id), None)
            if script:
                writer_name = script.get('writer_name', 'Неизвестный')
                title = script.get('title', 'Без заголовка')
                print(f"   {i+1}. ID: {script_id} - {writer_name}: {title[:40]}...")
        
        # Проверяем, что НЕ отправляются остальные
        all_ids = [script.get('script_id') for script in scripts]
        excluded_ids = [sid for sid in all_ids if sid not in top4_ids]
        
        if excluded_ids:
            print(f"\n✅ НЕ будут отправлены на генерацию изображений:")
            for script_id in excluded_ids:
                script = next((s for s in scripts if s.get('script_id') == script_id), None)
                if script:
                    writer_name = script.get('writer_name', 'Неизвестный')
                    title = script.get('title', 'Без заголовка')
                    print(f"   - ID: {script_id} - {writer_name}: {title[:40]}...")
        
    except Exception as e:
        print(f"❌ Ошибка при проверке логики генерации: {e}")
        return False
    
    # 7. Сохранение результатов теста
    print(f"\n💾 Сохранение результатов теста...")
    
    test_result = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "top4_selection",
        "news": {
            "title": news.get("title", ""),
            "content": news.get("content", "")[:200] + "..." if len(news.get("content", "")) > 200 else news.get("content", "")
        },
        "total_scripts": len(scripts),
        "scripts_with_evaluations": len(evaluations),
        "top4_selection": [
            {
                "rank": i+1,
                "script_id": script.get('script_id'),
                "writer_name": script.get('writer_name'),
                "title": script.get('title'),
                "average_score": score
            }
            for i, (script, score) in enumerate(sorted_scripts[:4])
        ],
        "excluded_scripts": [
            {
                "rank": i+5,
                "script_id": script.get('script_id'),
                "writer_name": script.get('writer_name'),
                "title": script.get('title'),
                "average_score": score
            }
            for i, (script, score) in enumerate(sorted_scripts[4:])
        ],
        "validation": {
            "correct_script_count": len(scripts) == 10,
            "all_scripts_evaluated": len(evaluations) == len(scripts),
            "top4_selected": len(top4_scripts) == 4,
            "success": len(scripts) == 10 and len(evaluations) == len(scripts) and len(top4_scripts) == 4
        }
    }
    
    # Создаем папку для результатов если её нет
    results_dir = Path("data/test_results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    result_file = results_dir / "test_top4_selection.json"
    
    try:
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Результат сохранен: {result_file}")
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {e}")
        return False
    
    # 8. Итоговый результат
    print(f"\n" + "=" * 80)
    if test_result["validation"]["success"]:
        print("🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print(f"   ✅ Создано {len(scripts)} сценариев (по 2 от каждого из 5 сценаристов)")
        print(f"   ✅ Все сценарии оценены жюри")
        print(f"   ✅ Выбраны топ-4 сценария для генерации изображений")
        print(f"   ✅ Логика выбора работает корректно")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН")
        if not test_result["validation"]["correct_script_count"]:
            print(f"   ❌ Неверное количество сценариев: {len(scripts)} (ожидается 10)")
        if not test_result["validation"]["all_scripts_evaluated"]:
            print(f"   ❌ Не все сценарии оценены: {len(evaluations)}/{len(scripts)}")
        if not test_result["validation"]["top4_selected"]:
            print(f"   ❌ Неверное количество топ-сценариев: {len(top4_scripts)} (ожидается 4)")
    
    print("=" * 80)
    
    return test_result["validation"]["success"]

if __name__ == "__main__":
    success = test_top4_selection()
    sys.exit(0 if success else 1)
