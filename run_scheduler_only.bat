@echo off
chcp 65001 >nul
echo ========================================
echo   ZAPUSK PLANIROVSHCHIKA DAILYCOMICBOT
echo ========================================
echo.

echo Zapusk tolko planirovshchika zadach...
echo.

REM Aktivatsiya virtualnogo okruzheniya (esli est)
if exist "venv\Scripts\activate.bat" (
    echo Aktivatsiya virtualnogo okruzheniya...
    call venv\Scripts\activate.bat
)

REM Zapusk tolko planirovshchika
python run_scheduler_only.py

echo.
echo ========================================
echo   PLANIROVSHCHIK OSTANOVLEN
echo ========================================
pause
