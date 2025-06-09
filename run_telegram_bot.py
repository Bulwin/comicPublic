"""
Скрипт для запуска Telegram бота DailyComicBot.
"""

import sys
import os
from pathlib import Path

# Добавляем путь к проекту в sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from telegram_bot import main

if __name__ == "__main__":
    main()
