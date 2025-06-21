@echo off
chcp 65001 >nul
echo ========================================
echo   ZAPUSK POLNOGO SERVERA DAILYCOMICBOT
echo ========================================
echo.

echo Zapusk polnogo servera s Telegram botom i planirovshchikom...
echo.

REM Aktivatsiya virtualnogo okruzheniya (esli est)


REM Zapusk polnogo servera
python run_full_server.py

echo.
echo ========================================
echo   SERVER OSTANOVLEN
echo ========================================
pause
