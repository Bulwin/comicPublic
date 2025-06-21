#!/usr/bin/env python3
"""
Запуск только планировщика задач DailyComicBot.
Без Telegram бота - только автоматические задачи.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.append(str(Path(__file__).resolve().parent))

# Импорт модулей проекта
from utils.scheduler import DailyComicBotScheduler
from utils import logger
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    """Основная функция для запуска только планировщика."""
    try:
        print("🚀 Запуск DailyComicBot Scheduler (ТОЛЬКО ПЛАНИРОВЩИК)")
        print("⏰ Автоматические задачи будут выполняться по расписанию")
        print("🛑 Нажмите Ctrl+C для остановки")
        print()
        
        # Создание и запуск планировщика
        scheduler = DailyComicBotScheduler()
        scheduler.start()
        
        print("✅ Планировщик запущен успешно")
        print("📅 Ожидание выполнения задач...")
        
        # Бесконечный цикл для поддержания работы планировщика
        try:
            while True:
                time.sleep(60)  # Проверяем каждую минуту
                
        except KeyboardInterrupt:
            print("\n🛑 Получен сигнал остановки...")
            scheduler.stop()
            print("✅ Планировщик остановлен")
            
    except Exception as e:
        print(f"❌ Ошибка при запуске планировщика: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
