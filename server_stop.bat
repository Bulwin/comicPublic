@echo off
echo ========================================
echo   ОСТАНОВКА СЕРВЕРА DAILYCOMICBOT
echo ========================================
echo.

REM Замените на ваши данные сервера
set SERVER_USER=your_username
set SERVER_HOST=your_server_ip
set SSH_KEY_PATH=path\to\your\ssh\key

echo Подключение к серверу %SERVER_HOST%...
echo.

ssh -i "%SSH_KEY_PATH%" %SERVER_USER%@%SERVER_HOST% "sudo systemctl stop dailycomicbot && echo 'Сервис остановлен' && sudo systemctl status dailycomicbot --no-pager"

echo.
echo ========================================
echo   СЕРВЕР ОСТАНОВЛЕН
echo ========================================
pause
