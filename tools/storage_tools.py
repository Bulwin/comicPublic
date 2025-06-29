"""
Модуль инструментов для работы с хранилищем данных.
Предоставляет функции для сохранения и загрузки данных в формате JSON.
"""

import json
import os
from datetime import datetime
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Импорт модулей проекта
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import logger, handle_exceptions, StorageError
from config import DATA_DIR, HISTORY_DIR, IMAGES_DIR, HISTORY_FILE_FORMAT


@handle_exceptions
def store_data(data: Dict[str, Any], filename: str, directory: Path = HISTORY_DIR) -> bool:
    """
    Сохранение данных в JSON-файл.
    
    Args:
        data (Dict[str, Any]): Данные для сохранения.
        filename (str): Имя файла.
        directory (Path, optional): Директория для сохранения. По умолчанию HISTORY_DIR.
        
    Returns:
        bool: True, если данные успешно сохранены, иначе False.
        
    Raises:
        StorageError: Если произошла ошибка при сохранении данных.
    """
    try:
        # Создание директории, если она не существует
        os.makedirs(directory, exist_ok=True)
        
        # Полный путь к файлу
        filepath = directory / filename
        
        # Сохранение данных в JSON-файл
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Данные успешно сохранены в файл {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в файл {filename}: {str(e)}")
        raise StorageError(f"Ошибка при сохранении данных: {str(e)}")


@handle_exceptions
def load_data(filename: str, directory: Path = HISTORY_DIR) -> Optional[Dict[str, Any]]:
    """
    Загрузка данных из JSON-файла.
    
    Args:
        filename (str): Имя файла.
        directory (Path, optional): Директория для загрузки. По умолчанию HISTORY_DIR.
        
    Returns:
        Optional[Dict[str, Any]]: Загруженные данные или None, если произошла ошибка.
        
    Raises:
        StorageError: Если произошла ошибка при загрузке данных.
    """
    try:
        # Полный путь к файлу
        filepath = directory / filename
        
        # Проверка существования файла
        if not os.path.exists(filepath):
            logger.warning(f"Файл {filepath} не существует")
            return None
        
        # Загрузка данных из JSON-файла
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Данные успешно загружены из файла {filepath}")
        return data
    
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных из файла {filename}: {str(e)}")
        raise StorageError(f"Ошибка при загрузке данных: {str(e)}")


@handle_exceptions
def store_news(news: Dict[str, Any], date: Optional[datetime] = None) -> bool:
    """
    Сохранение новости дня.
    
    Args:
        news (Dict[str, Any]): Данные новости.
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        bool: True, если новость успешно сохранена, иначе False.
    """
    # Если дата не указана, используем текущую
    if date is None:
        date = datetime.now()
    
    # Создание директории для новостей
    news_dir = Path(DATA_DIR) / "news"
    news_dir.mkdir(exist_ok=True, parents=True)
    
    # Формирование имени файла на основе даты
    filename = f"news_{date.strftime('%Y%m%d')}.json"
    
    # Сохранение новости
    return store_data(news, filename, news_dir)


@handle_exceptions
def load_news(date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """
    Загрузка новости дня.
    
    Args:
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        Optional[Dict[str, Any]]: Загруженная новость или None, если произошла ошибка.
    """
    # Если дата не указана, используем текущую
    if date is None:
        date = datetime.now()
    
    # Создание директории для новостей
    news_dir = Path(DATA_DIR) / "news"
    
    # Формирование имени файла на основе даты
    filename = f"news_{date.strftime('%Y%m%d')}.json"
    
    # Загрузка новости
    return load_data(filename, news_dir)


@handle_exceptions
def store_daily_data(data: Dict[str, Any], date: Optional[datetime] = None) -> bool:
    """
    Сохранение ежедневных данных.
    
    Args:
        data (Dict[str, Any]): Данные для сохранения.
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        bool: True, если данные успешно сохранены, иначе False.
    """
    # Если дата не указана, используем текущую
    if date is None:
        date = datetime.now()
    
    # Формирование имени файла на основе даты
    filename = date.strftime(HISTORY_FILE_FORMAT)
    
    # Сохранение данных
    return store_data(data, filename)


@handle_exceptions
def load_daily_data(date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """
    Загрузка ежедневных данных.
    
    Args:
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        Optional[Dict[str, Any]]: Загруженные данные или None, если произошла ошибка.
    """
    # Если дата не указана, используем текущую
    if date is None:
        date = datetime.now()
    
    # Формирование имени файла на основе даты
    filename = date.strftime(HISTORY_FILE_FORMAT)
    
    # Загрузка данных
    return load_data(filename)


@handle_exceptions
def list_history_files() -> List[str]:
    """
    Получение списка файлов истории.
    
    Returns:
        List[str]: Список имен файлов истории.
    """
    try:
        # Создание директории, если она не существует
        os.makedirs(HISTORY_DIR, exist_ok=True)
        
        # Получение списка файлов
        files = [f for f in os.listdir(HISTORY_DIR) if f.endswith('.json')]
        
        # Сортировка файлов по дате (от новых к старым)
        files.sort(reverse=True)
        
        return files
    
    except Exception as e:
        logger.error(f"Ошибка при получении списка файлов истории: {str(e)}")
        return []


@handle_exceptions
def save_image(image_data: Union[bytes, str], filename: str) -> str:
    """
    Сохранение изображения.
    
    Args:
        image_data (Union[bytes, str]): Данные изображения (байты или путь к файлу).
        filename (str): Имя файла.
        
    Returns:
        str: Путь к сохраненному изображению.
        
    Raises:
        StorageError: Если произошла ошибка при сохранении изображения.
    """
    try:
        # Создание директории, если она не существует
        os.makedirs(IMAGES_DIR, exist_ok=True)
        
        # Полный путь к файлу
        filepath = IMAGES_DIR / filename
        
        # Если image_data - строка (путь к файлу), копируем файл
        if isinstance(image_data, str):
            import shutil
            shutil.copy(image_data, filepath)
        
        # Если image_data - байты, сохраняем их в файл
        else:
            with open(filepath, 'wb') as f:
                f.write(image_data)
        
        logger.info(f"Изображение успешно сохранено в файл {filepath}")
        return str(filepath)
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении изображения в файл {filename}: {str(e)}")
        raise StorageError(f"Ошибка при сохранении изображения: {str(e)}")


@handle_exceptions
def get_image_path(filename: str) -> Optional[str]:
    """
    Получение пути к изображению.
    
    Args:
        filename (str): Имя файла.
        
    Returns:
        Optional[str]: Путь к изображению или None, если файл не существует.
    """
    # Полный путь к файлу
    filepath = IMAGES_DIR / filename
    
    # Проверка существования файла
    if not os.path.exists(filepath):
        logger.warning(f"Изображение {filepath} не существует")
        return None
    
    return str(filepath)


@handle_exceptions
def store_evaluation(evaluation: Dict[str, Any], script_id: str) -> bool:
    """
    Сохранение оценки сценария в файл.
    
    Args:
        evaluation (Dict[str, Any]): Оценка сценария.
        script_id (str): Идентификатор сценария.
        
    Returns:
        bool: True, если оценка успешно сохранена, иначе False.
    """
    try:
        # Создание директории для сохранения оценок
        evaluations_dir = Path(DATA_DIR) / "evaluations"
        evaluations_dir.mkdir(exist_ok=True, parents=True)
        
        # Получение текущей даты
        today = datetime.now().strftime('%Y%m%d')
        
        # Формирование имени файла
        jury_type = evaluation.get("jury_type", "unknown")
        filename = f"evaluation_{today}_{script_id}_{jury_type}.json"
        
        # Полный путь к файлу
        filepath = evaluations_dir / filename
        
        # Сохранение оценки в файл
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evaluation, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Оценка успешно сохранена в файл {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении оценки: {str(e)}")
        return False


@handle_exceptions
def load_evaluations(script_id: str, date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Загрузка оценок сценария из файлов.
    
    Args:
        script_id (str): Идентификатор сценария.
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        List[Dict[str, Any]]: Список оценок сценария.
    """
    try:
        # Создание директории для сохранения оценок
        evaluations_dir = Path(DATA_DIR) / "evaluations"
        evaluations_dir.mkdir(exist_ok=True, parents=True)
        
        # Получение даты
        if date is None:
            date = datetime.now()
        
        # Формирование шаблона имени файла
        date_str = date.strftime('%Y%m%d')
        pattern = f"evaluation_{date_str}_{script_id}_*.json"
        
        # Поиск файлов по шаблону
        evaluations = []
        for filepath in evaluations_dir.glob(pattern):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    evaluation = json.load(f)
                    evaluations.append(evaluation)
            except Exception as e:
                logger.error(f"Ошибка при загрузке оценки из файла {filepath}: {str(e)}")
        
        logger.info(f"Загружено {len(evaluations)} оценок для сценария {script_id}")
        return evaluations
    
    except Exception as e:
        logger.error(f"Ошибка при загрузке оценок: {str(e)}")
        return []


# Функция для обрезания длинных строк
def truncate_text(text, max_length=100):
    """
    Обрезание длинного текста до указанной длины.
    
    Args:
        text (str): Текст для обрезания.
        max_length (int, optional): Максимальная длина текста. По умолчанию 100.
        
    Returns:
        str: Обрезанный текст.
    """
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text


@handle_exceptions
def store_script(script: Dict[str, Any], date: Optional[datetime] = None) -> bool:
    """
    Сохранение одного сценария в файл.
    
    Args:
        script (Dict[str, Any]): Сценарий для сохранения.
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        bool: True, если сценарий успешно сохранен, иначе False.
    """
    try:
        # Загружаем существующие сценарии
        existing_scripts = load_scripts(date)
        
        # Добавляем новый сценарий
        existing_scripts.append(script)
        
        # Сохраняем обновленный список
        return store_scripts(existing_scripts, date)
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении сценария: {str(e)}")
        return False


@handle_exceptions
def store_scripts(scripts: List[Dict[str, Any]], date: Optional[datetime] = None) -> bool:
    """
    Сохранение сценариев в файл.
    
    Args:
        scripts (List[Dict[str, Any]]): Список сценариев.
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        bool: True, если сценарии успешно сохранены, иначе False.
    """
    try:
        # Создание директории для сохранения сценариев
        jokes_dir = Path(DATA_DIR) / "jokes"
        jokes_dir.mkdir(exist_ok=True, parents=True)
        
        # Получение даты
        if date is None:
            date = datetime.now()
        
        # Формирование имени файла
        date_str = date.strftime('%Y%m%d')
        filename = f"jokes_{date_str}.json"
        
        # Полный путь к файлу
        filepath = jokes_dir / filename
        
        # Подготовка данных для сохранения
        data = {
            "date": date.isoformat(),
            "scripts": scripts,
            "total_scripts": len(scripts)
        }
        
        # Сохранение сценариев в файл
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Сценарии успешно сохранены в файл {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении сценариев: {str(e)}")
        return False


@handle_exceptions
def load_scripts(date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Загрузка сценариев из файла.
    
    Args:
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        List[Dict[str, Any]]: Список сценариев.
    """
    try:
        # Создание директории для сохранения сценариев
        jokes_dir = Path(DATA_DIR) / "jokes"
        jokes_dir.mkdir(exist_ok=True, parents=True)
        
        # Получение даты
        if date is None:
            date = datetime.now()
        
        # Формирование имени файла
        date_str = date.strftime('%Y%m%d')
        filename = f"jokes_{date_str}.json"
        
        # Полный путь к файлу
        filepath = jokes_dir / filename
        
        # Проверка существования файла
        if not filepath.exists():
            logger.warning(f"Файл со сценариями {filepath} не существует")
            return []
        
        # Загрузка сценариев из файла
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        scripts = data.get("scripts", [])
        logger.info(f"Загружено {len(scripts)} сценариев из файла {filepath}")
        return scripts
    
    except Exception as e:
        logger.error(f"Ошибка при загрузке сценариев: {str(e)}")
        return []


@handle_exceptions
def store_all_evaluations(scripts: List[Dict[str, Any]], evaluations: Dict[str, Dict[str, Any]], date: Optional[datetime] = None) -> bool:
    """
    Сохранение всех шуток и их оценок в один файл.
    
    Args:
        scripts (List[Dict[str, Any]]): Список сценариев.
        evaluations (Dict[str, Dict[str, Any]]): Словарь с оценками сценариев.
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        bool: True, если данные успешно сохранены, иначе False.
    """
    try:
        # Создание директории для сохранения оценок
        evaluations_dir = Path(DATA_DIR) / "evaluations"
        evaluations_dir.mkdir(exist_ok=True, parents=True)
        
        # Получение даты
        if date is None:
            date = datetime.now()
        
        # Формирование имени файла
        date_str = date.strftime('%Y%m%d')
        filename = f"all_evaluations_{date_str}.md"
        
        # Полный путь к файлу
        filepath = evaluations_dir / filename
        
        # Формирование содержимого файла
        content = f"# Оценки шуток от {date.strftime('%d.%m.%Y')}\n\n"
        
        # Добавление информации о каждом сценарии и его оценках
        for i, script in enumerate(scripts):
            script_id = script.get("script_id", f"script_{i+1}")
            
            # Проверка наличия оценок для данного сценария
            if script_id not in evaluations:
                continue
            
            # Обрезаем заголовок, если он слишком длинный
            title = script.get('title', 'Без заголовка')
            title_truncated = truncate_text(title, 100)
            
            # Добавление заголовка сценария
            is_winner = evaluations[script_id].get("winner", False)
            winner_text = " - ПОБЕДИТЕЛЬ" if is_winner else ""
            content += f"## Шутка {i+1}: {title_truncated} ({script.get('writer_name', 'Неизвестный автор')}){winner_text}\n\n"
            
            # Добавление содержания шутки
            content += "### Содержание шутки:\n"
            content += f"**Заголовок:** {title_truncated}  \n"
            content += f"**Автор:** {script.get('writer_name', 'Неизвестный автор')}  \n"
            
            # Обрезаем описание, если оно слишком длинное
            description = script.get('description', 'Нет описания')
            description_truncated = truncate_text(description, 200)
            content += f"**Описание:** {description_truncated}\n\n"
            
            # Добавление панелей
            for j, panel in enumerate(script.get('panels', [])):
                content += f"**Панель {j+1}:**  \n"
                
                # Обрезаем описание панели, если оно слишком длинное
                panel_description = panel.get('description', 'Нет описания')
                panel_description_truncated = truncate_text(panel_description, 100)
                content += f"Описание: {panel_description_truncated}  \n"
                
                # Добавление диалогов
                if panel.get('dialog'):
                    content += "Диалоги:  \n"
                    for dialog in panel['dialog']:
                        character = dialog.get('character', '')
                        text = dialog.get('text', '')
                        note = dialog.get('note', '')
                        
                        # Обрезаем текст диалога, если он слишком длинный
                        character_truncated = truncate_text(character, 50)
                        text_truncated = truncate_text(text, 100)
                        note_truncated = truncate_text(note, 50) if note else ''
                        
                        if note_truncated:
                            content += f"- {character_truncated} ({note_truncated}): \"{text_truncated}\"  \n"
                        else:
                            content += f"- {character_truncated}: \"{text_truncated}\"  \n"
                
                # Добавление текста от автора
                if panel.get('narration'):
                    narration = panel['narration']
                    narration_truncated = truncate_text(narration, 100)
                    content += f"Текст от автора: {narration_truncated}  \n"
                
                content += "\n"
            
            # Добавление подписи
            caption = script.get('caption', 'Нет подписи')
            caption_truncated = truncate_text(caption, 100)
            content += f"**Подпись:** {caption_truncated}\n\n"
            
            # Добавление оценок
            content += "### Оценки:\n\n"
            
            # Добавление оценок от каждого жюри
            script_evaluations = evaluations[script_id].get("evaluations", {})
            for jury_type, evaluation in script_evaluations.items():
                jury_name = {
                    "A": "Добряк Петрович",
                    "B": "Мрачный Эдгар",
                    "C": "Бунтарь Макс",
                    "D": "Хипстер Артемий",
                    "E": "Филолог Вербицкий"
                }.get(jury_type, f"Жюри {jury_type}")
                
                content += f"**Оценка от жюри {jury_type} ({jury_name}):** {evaluation.get('total_score', 0)}/100\n\n"
            
            # Добавление средней оценки
            content += f"**Средняя оценка:** {evaluations[script_id].get('average_score', 0):.1f}/100\n\n"
            
            # Добавление разделителя между сценариями
            content += "---\n\n"
        
        # Сохранение содержимого в файл
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Все оценки успешно сохранены в файл {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении всех оценок: {str(e)}")
        return False


# ===== НОВЫЕ ФУНКЦИИ ДЛЯ АНЕКДОТОВ (НЕ ИЗМЕНЯЮТ СУЩЕСТВУЮЩИЙ ФУНКЦИОНАЛ) =====

@handle_exceptions
def store_joke(joke: Dict[str, Any], date: Optional[datetime] = None) -> bool:
    """
    Сохранение одного анекдота в файл.
    
    Args:
        joke (Dict[str, Any]): Анекдот для сохранения.
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        bool: True, если анекдот успешно сохранен, иначе False.
    """
    try:
        # Загружаем существующие анекдоты
        existing_jokes = load_jokes(date)
        
        # Добавляем новый анекдот
        existing_jokes.append(joke)
        
        # Сохраняем обновленный список
        return store_jokes(existing_jokes, date)
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении анекдота: {str(e)}")
        return False


@handle_exceptions
def store_jokes(jokes: List[Dict[str, Any]], date: Optional[datetime] = None) -> bool:
    """
    Сохранение анекдотов в файл.
    
    Args:
        jokes (List[Dict[str, Any]]): Список анекдотов.
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        bool: True, если анекдоты успешно сохранены, иначе False.
    """
    try:
        # Создание директории для сохранения анекдотов
        jokes_dir = Path(DATA_DIR) / "jokes"
        jokes_dir.mkdir(exist_ok=True, parents=True)
        
        # Получение даты
        if date is None:
            date = datetime.now()
        
        # Формирование имени файла
        date_str = date.strftime('%Y%m%d')
        filename = f"jokes_{date_str}.json"
        
        # Полный путь к файлу
        filepath = jokes_dir / filename
        
        # Подготовка данных для сохранения
        data = {
            "date": date.isoformat(),
            "jokes": jokes,
            "total_jokes": len(jokes)
        }
        
        # Сохранение анекдотов в файл
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Анекдоты успешно сохранены в файл {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении анекдотов: {str(e)}")
        return False


@handle_exceptions
def load_jokes(date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Загрузка анекдотов из файла.
    
    Args:
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        List[Dict[str, Any]]: Список анекдотов.
    """
    try:
        # Создание директории для сохранения анекдотов
        jokes_dir = Path(DATA_DIR) / "jokes"
        jokes_dir.mkdir(exist_ok=True, parents=True)
        
        # Получение даты
        if date is None:
            date = datetime.now()
        
        # Формирование имени файла
        date_str = date.strftime('%Y%m%d')
        filename = f"jokes_{date_str}.json"
        
        # Полный путь к файлу
        filepath = jokes_dir / filename
        
        # Проверка существования файла
        if not filepath.exists():
            logger.warning(f"Файл с анекдотами {filepath} не существует")
            return []
        
        # Загрузка анекдотов из файла
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        jokes = data.get("jokes", [])
        logger.info(f"Загружено {len(jokes)} анекдотов из файла {filepath}")
        return jokes
    
    except Exception as e:
        logger.error(f"Ошибка при загрузке анекдотов: {str(e)}")
        return []


@handle_exceptions
def store_joke_publication(publication_data: Dict[str, Any], date: Optional[datetime] = None) -> bool:
    """
    Сохранение данных о публикации анекдота.
    
    Args:
        publication_data (Dict[str, Any]): Данные о публикации анекдота.
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        bool: True, если данные успешно сохранены, иначе False.
    """
    try:
        # Создание директории для сохранения публикаций
        publications_dir = Path(DATA_DIR) / "joke_publications"
        publications_dir.mkdir(exist_ok=True, parents=True)
        
        # Получение даты
        if date is None:
            date = datetime.now()
        
        # Формирование имени файла
        date_str = date.strftime('%Y%m%d')
        filename = f"joke_publication_{date_str}.json"
        
        # Полный путь к файлу
        filepath = publications_dir / filename
        
        # Добавление временной метки
        publication_data["saved_at"] = datetime.now().isoformat()
        
        # Сохранение данных о публикации в файл
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(publication_data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Данные о публикации анекдота успешно сохранены в файл {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных о публикации анекдота: {str(e)}")
        return False


@handle_exceptions
def load_joke_publication(date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """
    Загрузка данных о публикации анекдота.
    
    Args:
        date (Optional[datetime], optional): Дата. По умолчанию None (текущая дата).
        
    Returns:
        Optional[Dict[str, Any]]: Данные о публикации или None, если файл не найден.
    """
    try:
        # Создание директории для сохранения публикаций
        publications_dir = Path(DATA_DIR) / "joke_publications"
        publications_dir.mkdir(exist_ok=True, parents=True)
        
        # Получение даты
        if date is None:
            date = datetime.now()
        
        # Формирование имени файла
        date_str = date.strftime('%Y%m%d')
        filename = f"joke_publication_{date_str}.json"
        
        # Полный путь к файлу
        filepath = publications_dir / filename
        
        # Проверка существования файла
        if not filepath.exists():
            logger.warning(f"Файл с данными о публикации анекдота {filepath} не существует")
            return None
        
        # Загрузка данных из файла
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Данные о публикации анекдота загружены из файла {filepath}")
        return data
    
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных о публикации анекдота: {str(e)}")
        return None
