@echo off
echo ========================================
echo   ДЕПЛОЙ НА СЕРВЕР DAILYCOMICBOT
echo ========================================
echo.

REM Замените на ваши данные сервера
set SERVER_USER=root
set SERVER_HOST=95.216.138.177
set SSH_KEY_PATH=path\to\your\ssh\key

echo Подключение к серверу %SERVER_HOST%...
echo.

echo 1. Обновление кода из Git...
ssh -i "%SSH_KEY_PATH%" %SERVER_USER%@%SERVER_HOST% "cd /opt/dailycomicbot && git pull origin master"

echo.
echo 2. Перезапуск сервиса...
ssh -i "%SSH_KEY_PATH%" %SERVER_USER%@%SERVER_HOST% "sudo systemctl restart dailycomicbot"

echo.
echo 3. Проверка статуса...
ssh -i "%SSH_KEY_PATH%" %SERVER_USER%@%SERVER_HOST% "sudo systemctl status dailycomicbot --no-pager"

echo.
echo 4. Показ последних логов...
ssh -i "%SSH_KEY_PATH%" %SERVER_USER%@%SERVER_HOST% "sudo journalctl -u dailycomicbot --no-pager -n 20"

echo.
echo ========================================
echo   ДЕПЛОЙ ЗАВЕРШЕН
echo ========================================
pause
