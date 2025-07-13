@echo off
REM AUV Control and Training Suite - Windows Batch Script
REM This script provides easy access to common AUV system operations

setlocal enabledelayedexpansion

echo ========================================
echo    AUV Control and Training Suite
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if we're in the correct directory
if not exist "start.py" (
    echo ERROR: start.py not found
    echo Please run this script from the Unity_Python_Code directory
    pause
    exit /b 1
)

python start.py --start_hardware --start_windows_simulator --processes 6 --fresh