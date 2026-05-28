@echo off
chcp 65001 >nul
title 😂 Анекдот в тему — Шутки через микрофон

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║     😂 АНЕКДОТ В ТЕМУ — Запуск                      ║
echo ║     Слушаю разговор и подбираю шутки в тему         ║
echo ╚══════════════════════════════════════════════════════╝
echo.

REM Папка проекта (рядом с этим bat-файлом)
set "PROJECT_DIR=%~dp0"

cd /d "%PROJECT_DIR%"

REM Проверяем Python
where python >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установи Python 3.10+ с python.org
    pause
    exit /b 1
)

REM Проверяем venv
if not exist "venv\Scripts\activate.bat" (
    echo 📦 Создаю виртуальное окружение и устанавливаю зависимости...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install fastapi uvicorn scikit-learn numpy requests pydantic SpeechRecognition pyaudio faster-whisper
) else (
    call venv\Scripts\activate.bat
)

echo.
echo Выбери режим:
echo   [1] Только бэкенд (веб-интерфейс на http://localhost:8000)
echo   [2] Бэкенд + голос (микрофон → шутки в консоль)
echo   [3] Полный (бэкенд + голос + overlay на экране)
echo   [4] Выход
echo.

set /p mode="Введи номер (1-4): "

if "%mode%"=="1" (
    echo.
    echo 🌐 Запускаю бэкенд... Открой http://localhost:8000
    echo.
    python launcher.py server
) else if "%mode%"=="2" (
    echo.
    echo 🎙️ Запускаю бэкенд + голосовой монитор...
    echo    Говори в микрофон — шутки появятся через 20 сек!
    echo.
    python launcher.py voice
) else if "%mode%"=="3" (
    echo.
    echo 🎙️ Запускаю всё... Overlay появится в углу экрана
    echo.
    python launcher.py full
) else (
    exit /b 0
)

pause
