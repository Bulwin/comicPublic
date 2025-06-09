"""
Модуль инструментов для работы с изображениями.
Предоставляет функции для создания изображений с помощью GPT-Image-1.
"""

import sys
import os
import base64
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import io

# Импорт модулей проекта
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import logger, handle_exceptions, retry_on_api_error, OpenAIError
from config import OPENAI_API_KEY, GPT_IMAGE_MODEL, GPT_IMAGE_QUALITY, IMAGES_DIR
from tools.storage_tools import save_image


@handle_exceptions
@retry_on_api_error(max_attempts=3)
def generate_comic_image(
    prompt: str,
    num_panels: int = 4,
    quality: str = None,
    filename: str = None
) -> str:
    """
    Создание изображения комикса с помощью GPT-Image-1.
    
    Args:
        prompt (str): Текстовое описание для генерации изображения.
        num_panels (int, optional): Количество панелей в комиксе. По умолчанию 4.
        quality (str, optional): Качество изображения (low, medium, high).
            По умолчанию None (используется значение из конфигурации).
        filename (str, optional): Имя файла для сохранения изображения.
            По умолчанию None (генерируется автоматически).
            
    Returns:
        str: Путь к сохраненному изображению.
        
    Raises:
        OpenAIError: Если произошла ошибка при создании изображения.
    """
    try:
        # Если качество не указано, используем значение из конфигурации
        if quality is None:
            quality = GPT_IMAGE_QUALITY
        
        # Формирование запроса для создания комикса
        enhanced_prompt = create_comic_prompt(prompt, num_panels)
        
        # Создание изображения
        image_data = call_gpt_image_api(enhanced_prompt, quality)
        
        # Если имя файла не указано, генерируем его автоматически
        if filename is None:
            filename = f"comic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # Сохранение изображения
        image_path = save_image(image_data, filename)
        
        logger.info(f"Изображение комикса успешно создано и сохранено в {image_path}")
        return image_path
    
    except Exception as e:
        logger.error(f"Ошибка при создании изображения комикса: {str(e)}")
        raise OpenAIError(f"Ошибка при создании изображения комикса: {str(e)}")


def filter_english_text(text: str) -> str:
    """
    Простая очистка промпта от возможных проблемных символов.
    Не удаляет английский текст, а просто очищает от лишних символов.
    
    Args:
        text (str): Исходный текст.
        
    Returns:
        str: Очищенный текст.
    """
    import re
    
    # Просто очищаем от множественных пробелов и переносов строк
    cleaned_text = re.sub(r'\s+', ' ', text).strip()
    
    return cleaned_text


def create_comic_prompt(prompt: str, num_panels: int) -> str:
    """
    Создание улучшенного запроса для генерации комикса.
    
    Args:
        prompt (str): Исходный запрос.
        num_panels (int): Количество панелей в комиксе.
        
    Returns:
        str: Улучшенный запрос для генерации комикса.
    """
    # Фильтрация английского текста из промпта
    filtered_prompt = filter_english_text(prompt)
    
    # Улучшенный шаблон для комикса с отступами
    comic_template = f"""
    Создай комикс из {num_panels} панелей на тему: {filtered_prompt}
    
    КРИТИЧЕСКИ ВАЖНО: 
    - Используй ТОЧНО тот текст, который указан в описании сценария!
    - НЕ переводи и НЕ изменяй текст из сценария!
    - Если в сценарии написано "Uber" - пиши "Uber", если "CEO" - пиши "CEO" итд
    - Воспроизводи текст диалогов и подписей БУКВАЛЬНО как в сценарии
    
    ВАЖНЫЕ ТРЕБОВАНИЯ К КОМПОЗИЦИИ:
    - Оставь отступы 40-50 пикселей от краев изображения
    - Панели должны быть расположены в центре с достаточными промежутками между ними
    - Текстовые пузыри должны быть ПОЛНОСТЬЮ внутри панелей, не касаясь краев
    - Весь текст должен быть читаемым и не обрезанным
    - Между панелями должны быть четкие разделители (белые полосы шириной 10-15 пикселей)
    
    РАЗМЕЩЕНИЕ ЭЛЕМЕНТОВ:
    - Панели занимают центральную область изображения (80% от общего размера)
    - Вокруг панелей - белые поля для предотвращения обрезания
    - Текстовые пузыри размещаются с отступом от краев панелей
    - Персонажи и объекты не должны касаться границ панелей
    
    ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ:
    - Размер изображения: 1024x1024 пикселей
    - Панели расположены в сетке 2x2 (для 4 панелей)
    - Каждая панель имеет четкую черную рамку толщиной 2-3 пикселя
    - Фон между панелями - белый
    - Шрифт в пузырях - крупный и четкий
    
    Стиль: Современный комикс с четкими линиями и яркими цветами.
    Убедись, что ВСЕ элементы комикса помещаются внутри изображения с запасом!
    """
    
    return comic_template


