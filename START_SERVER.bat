@echo off
chcp 65001 >nul 2>&1
title Anekdot v Temu — Quick Start

echo ============================================
echo   Anekdot v Temu v3.14.3
echo   http://localhost:8000
echo ============================================
echo.

cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

pip install -q fastapi uvicorn scikit-learn numpy gTTS pydantic python-multipart openai 2>nul

start "" http://localhost:8000

python -m uvicorn main:app --host 0.0.0.0 --port 8000
