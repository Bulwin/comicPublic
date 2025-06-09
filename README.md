# 🎭 DailyComicBot

Автоматизированная система создания ежедневных комиксов на основе новостей с использованием ИИ.

## 🚀 Быстрый старт

### Локальный запуск
```bash
# 1. Настройте .env файл
cp .env.example .env
# Заполните реальными API ключами

# 2. Установите зависимости
pip install -r requirements.txt

# 3. Запустите полный сервер
python run_full_server.py

# Или только Telegram бота
python run_telegram_bot.py
```

### Docker запуск
```bash
# 1. Настройте .env файл
cp .env.example .env

# 2. Запустите через Docker Compose
docker-compose up -d

# 3. Проверьте логи
docker-compose logs -f
```

### Деплой на сервер
```bash
# Автоматический деплой на Ubuntu
./deploy.sh
```

## 📋 Основные файлы

### 🎯 Запуск
- `run_full_server.py` - полный сервер с планировщиком и Telegram ботом
- `run_telegram_bot.py` - только Telegram бот для ручного управления
- `telegram_bot.py` - код Telegram бота

### ⚙️ Конфигурация
- `.env.example` - шаблон конфигурации
- `config.py` - основная конфигурация
- `requirements.txt` - зависимости Python

### 🐳 Деплой
- `Dockerfile` - контейнеризация
- `docker-compose.yml` - оркестрация
- `dailycomicbot.service` - systemd сервис
- `deploy.sh` - автоматический деплой

### 📚 Документация
- `DEPLOYMENT_GUIDE.md` - руководство по деплою
- `HOSTING_READINESS_REPORT.md` - анализ готовности к хостингу

## 🏗️ Архитектура

```
DailyComicBot/
├── agents/              # ИИ агенты (менеджер, сценаристы, жюри)
├── tools/               # Инструменты (новости, изображения, публикация)
├── utils/               # Утилиты (логирование, API, планировщик)
├── data/                # Данные (новости, сценарии, изображения)
├── instructions/        # Инструкции для ИИ агентов
└── prompts/             # Промпты для ИИ
```

## 🔧 Workflow

1. **Сбор новостей** - Perplexity API
2. **Генерация сценариев** - OpenAI Assistants API (5 сценаристов)
3. **Оценка жюри** - OpenAI Assistants API (5 экспертов)
4. **Создание изображения** - DALL-E 3
5. **Публикация** - Telegram канал

## 🤖 Telegram бот

Интерактивное управление через Telegram:
- 🚀 Ручной запуск процесса
- 📰 Одобрение/перегенерация новости
- ✍️ Выбор лучшего сценария
- 🖼️ Выбор изображения
- 📤 Публикация в канал

## 📊 Мониторинг

### Логи
- `logs/` - логи приложения
- `journalctl -u dailycomicbot -f` - системные логи

### Управление (после деплоя)
```bash
dailycomicbot-ctl start|stop|restart|status|logs|update
backup-dailycomicbot
```

## 🔑 Требуемые API ключи

- **OpenAI API** - для GPT-4 и DALL-E
- **Perplexity API** - для сбора новостей
- **Telegram Bot Token** - для бота
- **Assistant IDs** - для сценаристов и жюри

## 📈 Системные требования

- **Python:** 3.9+
- **RAM:** 2GB+ (рекомендуется 4GB)
- **CPU:** 2 ядра
- **Диск:** 20GB+ SSD

## 🔒 Безопасность

- Все API ключи в переменных окружения
- `.env` исключен из git
- Systemd сервис с ограничениями
- Firewall и fail2ban настроены

## 📞 Поддержка

Подробная документация в `DEPLOYMENT_GUIDE.md`

---

**DailyComicBot** - создавайте комиксы автоматически! 🎉
