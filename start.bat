@echo off
chcp 65001 >nul
title 😂 Анекдот в тему v3.8.0
color 0A

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║  😂 Анекдот в тему — AI шутки по контексту  ║
echo  ║            Версия 3.8.0                     ║
echo  ║       286K анекдотов, 120 категорий         ║
echo  ╚═══════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: Check Python
where python >nul 2>nul
if errorlevel 1 (
    echo ❌ Python не найден!
    echo    Скачайте: https://www.python.org/downloads/
    echo    ⚠️ При установке отметьте "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo ✅ %%i

:: Check if deps installed
python -c "import fastapi, uvicorn, sklearn" 2>nul
if errorlevel 1 (
    echo.
    echo ⚠️ Зависимости не установлены. Устанавливаю...
    echo    Это может занять 2-5 минут (первый раз)...
    echo.
    pip install fastapi uvicorn scikit-learn numpy pydantic python-multipart
    if errorlevel 1 (
        echo.
        echo ❌ Ошибка установки! Попробуйте вручную:
        echo    pip install fastapi uvicorn scikit-learn numpy pydantic python-multipart
        echo.
        pause
        exit /b 1
    )
    echo.
    echo ✅ Зависимости установлены!
)

echo.
echo 🚀 Запуск сервера...
echo.
echo  📍 Открой в браузере:  http://localhost:8000/
echo.
echo  Страницы:
echo    http://localhost:8000/          — Веб-версия (SPA)
echo    http://localhost:8000/desktop   — Десктоп-версия
echo    http://localhost:8000/flutter   — Flutter Web
echo.
echo  🛑 Для остановки: Ctrl+C
echo.
echo  ══════════════════════════════════════════
echo.

:: Auto-open browser after 3 seconds
start "" /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8000/"

python main.py 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Ошибка запуска! Смотри лог выше ↑
    echo.
    echo Возможные причины:
    echo   1. Порт 8000 занят — закройте другие программы
    echo   2. Зависимости не установлены — запустите install.bat
    echo   3. Мало памяти — нужно ~1GB RAM для 286K шуток
    echo.
)

pause
