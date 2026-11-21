@echo off
title AI_MONITOR // BOOTLOADER
color 0A
cd /d "%~dp0"

echo ====================================================================
echo   AI_MONITOR // HACKER SURVEILLANCE TERMINAL v4.0
echo ====================================================================
echo.

set "PY_CMD="
py -3 --version >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py -3"
) else (
    python --version >nul 2>nul
    if %errorlevel% equ 0 (
        set "PY_CMD=python"
    )
)

if "%PY_CMD%"=="" (
    color 0C
    echo [ERROR] Python 3 not found!
    echo Install Python 3.11+ from https://www.python.org/downloads/
    echo Make sure "Add python.exe to PATH" is checked.
    echo.
    pause
    exit /b 1
)

echo [OK] Python runner: %PY_CMD%

if not exist ".venv\Scripts\python.exe" (
    echo [..] Creating virtual environment .venv ...
    %PY_CMD% -m venv .venv
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Failed to create .venv
        pause
        exit /b 1
    )
)

set "VENV_PY=.venv\Scripts\python.exe"

echo [..] Installing/verifying dependencies ...
"%VENV_PY%" -m pip install --upgrade pip >nul 2>nul
"%VENV_PY%" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Failed to install requirements.txt
    pause
    exit /b 1
)

echo [OK] Dependencies ready. Launching terminal UI ...
echo.
"%VENV_PY%" run.py
echo.
echo [INFO] Server stopped.
pause
