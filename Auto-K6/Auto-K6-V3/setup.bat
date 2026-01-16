@echo off
title Auto-K6 Installer
color 1
echo Verifying Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b 1
)
cls
echo.
echo Installing required packages...
echo.
pip install -r requirements.txt
cls
echo.
echo Installation complete press any key to start Auto-K6-V3.py !
pause>nul
cls
python Auto-K6-V3.py