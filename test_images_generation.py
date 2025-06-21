#!/usr/bin/env python3
"""
Тестирование этапа генерации изображений с проверкой использования топ-4 сценариев.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).resolve().parent))

from agents.manager import ManagerAgent
from tools.news_tools import get_top_news
from tools.storage_tools import load_scripts, load_evaluations
from utils.logger import info, error, warning

def test_images_generation():
    """Тестирование генерации изображений и проверка использования топ-4."""
    
    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ ЭТАПА 3: ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ")
    print("="*80 + "\n")
    
    # Получаем новость
    print("🔄 Получение новости...")
    news = get_top_news(force_new=False)
    
    if not news:
        print("❌ ОШИБКА: Не удалось получить новость!")
        return False
    
    print(f"✅ Новость получена: {news['title'][:50]}...")
    
    # Создаем менеджера
    print("\n🤖 Инициализация менеджера комиксов...")
    manager = ManagerAgent()
    
    # Проверяем наличие сценариев
    print("\n📚 ПРОВЕРКА СУЩЕСТВУЮЩИХ СЦЕНАРИЕВ:")
    print("-" * 40)
    
    # Загружаем сценарии из файловой системы
    scripts = load_scripts()
    
    if not scripts:
        print("⚠️  Нет сохраненных сценариев, запускаем генерацию...")
        manager.news = news
        scripts = manager.generate_scripts()
        
        if not scripts:
            print("❌ ОШИБКА: Не удалось сгенерировать сценарии!")
            return False
    
    print(f"✅ Загружено сценариев: {len(scripts)}")
    
    # Проверяем наличие оценок
    print("\n⚖️  ПРОВЕРКА ОЦЕНОК:")
    print("-" * 40)
    
    evaluations = load_evaluations()
    
    if not evaluations:
        print("⚠️  Нет сохраненных оценок, запускаем оценку...")
        manager.scripts = scripts
        evaluations = manager.evaluate_scripts()
        
        if not evaluations:
            print("❌ ОШИБКА: Не удалось получить оценки!")
            return False
    
    print(f"✅ Загружено оценок: {len(evaluations)}")
    
    # Определяем топ-4 сценария
    print("\n🏆 ОПРЕДЕЛЕНИЕ ТОП-4 СЦЕНАРИЕВ:")
    print("-" * 40)
    
    sorted_scripts = sorted(
        evaluations.items(),
        key=lambda x: x[1]['average_score'],
        reverse=True
    )[:4]
    
    top_4_ids = []
    for i, (script_id, eval_data) in enumerate(sorted_scripts):
        top_4_ids.append(script_id)
        print(f"\n{i+1}. Сценарий {script_id}:")
        print(f"   Средний балл: {eval_data['average_score']:.1f}")
        print(f"   Автор: {eval_data.get('writer_name', 'Неизвестен')}")
        
        # Находим соответствующий сценарий
        script = next((s for s in scripts if s.get('script_id') == script_id), None)
        if script:
            print(f"   Заголовок: {script.get('title', 'Без заголовка')}")
    
    # Генерация изображений
    print("\n" + "="*80)
    print("🎨 ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ:")
    print("="*80 + "\n")
    
    print("📸 Запуск генерации изображений для топ-4 сценариев...")
    
    # Отслеживаем какие сценарии используются для генерации
    generated_images = []
    generation_log = []
    
    # Перехватываем вызовы генерации изображений
    original_generate_image = manager.generate_image
    
    def track_image_generation(script):
        """Обертка для отслеживания генерации изображений."""
        script_id = script.get('script_id', 'unknown')
        
        print(f"\n🎨 Генерация изображения для сценария: {script_id}")
        print(f"   Заголовок: {script.get('title', 'Без заголовка')}")
        print(f"   Автор: {script.get('writer_name', 'Неизвестен')}")
        
        # Проверяем, входит ли в топ-4
        is_top_4 = script_id in top_4_ids
        print(f"   В топ-4: {'✅ ДА' if is_top_4 else '❌ НЕТ'}")
        
        generation_log.append({
            'script_id': script_id,
            'title': script.get('title', 'Без заголовка'),
            'writer_name': script.get('writer_name', 'Неизвестен'),
            'is_top_4': is_top_4,
            'timestamp': datetime.now().isoformat()
        })
        
        # Вызываем оригинальную функцию
        result = original_generate_image(script)
        
        if result:
            generated_images.append({
                'script_id': script_id,
                'image_path': result,
                'is_top_4': is_top_4
            })
            print(f"   ✅ Изображение создано: {result}")
        else:
            print(f"   ❌ Не удалось создать изображение")
        
        return result
    
    # Подменяем функцию для отслеживания
    manager.generate_image = track_image_generation
    
    # Запускаем генерацию
    try:
        # Устанавливаем данные в менеджере
        manager.scripts = scripts
        manager.evaluations = evaluations
        
        # Получаем топ-4 сценарии
        top_scripts = manager.select_top_scripts(4)
        
        # Генерируем изображения для топ-4
        images = manager.create_images_for_top_scripts(top_scripts)
    finally:
        # Восстанавливаем оригинальную функцию
        manager.generate_image = original_generate_image
    
    # Анализ результатов
    print("\n" + "="*80)
    print("📊 АНАЛИЗ РЕЗУЛЬТАТОВ:")
    print("="*80 + "\n")
    
    print(f"📈 Статистика генерации:")
    print(f"- Всего попыток генерации: {len(generation_log)}")
    print(f"- Успешно сгенерировано: {len(generated_images)}")
    print(f"- Из топ-4: {sum(1 for img in generated_images if img['is_top_4'])}")
    print(f"- Не из топ-4: {sum(1 for img in generated_images if not img['is_top_4'])}")
    
    # Проверка корректности
    print("\n🔍 ПРОВЕРКА КОРРЕКТНОСТИ:")
    print("-" * 40)
    
    errors = []
    
    # Проверяем, что генерировались только топ-4
    for log_entry in generation_log:
        if not log_entry['is_top_4']:
            errors.append(f"Генерировалось изображение для сценария НЕ из топ-4: {log_entry['script_id']}")
    
    # Проверяем, что все топ-4 были сгенерированы
    generated_ids = [log['script_id'] for log in generation_log]
    for top_id in top_4_ids:
        if top_id not in generated_ids:
            errors.append(f"НЕ было сгенерировано изображение для топ-4 сценария: {top_id}")
    
    if errors:
        print("❌ ОБНАРУЖЕНЫ ОШИБКИ:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ Все изображения сгенерированы корректно!")
        print("✅ Использовались только топ-4 сценария!")
    
    # Сохранение результатов
    print("\n💾 СОХРАНЕНИЕ РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ:")
    print("-" * 40)
    
    test_file = Path("data/test_results/test_images_generation.json")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_data = {
        'timestamp': datetime.now().isoformat(),
        'news_title': news['title'],
        'top_4_scripts': [
            {
                'position': i+1,
                'script_id': script_id,
                'average_score': eval_data['average_score'],
                'writer_name': eval_data.get('writer_name', 'Неизвестен'),
                'title': next((s.get('title') for s in scripts if s.get('script_id') == script_id), 'Не найден')
            }
            for i, (script_id, eval_data) in enumerate(sorted_scripts)
        ],
        'generation_log': generation_log,
        'generated_images': generated_images,
        'validation': {
            'total_attempts': len(generation_log),
            'successful_generations': len(generated_images),
            'from_top_4': sum(1 for img in generated_images if img['is_top_4']),
            'not_from_top_4': sum(1 for img in generated_images if not img['is_top_4']),
            'errors': errors,
            'is_valid': len(errors) == 0
        }
    }
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Результаты сохранены в: {test_file}")
    
    # Итоговый результат
    print("\n" + "="*80)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print("="*80)
    
    if len(errors) == 0 and len(generated_images) == 4:
        print(f"\n✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print(f"✅ Все 4 изображения сгенерированы для топ-4 сценариев!")
    else:
        print(f"\n❌ ТЕСТ ПРОВАЛЕН!")
        if len(errors) > 0:
            print(f"   Обнаружено ошибок: {len(errors)}")
        if len(generated_images) != 4:
            print(f"   Сгенерировано изображений: {len(generated_images)} (ожидалось 4)")
    
    return len(errors) == 0 and len(generated_images) == 4

if __name__ == "__main__":
    try:
        success = test_images_generation()
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
