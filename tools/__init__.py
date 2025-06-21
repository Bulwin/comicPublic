"""
Пакет инструментов для проекта DailyComicBot.
Содержит модули для работы с новостями, изображениями, хранилищем данных и публикации в социальные сети.
"""

from tools.news_tools import get_top_news
from tools.image_tools import generate_comic_image
from tools.storage_tools import (
    store_data, load_data, store_daily_data, load_daily_data,
    list_history_files, save_image, get_image_path, store_news, load_news,
    store_scripts, load_scripts
)
from tools.publishing_tools import (
    post_to_telegram, post_to_instagram, publish_to_all_platforms, format_caption
)

__all__ = [
    # Инструменты для работы с новостями
    'get_top_news',
    
    # Инструменты для работы с изображениями
    'generate_comic_image',
    
    # Инструменты для работы с хранилищем данных
    'store_data', 'load_data', 'store_daily_data', 'load_daily_data',
    'list_history_files', 'save_image', 'get_image_path', 'store_news', 'load_news',
    
    # Инструменты для публикации в социальные сети
    'post_to_telegram', 'post_to_instagram', 'publish_to_all_platforms', 'format_caption'
]
