@echo off
REM =========================================================
REM Saffron AI Climate Controller - Backend Launch Script
REM Author: Abhishek
REM Date: 2026-03-22
REM =========================================================

setlocal
CHCP 65001 >nul

set "VENV_DIR=.venv"
set "ANA_PYTHON=C:\ProgramData\anaconda3\python.exe"

if exist "%VENV_DIR%" (
    if not exist "%VENV_DIR%\Scripts\activate.bat" (
        echo [!] Repairing corrupted environment...
        rmdir /S /Q "%VENV_DIR%"
    )
)

if not exist "%VENV_DIR%" (
    echo [1/3] Creating Python 3.12 environment...
    "%ANA_PYTHON%" -m venv "%VENV_DIR%"
    if ERRORLEVEL 1 (
        echo [ERROR] Failed to create venv
        exit /b 1
    )
)

echo [2/3] Activating environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo [3/3] Checking dependencies...
pip install -r requirements.txt -q

echo [API] Ready at http://localhost:5000
python api.py

exit /b 0
