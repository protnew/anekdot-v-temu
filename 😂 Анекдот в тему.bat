@echo off
chcp 65001 >nul
title 😂 Анекдот в тему — Шутки через микрофон

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║     😂 АНЕКДОТ В ТЕМУ — Запуск                      ║
echo ║     Слушаю разговор и подбираю шутки в тему         ║
echo ╚══════════════════════════════════════════════════════╝
echo.

REM Переходим в папку где лежит этот bat-файл (папка проекта)
cd /d "%~dp0"

REM Проверяем Python
where python >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установи Python 3.10+ с python.org
    pause
    exit /b 1
)

REM Проверяем venv
if not exist "venv\Scripts\activate.bat" (
    echo 📦 Первая установка — создаю окружение и ставлю зависимости...
    echo    Это займёт 1-2 минуты, потом запуск будет мгновенным.
    echo.
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo Выбери режим:
echo   [1] Веб-интерфейс — открыть http://localhost:8000
echo   [2] Голос — говоришь в микрофон, шутки через 20 сек
echo   [3] Полный — голос + шутки поверх всех окон
echo   [4] Выход
echo.

set /p mode="Введи номер (1-4): "

if "%mode%"=="1" (
    echo.
    echo 🌐 Открой в браузере http://localhost:8000
    echo.
    python launcher.py server
) else if "%mode%"=="2" (
    echo.
    echo 🎙️ Говори в микрофон — шутки появятся через 20 сек!
    echo.
    python launcher.py voice
) else if "%mode%"=="3" (
    echo.
    echo 🎙️ Всё запущено — overlay появится в углу экрана
    echo.
    python launcher.py full
) else (
    exit /b 0
)

pause
