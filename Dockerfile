FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash dailycomicbot

# Установка рабочей директории
WORKDIR /app

# Копирование файла зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание необходимых директорий
RUN mkdir -p data/images data/news data/jokes data/evaluations data/history logs

# Установка прав доступа
RUN chown -R dailycomicbot:dailycomicbot /app

# Переключение на пользователя приложения
USER dailycomicbot

# Открытие порта (если потребуется веб-интерфейс)
EXPOSE 8000

# Команда запуска
CMD ["python", "run_full_server.py"]