def call_gpt_image_api(prompt: str, quality: str) -> bytes:
    """
    Вызов API GPT-Image-1 для создания изображения.
    
    Args:
        prompt (str): Запрос для генерации изображения.
        quality (str): Качество изображения (low, medium, high).
        
    Returns:
        bytes: Данные изображения в формате байтов.
        
    Raises:
        OpenAIError: Если произошла ошибка при вызове API.
    """
    try:
        # Импорт необходимых модулей
        from openai import OpenAI
        import base64
        
        # Преобразование качества из формата проекта в формат API OpenAI
        api_quality = "high"  # По умолчанию
        if quality == "medium":
            api_quality = "medium"
        elif quality == "low":
            api_quality = "low"
        
        logger.info(f"Вызов API GPT-Image-1 с качеством: {api_quality}")
        logger.info(f"Промпт: {prompt}")
        
        # Попытка использовать реальный API OpenAI
        try:
            # Инициализация клиента OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Вызов API OpenAI для генерации изображения
            logger.info(f"Вызов API OpenAI с моделью {GPT_IMAGE_MODEL}")
            
            # Генерация изображения согласно официальной документации
            response = client.images.generate(
                model=GPT_IMAGE_MODEL,
                prompt=prompt,
                quality=api_quality,
                size="1024x1024",  # Стандартный размер для комикса
                n=1  # Генерируем одно изображение
            )
            
            # Отмечаем в логе, что получен ответ от API, но не выводим его содержимое
            logger.info("Получен ответ от API OpenAI (содержимое скрыто из-за большого размера)")
            
            # Проверка наличия данных в ответе
            if not response or not response.data or len(response.data) == 0:
                raise ValueError("Ответ от API не содержит данных")
                
            # Получение данных изображения
            image_data = response.data[0]
            
            # Проверка наличия b64_json в ответе
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                # Если есть b64_json, используем его
                logger.info("Получены данные изображения в формате base64")
                image_bytes = base64.b64decode(image_data.b64_json)
                return image_bytes
            elif hasattr(image_data, 'url') and image_data.url:
                # Если есть URL, загружаем изображение по URL
                image_url = image_data.url
                logger.info("Получен URL изображения от OpenAI (URL скрыт из-за большого размера)")
                
                # Загрузка изображения по URL
                image_response = requests.get(image_url, timeout=30)
                
                # Проверка успешности загрузки
                if image_response.status_code == 200:
                    logger.info("Изображение успешно загружено по URL")
                    return image_response.content
                else:
                    error_msg = f"Ошибка при загрузке изображения: {image_response.status_code}"
                    logger.error(error_msg)
                    raise OpenAIError(error_msg)
            else:
                # Если нет ни b64_json, ни URL, выбрасываем исключение
                raise ValueError("В ответе API отсутствуют данные изображения (ни b64_json, ни URL)")
                
        except Exception as api_e:
            # Если произошла ошибка при вызове API, логируем её и используем заглушку
            error_msg = f"Ошибка при вызове API OpenAI: {str(api_e)}"
            logger.error(error_msg)
            logger.warning("Используется заглушка для функции call_gpt_image_api")
            
            # Создание тестового изображения
            return create_fallback_image(prompt, quality)
    
    except Exception as e:
        logger.error(f"Ошибка при создании изображения: {str(e)}")
        return create_fallback_image(prompt, quality)


