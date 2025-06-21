@echo off
echo ========================================
echo   СТАТУС СЕРВЕРА DAILYCOMICBOT
echo ========================================
echo.

REM Замените на ваши данные сервера
set SERVER_USER=root
set SERVER_HOST=95.216.138.177
set SSH_KEY_PATH=path\to\your\ssh\key

echo Подключение к серверу %SERVER_HOST%...
echo.

echo 1. Статус сервиса...
ssh -i "%SSH_KEY_PATH%" %SERVER_USER%@%SERVER_HOST% "sudo systemctl status dailycomicbot --no-pager"

echo.
echo 2. Последние 30 строк логов...
ssh -i "%SSH_KEY_PATH%" %SERVER_USER%@%SERVER_HOST% "sudo journalctl -u dailycomicbot --no-pager -n 30"

echo.
echo 3. Использование ресурсов...
ssh -i "%SSH_KEY_PATH%" %SERVER_USER%@%SERVER_HOST% "ps aux | grep python | grep -v grep"

echo.
echo ========================================
echo   ПРОВЕРКА ЗАВЕРШЕНА
echo ========================================
pause
