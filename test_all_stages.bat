@echo off
echo ========================================
echo TESTING ALL STAGES OF DAILYCOMICBOT
echo ========================================
echo.

echo [1/3] Testing News Format...
echo ----------------------------------------
call test_news_format.bat
if %errorlevel% neq 0 (
    echo.
    echo ERROR: News format test failed!
    echo Stopping test sequence.
    pause
    exit /b 1
)

echo.
echo [2/3] Testing Scripts Format...
echo ----------------------------------------
call test_scripts_format.bat
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Scripts format test failed!
    echo Stopping test sequence.
    pause
    exit /b 1
)

echo.
echo [3/3] Testing Images Generation...
echo ----------------------------------------
call test_images_generation.bat
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Images generation test failed!
    echo Stopping test sequence.
    pause
    exit /b 1
)

echo.
echo ========================================
echo ALL TESTS COMPLETED SUCCESSFULLY!
echo ========================================
pause
