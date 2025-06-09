# 🚀 Руководство по деплою DailyComicBot на хостинг

## ⚠️ КРИТИЧЕСКИ ВАЖНО - БЕЗОПАСНОСТЬ

### 🔴 НЕМЕДЛЕННЫЕ ДЕЙСТВИЯ ПЕРЕД ДЕПЛОЕМ

1. **Отзовите скомпрометированные API ключи:**
   - Зайдите в [OpenAI Dashboard](https://platform.openai.com/api-keys)
   - Удалите ключ `sk-proj-PTub7qZDw5xNMY10Gf7H...`
   - Зайдите в [Perplexity Dashboard](https://www.perplexity.ai/settings/api)
   - Удалите ключ `pplx-sEGUJbIEssk6KxtGTxqr...`

2. **Создайте новые API ключи:**
   - Создайте новый OpenAI API ключ
   - Создайте новый Perplexity API ключ
   - Создайте новых ассистентов в OpenAI (если нужно)

## 🎯 Варианты деплоя

### Вариант 1: Автоматический деплой (Рекомендуется)

```bash
# На сервере Ubuntu 22.04 LTS
git clone <your-repo> dailycomicbot
cd dailycomicbot
./deploy.sh
```

### Вариант 2: Docker деплой

```bash
# Клонирование репозитория
git clone <your-repo> dailycomicbot
cd dailycomicbot

# Настройка .env
cp .env.example .env
nano .env  # Заполните реальными значениями

# Запуск через Docker Compose
docker-compose up -d

# Проверка статуса
docker-compose logs -f
```

### Вариант 3: Ручной деплой

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3 python3-pip python3-venv git

# Создание пользователя
sudo useradd --create-home --shell /bin/bash dailycomicbot

# Клонирование и настройка
sudo mkdir -p /opt/dailycomicbot
sudo chown dailycomicbot:dailycomicbot /opt/dailycomicbot
sudo -u dailycomicbot git clone <your-repo> /opt/dailycomicbot
cd /opt/dailycomicbot

# Виртуальное окружение
sudo -u dailycomicbot python3 -m venv venv
sudo -u dailycomicbot ./venv/bin/pip install -r requirements.txt

# Настройка .env
sudo -u dailycomicbot cp .env.example .env
sudo -u dailycomicbot nano .env

# Systemd сервис
sudo cp dailycomicbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dailycomicbot
sudo systemctl start dailycomicbot
```

## 📋 Конфигурация .env файла

```env
# API ключи (ОБЯЗАТЕЛЬНО заполните новыми!)
OPENAI_API_KEY=sk-proj-ваш_новый_openai_ключ
PERPLEXITY_API_KEY=pplx-ваш_новый_perplexity_ключ

# Assistant ID (создайте новых или используйте существующих)
SCRIPTWRITER_A_ASSISTANT_ID=asst_ваш_assistant_id
SCRIPTWRITER_B_ASSISTANT_ID=asst_ваш_assistant_id
SCRIPTWRITER_C_ASSISTANT_ID=asst_ваш_assistant_id
SCRIPTWRITER_D_ASSISTANT_ID=asst_ваш_assistant_id
SCRIPTWRITER_E_ASSISTANT_ID=asst_ваш_assistant_id

JURY_A_ASSISTANT_ID=asst_ваш_jury_id
JURY_B_ASSISTANT_ID=asst_ваш_jury_id
JURY_C_ASSISTANT_ID=asst_ваш_jury_id
JURY_D_ASSISTANT_ID=asst_ваш_jury_id
JURY_E_ASSISTANT_ID=asst_ваш_jury_id

# Telegram настройки
TELEGRAM_BOT_TOKEN=ваш_telegram_bot_token
TELEGRAM_CHANNEL_ID=-1002433046352  # Ваш проверенный ID
TELEGRAM_ADMIN_CHAT_ID=ваш_admin_chat_id
PUBLISHER_BOT_TOKEN=ваш_publisher_bot_token

# Instagram (опционально)
INSTAGRAM_USERNAME=ваш_instagram_username
INSTAGRAM_PASSWORD=ваш_instagram_password

# Настройки времени
TIMEZONE=Europe/Nicosia
NEWS_COLLECTION_HOUR=13
NEWS_COLLECTION_MINUTE=0
PUBLICATION_TIME_HOUR=13
PUBLICATION_TIME_MINUTE=15
```

## 🖥️ Рекомендуемые VPS провайдеры

### 1. **DigitalOcean** (Простота)
- **Droplet:** Basic, 2GB RAM, 1 vCPU, 50GB SSD
- **Цена:** ~$12/месяц
- **Плюсы:** Простая настройка, хорошая документация
- **Минусы:** Дороже конкурентов

### 2. **Hetzner Cloud** (Цена/качество)
- **Сервер:** CX21, 4GB RAM, 2 vCPU, 40GB SSD
- **Цена:** ~€4.5/месяц
- **Плюсы:** Отличная цена, быстрые SSD
- **Минусы:** Европейские дата-центры

### 3. **Vultr** (Гибкость)
- **Instance:** Regular Performance, 2GB RAM, 1 vCPU, 55GB SSD
- **Цена:** ~$12/месяц
- **Плюсы:** Много локаций, почасовая оплата
- **Минусы:** Средняя производительность

### 4. **Contabo** (Бюджет)
- **VPS:** VPS S, 4GB RAM, 4 vCPU, 50GB SSD
- **Цена:** ~€5/месяц
- **Плюсы:** Очень дешево, много ресурсов
- **Минусы:** Переменная производительность

## 🔧 Команды управления

После деплоя доступны команды:

```bash
# Управление сервисом
dailycomicbot-ctl start     # Запуск
dailycomicbot-ctl stop      # Остановка
dailycomicbot-ctl restart   # Перезапуск
dailycomicbot-ctl status    # Статус
dailycomicbot-ctl logs      # Логи
dailycomicbot-ctl update    # Обновление

# Бэкап
backup-dailycomicbot        # Создание бэкапа

# Docker команды (если используете Docker)
docker-compose up -d        # Запуск
docker-compose down         # Остановка
docker-compose logs -f      # Логи
docker-compose restart      # Перезапуск
```

## 📊 Мониторинг

### Проверка статуса
```bash
# Статус сервиса
systemctl status dailycomicbot

# Логи в реальном времени
journalctl -u dailycomicbot -f

# Использование ресурсов
htop
```

### Важные файлы
```
/opt/dailycomicbot/          # Основная директория
├── .env                     # Конфигурация
├── logs/                    # Логи приложения
├── data/                    # Данные приложения
│   ├── images/              # Сгенерированные изображения
│   ├── news/                # Собранные новости
│   ├── jokes/               # Сценарии
│   └── history/             # История публикаций
└── venv/                    # Виртуальное окружение
```

## 🔒 Безопасность

### Firewall
```bash
# Проверка статуса
sudo ufw status

# Разрешенные порты
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Fail2ban
```bash
# Статус
sudo fail2ban-client status

# Статус SSH защиты
sudo fail2ban-client status sshd
```

### Обновления
```bash
# Автоматические обновления безопасности
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## 🚨 Устранение неполадок

### Проблема: Сервис не запускается
```bash
# Проверка логов
journalctl -u dailycomicbot -n 50

# Проверка конфигурации
sudo -u dailycomicbot /opt/dailycomicbot/venv/bin/python -c "from dotenv import load_dotenv; load_dotenv(); print('Config OK')"
```

### Проблема: API ошибки
```bash
# Проверка API ключей
grep -E "(OPENAI|PERPLEXITY)_API_KEY" /opt/dailycomicbot/.env

# Тест OpenAI подключения
sudo -u dailycomicbot /opt/dailycomicbot/venv/bin/python -c "
import openai
import os
from dotenv import load_dotenv
load_dotenv()
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
print('OpenAI connection OK')
"
```

### Проблема: Telegram бот не отвечает
```bash
# Проверка токена
curl -s "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# Проверка webhook
curl -s "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"
```

## 📈 Масштабирование

### Увеличение ресурсов
- **RAM:** Увеличьте до 4GB для стабильной работы
- **CPU:** 2 ядра достаточно для большинства нагрузок
- **Диск:** 50GB+ для хранения истории изображений

### Мониторинг производительности
```bash
# Использование памяти
free -h

# Использование диска
df -h

# Загрузка CPU
top
```

## 🔄 Обновления

### Автоматическое обновление
```bash
# Обновление кода и зависимостей
dailycomicbot-ctl update
```

### Ручное обновление
```bash
cd /opt/dailycomicbot
sudo systemctl stop dailycomicbot
sudo -u dailycomicbot git pull
sudo -u dailycomicbot ./venv/bin/pip install -r requirements.txt
sudo systemctl start dailycomicbot
```

## 📞 Поддержка

### Логи для диагностики
```bash
# Системные логи
journalctl -u dailycomicbot --since "1 hour ago"

# Логи приложения
tail -f /opt/dailycomicbot/logs/*.log

# Docker логи (если используете Docker)
docker-compose logs --tail=100
```

### Полезные команды
```bash
# Проверка всех процессов Python
ps aux | grep python

# Проверка сетевых подключений
netstat -tlnp | grep python

# Проверка использования диска
du -sh /opt/dailycomicbot/*
```

---

## ✅ Чеклист готовности к деплою

- [ ] ✅ Исправлен .env.example (убраны реальные ключи)
- [ ] ✅ Отозваны скомпрометированные API ключи
- [ ] ✅ Созданы новые API ключи
- [ ] ✅ Выбран VPS провайдер
- [ ] ✅ Настроен сервер Ubuntu 22.04 LTS
- [ ] ✅ Запущен скрипт деплоя
- [ ] ✅ Настроен .env файл с реальными значениями
- [ ] ✅ Протестирован запуск сервиса
- [ ] ✅ Проверена работа Telegram бота
- [ ] ✅ Настроен мониторинг и бэкапы

**После выполнения всех пунктов DailyComicBot готов к продакшену! 🎉**
