#!/bin/bash

# Скрипт деплоя DailyComicBot на Ubuntu сервер
# Использование: ./deploy.sh

set -e  # Остановка при ошибке

echo "🚀 Начало деплоя DailyComicBot..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав root
if [[ $EUID -eq 0 ]]; then
   log_error "Не запускайте этот скрипт от root!"
   exit 1
fi

# Проверка операционной системы
if [[ ! -f /etc/os-release ]]; then
    log_error "Неподдерживаемая операционная система"
    exit 1
fi

source /etc/os-release
if [[ "$ID" != "ubuntu" ]]; then
    log_warn "Скрипт тестировался только на Ubuntu. Продолжить? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Обновление системы
log_info "Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
log_info "Установка системных зависимостей..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    nginx \
    ufw \
    fail2ban \
    htop \
    tree

# Создание пользователя для приложения
log_info "Создание пользователя dailycomicbot..."
if ! id "dailycomicbot" &>/dev/null; then
    sudo useradd --create-home --shell /bin/bash dailycomicbot
    log_info "Пользователь dailycomicbot создан"
else
    log_info "Пользователь dailycomicbot уже существует"
fi

# Создание директории приложения
log_info "Создание директории приложения..."
sudo mkdir -p /opt/dailycomicbot
sudo chown dailycomicbot:dailycomicbot /opt/dailycomicbot

# Копирование файлов приложения
log_info "Копирование файлов приложения..."
sudo -u dailycomicbot cp -r . /opt/dailycomicbot/
cd /opt/dailycomicbot

# Создание виртуального окружения
log_info "Создание виртуального окружения..."
sudo -u dailycomicbot python3 -m venv venv
sudo -u dailycomicbot ./venv/bin/pip install --upgrade pip

# Установка зависимостей Python
log_info "Установка зависимостей Python..."
sudo -u dailycomicbot ./venv/bin/pip install -r requirements.txt

# Создание необходимых директорий
log_info "Создание директорий для данных..."
sudo -u dailycomicbot mkdir -p data/{images,news,jokes,evaluations,history} logs

# Настройка .env файла
log_info "Настройка конфигурации..."
if [[ ! -f .env ]]; then
    sudo -u dailycomicbot cp .env.example .env
    log_warn "Файл .env создан из шаблона. ОБЯЗАТЕЛЬНО заполните его реальными значениями!"
    log_warn "Отредактируйте файл: sudo -u dailycomicbot nano /opt/dailycomicbot/.env"
else
    log_info "Файл .env уже существует"
fi

# Установка systemd сервиса
log_info "Установка systemd сервиса..."
sudo cp dailycomicbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dailycomicbot

# Настройка firewall
log_info "Настройка firewall..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Настройка fail2ban
log_info "Настройка fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Создание скрипта для управления
log_info "Создание скрипта управления..."
cat > /tmp/dailycomicbot-ctl << 'EOF'
#!/bin/bash

case "$1" in
    start)
        sudo systemctl start dailycomicbot
        echo "DailyComicBot запущен"
        ;;
    stop)
        sudo systemctl stop dailycomicbot
        echo "DailyComicBot остановлен"
        ;;
    restart)
        sudo systemctl restart dailycomicbot
        echo "DailyComicBot перезапущен"
        ;;
    status)
        sudo systemctl status dailycomicbot
        ;;
    logs)
        sudo journalctl -u dailycomicbot -f
        ;;
    update)
        cd /opt/dailycomicbot
        sudo systemctl stop dailycomicbot
        sudo -u dailycomicbot git pull
        sudo -u dailycomicbot ./venv/bin/pip install -r requirements.txt
        sudo systemctl start dailycomicbot
        echo "DailyComicBot обновлен"
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|update}"
        exit 1
        ;;
esac
EOF

sudo mv /tmp/dailycomicbot-ctl /usr/local/bin/
sudo chmod +x /usr/local/bin/dailycomicbot-ctl

# Создание скрипта бэкапа
log_info "Создание скрипта бэкапа..."
cat > /tmp/backup-dailycomicbot << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/backups/dailycomicbot"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="dailycomicbot_backup_$DATE.tar.gz"

mkdir -p "$BACKUP_DIR"

cd /opt/dailycomicbot
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude='venv' \
    --exclude='logs/*.log' \
    --exclude='.git' \
    .

echo "Бэкап создан: $BACKUP_DIR/$BACKUP_FILE"

# Удаление старых бэкапов (старше 7 дней)
find "$BACKUP_DIR" -name "dailycomicbot_backup_*.tar.gz" -mtime +7 -delete
EOF

sudo mv /tmp/backup-dailycomicbot /usr/local/bin/
sudo chmod +x /usr/local/bin/backup-dailycomicbot

# Добавление задачи бэкапа в cron
log_info "Настройка автоматических бэкапов..."
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-dailycomicbot") | crontab -

# Проверка конфигурации
log_info "Проверка конфигурации..."
if [[ -f /opt/dailycomicbot/.env ]]; then
    if grep -q "your_.*_here" /opt/dailycomicbot/.env; then
        log_error "В файле .env остались заглушки! Заполните реальными значениями."
        log_error "Отредактируйте: sudo -u dailycomicbot nano /opt/dailycomicbot/.env"
        ENV_CONFIGURED=false
    else
        log_info "Файл .env настроен"
        ENV_CONFIGURED=true
    fi
else
    log_error "Файл .env не найден!"
    ENV_CONFIGURED=false
fi

# Финальные инструкции
echo ""
log_info "🎉 Деплой завершен!"
echo ""
echo "📋 Следующие шаги:"
echo ""

if [[ "$ENV_CONFIGURED" == "false" ]]; then
    echo "1. 🔧 ОБЯЗАТЕЛЬНО настройте .env файл:"
    echo "   sudo -u dailycomicbot nano /opt/dailycomicbot/.env"
    echo ""
fi

echo "2. 🚀 Запустите сервис:"
echo "   dailycomicbot-ctl start"
echo ""
echo "3. 📊 Проверьте статус:"
echo "   dailycomicbot-ctl status"
echo ""
echo "4. 📝 Просмотр логов:"
echo "   dailycomicbot-ctl logs"
echo ""
echo "🛠️  Команды управления:"
echo "   dailycomicbot-ctl {start|stop|restart|status|logs|update}"
echo ""
echo "💾 Бэкап:"
echo "   backup-dailycomicbot"
echo ""
echo "📁 Файлы приложения: /opt/dailycomicbot"
echo "📁 Логи: /opt/dailycomicbot/logs"
echo "📁 Данные: /opt/dailycomicbot/data"
echo ""

if [[ "$ENV_CONFIGURED" == "false" ]]; then
    log_warn "⚠️  НЕ ЗАБУДЬТЕ настроить .env файл перед запуском!"
fi

log_info "✅ Деплой завершен успешно!"
