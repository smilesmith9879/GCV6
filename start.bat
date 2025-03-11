@echo off
echo ===================================
echo AI Smart Car - Starting Application
echo ===================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed!
    exit /b 1
)

REM Check if app.py exists
if not exist app.py (
    echo Error: app.py not found!
    exit /b 1
)

REM Display IP address
echo Your IP address:
ipconfig | findstr /i "IPv4"
echo.

echo Starting AI Smart Car application...
echo Access the web interface at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the application
echo.

REM Start the application
python app.py 