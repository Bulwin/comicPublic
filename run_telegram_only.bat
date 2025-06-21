@echo off
chcp 65001 >nul
echo ========================================
echo   ZAPUSK TELEGRAM BOTA DAILYCOMICBOT
echo ========================================
echo.

echo Zapusk tolko Telegram bota...
echo.

REM Aktivatsiya virtualnogo okruzheniya (esli est)
if exist "venv\Scripts\activate.bat" (
    echo Aktivatsiya virtualnogo okruzheniya...
    call venv\Scripts\activate.bat
)

REM Zapusk tolko Telegram bota
python run_telegram_bot.py

echo.
echo ========================================
echo   TELEGRAM BOT OSTANOVLEN
echo ========================================
pause
