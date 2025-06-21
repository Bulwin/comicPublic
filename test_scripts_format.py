#!/usr/bin/env python3
"""
Тестирование этапа генерации сценариев с проверкой формата.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).resolve().parent))

from agents.manager import ManagerAgent
from tools.news_tools import get_top_news
from utils.logger import info, error, warning
from config import SCRIPTWRITERS

def validate_script_format(script, script_id):
    """Валидация формата сценария."""
    print(f"\n🔍 ПРОВЕРКА СЦЕНАРИЯ {script_id}:")
    print("-" * 40)
    
    errors = []
    warnings = []
    
    # Проверка обязательных полей
    required_fields = ['title', 'description', 'panels', 'caption', 'writer_type', 'writer_name']
    for field in required_fields:
        if field not in script:
            errors.append(f"Отсутствует обязательное поле: {field}")
            print(f"❌ Отсутствует поле: {field}")
        else:
            print(f"✅ Поле '{field}' присутствует")
    
    # Проверка заголовка
    if 'title' in script:
        title = script['title']
        print(f"\n📝 Заголовок: {title}")
        if not title or title == "Без заголовка":
            warnings.append("Заголовок пустой или стандартный")
            print("   ⚠️  Заголовок пустой или стандартный")
    
    # Проверка описания
    if 'description' in script:
        desc = script['description']
        print(f"\n📝 Описание: {desc[:100]}...")
        if not desc or desc == "Без описания":
            warnings.append("Описание пустое или стандартное")
            print("   ⚠️  Описание пустое или стандартное")
    
    # Проверка панелей
    if 'panels' in script:
        panels = script['panels']
        print(f"\n📊 Панели: {len(panels)} шт.")
        
        if len(panels) != 4:
            errors.append(f"Неверное количество панелей: {len(panels)} (должно быть 4)")
            print(f"   ❌ Неверное количество панелей: {len(panels)}")
        
        for i, panel in enumerate(panels):
            print(f"\n   Панель {i+1}:")
            
            # Проверка описания панели
            if 'description' not in panel:
                errors.append(f"Панель {i+1}: отсутствует описание")
                print(f"      ❌ Отсутствует описание")
            else:
                desc = panel['description']
                if not desc or desc == "[Описание панели отсутствует или не предоставлено]":
                    warnings.append(f"Панель {i+1}: описание пустое")
                    print(f"      ⚠️  Описание пустое или стандартное")
                else:
                    print(f"      ✅ Описание: {desc[:50]}...")
            
            # Проверка диалогов
            if 'dialog' in panel and panel['dialog']:
                print(f"      ✅ Диалоги: {len(panel['dialog'])} реплик")
                for dialog in panel['dialog']:
                    if not isinstance(dialog, dict) or 'character' not in dialog or 'text' not in dialog:
                        errors.append(f"Панель {i+1}: неверный формат диалога")
            
            # Проверка нарратива
            if 'narration' in panel and panel['narration']:
                print(f"      ✅ Текст от автора: {panel['narration'][:30]}...")
            
            # Проверка наличия контента
            has_dialog = bool(panel.get('dialog'))
            has_narration = bool(panel.get('narration'))
            has_description = bool(panel.get('description') and 
                                 panel['description'] != "[Описание панели отсутствует или не предоставлено]")
            
            if not has_dialog and not has_narration and not has_description:
                errors.append(f"Панель {i+1}: нет никакого контента")
                print(f"      ❌ Панель пустая - нет ни описания, ни диалогов, ни текста")
    
    # Проверка подписи
    if 'caption' in script:
        caption = script['caption']
        print(f"\n📝 Подпись: {caption}")
        if not caption or caption == "Без подписи":
            warnings.append("Подпись пустая или стандартная")
            print("   ⚠️  Подпись пустая или стандартная")
    
    # Проверка метаданных
    print(f"\n📋 Метаданные:")
    if 'writer_type' in script:
        print(f"   ✅ Тип сценариста: {script['writer_type']}")
    if 'writer_name' in script:
        print(f"   ✅ Имя сценариста: {script['writer_name']}")
    
    return {
        'script_id': script_id,
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }

def test_scripts_format():
    """Тестирование генерации сценариев и проверка формата."""
    
    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ ЭТАПА 2: ГЕНЕРАЦИЯ СЦЕНАРИЕВ")
    print("="*80 + "\n")
    
    # Получаем новость для генерации
    print("🔄 Получение новости для генерации сценариев...")
    news = get_top_news(force_new=False)  # Используем существующую новость
    
    if not news:
        print("❌ ОШИБКА: Не удалось получить новость!")
        return False
    
    print(f"✅ Новость получена: {news['title'][:50]}...")
    
    # Создаем менеджера
    print("\n🤖 Инициализация менеджера комиксов...")
    manager = ManagerAgent()
    
    # Генерируем сценарии
    print("\n🎭 ГЕНЕРАЦИЯ СЦЕНАРИЕВ:")
    print("-" * 40)
    print(f"Запуск генерации {len(SCRIPTWRITERS)} сценариев...")
    
    # Устанавливаем новость в менеджере
    manager.news = news
    scripts = manager.generate_scripts()
    
    if not scripts:
        print("❌ ОШИБКА: Не удалось сгенерировать сценарии!")
        return False
    
    print(f"\n✅ Сгенерировано сценариев: {len(scripts)}")
    
    # Проверяем формат каждого сценария
    print("\n" + "="*80)
    print("📋 ПРОВЕРКА ФОРМАТА СЦЕНАРИЕВ:")
    print("="*80)
    
    validation_results = []
    for i, script in enumerate(scripts):
        script_id = script.get('script_id', f'script_{i+1}')
        result = validate_script_format(script, script_id)
        validation_results.append(result)
    
    # Оценка сценариев
    print("\n" + "="*80)
    print("⚖️ ОЦЕНКА СЦЕНАРИЕВ ЖЮРИ:")
    print("="*80)
    
    print("\n🎯 Запуск оценки сценариев...")
    # Устанавливаем сценарии в менеджере
    manager.scripts = scripts
    evaluations = manager.evaluate_scripts()
    
    if evaluations:
        print(f"\n✅ Получено оценок: {len(evaluations)}")
        
        # Проверяем топ-4
        print("\n🏆 ТОП-4 СЦЕНАРИЯ:")
        print("-" * 40)
        
        sorted_scripts = sorted(
            evaluations.items(),
            key=lambda x: x[1]['average_score'],
            reverse=True
        )[:4]
        
        for i, (script_id, eval_data) in enumerate(sorted_scripts):
            print(f"\n{i+1}. Сценарий {script_id}:")
            print(f"   Средний балл: {eval_data['average_score']:.1f}")
            print(f"   Автор: {eval_data.get('writer_name', 'Неизвестен')}")
            
            # Находим соответствующий сценарий
            script = next((s for s in scripts if s.get('script_id') == script_id), None)
            if script:
                print(f"   Заголовок: {script.get('title', 'Без заголовка')}")
    
    # Сохранение результатов
    print("\n💾 СОХРАНЕНИЕ РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ:")
    print("-" * 40)
    
    test_file = Path("data/test_results/test_scripts_format.json")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Подготовка данных для сохранения
    test_data = {
        'timestamp': datetime.now().isoformat(),
        'news_title': news['title'],
        'scripts_count': len(scripts),
        'validation_results': validation_results,
        'top_4_scripts': [
            {
                'script_id': script_id,
                'average_score': eval_data['average_score'],
                'writer_name': eval_data.get('writer_name', 'Неизвестен'),
                'title': next((s.get('title') for s in scripts if s.get('script_id') == script_id), 'Не найден')
            }
            for script_id, eval_data in sorted_scripts
        ] if evaluations else [],
        'summary': {
            'total_scripts': len(scripts),
            'valid_scripts': sum(1 for r in validation_results if r['valid']),
            'scripts_with_errors': sum(1 for r in validation_results if not r['valid']),
            'scripts_with_warnings': sum(1 for r in validation_results if r['warnings'])
        }
    }
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Результаты сохранены в: {test_file}")
    
    # Сохранение полных сценариев для анализа
    scripts_file = Path("data/test_results/test_scripts_full.json")
    with open(scripts_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'scripts': scripts,
            'evaluations': evaluations
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Полные сценарии сохранены в: {scripts_file}")
    
    # Итоговый результат
    print("\n" + "="*80)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print("="*80)
    
    total_errors = sum(len(r['errors']) for r in validation_results)
    total_warnings = sum(len(r['warnings']) for r in validation_results)
    
    print(f"\n📈 Статистика:")
    print(f"- Всего сценариев: {len(scripts)}")
    print(f"- Валидных сценариев: {sum(1 for r in validation_results if r['valid'])}")
    print(f"- Сценариев с ошибками: {sum(1 for r in validation_results if not r['valid'])}")
    print(f"- Всего ошибок: {total_errors}")
    print(f"- Всего предупреждений: {total_warnings}")
    
    if total_errors == 0:
        print(f"\n✅ ВСЕ СЦЕНАРИИ ПРОШЛИ ВАЛИДАЦИЮ!")
    else:
        print(f"\n⚠️  ОБНАРУЖЕНЫ ОШИБКИ В ФОРМАТАХ!")
        for result in validation_results:
            if result['errors']:
                print(f"\n   Сценарий {result['script_id']}:")
                for error in result['errors']:
                    print(f"   - {error}")
    
    return total_errors == 0

if __name__ == "__main__":
    try:
        success = test_scripts_format()
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
