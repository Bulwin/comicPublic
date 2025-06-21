@echo off
echo ========================================
echo   ЛОГИ СЕРВЕРА DAILYCOMICBOT
echo ========================================
echo.

REM Замените на ваши данные сервера
set SERVER_USER=root
set SERVER_HOST=95.216.138.177
set SSH_KEY_PATH=path\to\your\ssh\key

echo Подключение к серверу %SERVER_HOST%...
echo.

echo Показ логов в реальном времени (Ctrl+C для выхода)...
echo.

ssh -i "%SSH_KEY_PATH%" %SERVER_USER%@%SERVER_HOST% "sudo journalctl -u dailycomicbot -f"

echo.
echo ========================================
echo   ПРОСМОТР ЛОГОВ ЗАВЕРШЕН
echo ========================================
pause
