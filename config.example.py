"""
Конфигурационный файл для проекта DailyComicBot.
Содержит настройки API ключей, параметры подключения и другие конфигурационные параметры.
"""

import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Загрузка переменных окружения из .env файла
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
HISTORY_DIR = DATA_DIR / "history"
IMAGES_DIR = DATA_DIR / "images"

# Создание директорий, если они не существуют
for dir_path in [DATA_DIR, LOGS_DIR, HISTORY_DIR, IMAGES_DIR]:
    dir_path.mkdir(exist_ok=True, parents=True)

# API ключи
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# Параметры для Assistants API загружаются из переменных окружения
# SCRIPTWRITER_A_ASSISTANT_ID, SCRIPTWRITER_B_ASSISTANT_ID, и т.д.
# JURY_A_ASSISTANT_ID, JURY_B_ASSISTANT_ID, и т.д.

# Настройки OpenAI
OPENAI_MODEL = "gpt-4"  # Модель для агентов
GPT_IMAGE_MODEL = "gpt-image-1"  # Модель для генерации изображений
GPT_IMAGE_QUALITY = "high"  # Качество изображений (low, medium, high)

# Настройки публикации
PUBLICATION_TIME_HOUR = 13  # Час публикации (Cyprus time)
PUBLICATION_TIME_MINUTE = 15  # Минута публикации
NEWS_COLLECTION_HOUR = 13  # Час сбора новостей
NEWS_COLLECTION_MINUTE = 0  # Минута сбора новостей
TIMEZONE = "Europe/Nicosia"  # Часовой пояс Кипра

# Настройки Telegram
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
PUBLISHER_BOT_TOKEN = os.getenv("PUBLISHER_BOT_TOKEN")  # Токен бота для публикации в канал

# Настройки Instagram
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

# Настройки логирования
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / "daily_comic_bot.log"

# Настройки агентов
SCRIPTWRITERS = {
    "A": {
        "name": "Добряк Петрович",
        "description": "Добродушный пожилой юморист старой школы, создающий комиксы с классическим компанейским юмором, добрым, на уровне столовых анекдотов. Ценит шутки, понятные всем, избегает грубости и пошлости. Его девиз: 'Хороший юмор объединяет людей, а не разделяет их'."
    },
    "B": {
        "name": "Мрачный Эдгар",
        "description": "Меланхоличный интеллектуал с тягой к мрачным темам, создающий комиксы с черным юмором. Любит иронию, сарказм, неожиданные повороты и абсурдные ситуации. Балансирует на грани приличия, но никогда не переходит в откровенную жестокость. Его девиз: 'В самых темных темах можно найти свет юмора'."
    },
    "C": {
        "name": "Бунтарь Макс",
        "description": "Молодой провокатор, намеренно идущий против течения, создающий комиксы с юмором за гранью, с легкой нетерпимостью к меньшинствам, высмеиванием феминисток, веганов, ЛГБТ, БЛМ и прочих. Использует стереотипы и преувеличения, но избегает прямых оскорблений. Его девиз: 'Политкорректность убивает настоящий юмор'."
    },
    "D": {
        "name": "Хипстер Артемий",
        "description": "Модный городской интеллектуал в очках с толстой оправой, создающий комиксы с иронией, постиронией, абсурдом и сарказмом. Обожает многослойные шутки, отсылки к поп-культуре и метаюмор. Его комиксы требуют определенного уровня знаний для полного понимания. Его девиз: 'Если ты не понял шутку, возможно, она не для тебя'."
    },
    "E": {
        "name": "Филолог Вербицкий",
        "description": "Утонченный знаток языка с филологическим образованием, создающий комиксы с каламбурами и игрой слов. Мастерски использует многозначность слов, созвучия и лингвистические парадоксы. Его шутки интеллигентны и требуют хорошего знания языка. Его девиз: 'Игра слов - высшая форма языкового искусства'."
    }
}

# Настройки комикса
COMIC_PANELS = 4  # Количество панелей в комиксе

# Настройки хранения данных
HISTORY_FILE_FORMAT = "%Y-%m-%d.json"  # Формат имени файла истории (по дате)

# Настройки Assistants API
USE_ASSISTANTS_API = os.getenv("USE_ASSISTANTS_API", "True").lower() == "true"  # Использовать ли Assistants API вместо прямых вызовов OpenAI API
ASSISTANTS_API_TIMEOUT = 60  # Таймаут для запросов к Assistants API в секундах
ASSISTANTS_API_MAX_RETRIES = 3  # Максимальное количество попыток запроса к Assistants API

# Настройки времени для анекдотов
JOKE_PUBLICATION_HOUR = int(os.getenv("JOKE_PUBLICATION_HOUR", "14"))
JOKE_PUBLICATION_MINUTE = int(os.getenv("JOKE_PUBLICATION_MINUTE", "0"))
