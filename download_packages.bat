@echo off
echo ===================================
echo AI Smart Car - Package Downloader
echo ===================================
echo.
echo This script will download all required packages for offline installation.
echo.

REM Create directory for packages
if not exist offline-packages mkdir offline-packages
echo Downloading packages to: %CD%\offline-packages
echo.

REM Check if requirements.txt exists
if not exist requirements.txt (
    echo Error: requirements.txt not found!
    exit /b 1
)

REM Download packages
python -m pip download -d offline-packages -r requirements.txt

if %ERRORLEVEL% neq 0 (
    echo.
    echo Error downloading packages!
    exit /b 1
)

echo.
echo Packages downloaded successfully!
echo.
echo Transfer the 'offline-packages' directory along with the project files to your Raspberry Pi.
echo.
echo To install on the Raspberry Pi, run:
echo python install.py
echo.
pause 