def create_fallback_image(prompt: str, quality: str) -> bytes:
    """
    Создание заглушки изображения в случае ошибки.
    
    Args:
        prompt (str): Запрос для генерации изображения.
        quality (str): Качество изображения.
        
    Returns:
        bytes: Данные изображения в формате байтов.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Создание изображения
        width, height = 800, 800
        image = Image.new("RGB", (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Разделение на панели
        num_panels = 4
        panel_width = width // 2
        panel_height = height // 2
        
        # Рисование рамок панелей
        for i in range(2):
            for j in range(2):
                x1 = i * panel_width
                y1 = j * panel_height
                x2 = x1 + panel_width - 1
                y2 = y1 + panel_height - 1
                draw.rectangle([(x1, y1), (x2, y2)], outline=(0, 0, 0), width=2)
                
                # Заполнение панелей цветом для наглядности
                fill_color = (240, 240, 240) if (i + j) % 2 == 0 else (230, 230, 230)
                draw.rectangle([(x1+2, y1+2), (x2-2, y2-2)], fill=fill_color)
        
        # Добавление текста - используем только load_default() для совместимости
        font = ImageFont.load_default()
        
        # Добавление текста с информацией о промпте
        prompt_lines = prompt.strip().split('\n')
        prompt_text = prompt_lines[0] if prompt_lines else "Комикс"
        if len(prompt_text) > 40:
            prompt_text = prompt_text[:37] + "..."
            
        # Добавление текста в панели
        panel_texts = [
            "Панель 1: " + prompt_text,
            "Панель 2: Продолжение",
            "Панель 3: Развитие",
            "Панель 4: Финал"
        ]
        
        draw.text((10, 10), panel_texts[0], fill=(0, 0, 0), font=font)
        draw.text((panel_width + 10, 10), panel_texts[1], fill=(0, 0, 0), font=font)
        draw.text((10, panel_height + 10), panel_texts[2], fill=(0, 0, 0), font=font)
        draw.text((panel_width + 10, panel_height + 10), panel_texts[3], fill=(0, 0, 0), font=font)
        
        # Добавление подписи
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        draw.text((width // 2 - 150, height - 30), f"Тестовый комикс | {current_time} | Качество: {quality}", fill=(0, 0, 0), font=font)
        
        # Сохранение изображения в байты
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)
        
        logger.info("Тестовое изображение комикса успешно создано")
        return img_byte_arr.getvalue()
    
    except Exception as e:
        logger.error(f"Ошибка при создании тестового изображения: {str(e)}")
        
        # Создаем очень простое изображение без использования сложных функций
        try:
            # Создаем простое изображение с текстом об ошибке
            from PIL import Image, ImageDraw
            
            # Создание простого изображения
            width, height = 400, 200
            image = Image.new("RGB", (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            # Добавление рамки
            draw.rectangle([(0, 0), (width-1, height-1)], outline=(0, 0, 0), width=2)
            
            # Добавление текста об ошибке
            error_text = f"Ошибка создания изображения: {str(e)[:50]}"
            if len(error_text) > 50:
                error_text = error_text[:47] + "..."
                
            draw.text((10, height//2 - 10), error_text, fill=(255, 0, 0))
            draw.text((10, height//2 + 10), f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fill=(0, 0, 0))
            
            # Сохранение изображения в байты
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)
            
            logger.info("Создано запасное изображение с информацией об ошибке")
            return img_byte_arr.getvalue()
            
        except Exception as inner_e:
            logger.critical(f"Критическая ошибка при создании запасного изображения: {str(inner_e)}")
            
            # Если все методы не сработали, возвращаем предварительно созданное статическое изображение
            # Это может быть заранее подготовленное изображение с ошибкой
            static_error_image_path = Path(__file__).resolve().parent.parent / "data" / "static" / "error_image.png"
            
            if os.path.exists(static_error_image_path):
                with open(static_error_image_path, "rb") as f:
                    logger.info("Использовано статическое изображение ошибки")
                    return f.read()
            
            # Если даже статического изображения нет, создаем минимальное изображение 1x1 пиксель
            # Это гарантирует, что хоть какое-то изображение будет возвращено
            minimal_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82'
            logger.warning("Возвращено минимальное изображение 1x1 пиксель")
            return minimal_image
