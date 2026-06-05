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
    echo ❌ Python не найден! Сначала запустите install.bat
    pause
    exit /b 1
)

:: Check if deps installed
python -c "import fastapi, uvicorn, sklearn" 2>nul
if errorlevel 1 (
    echo ⚠️ Зависимости не установлены. Запускаю установку...
    pip install fastapi uvicorn scikit-learn numpy pydantic python-multipart --quiet
    echo.
)

echo 🚀 Запуск сервера...
echo.
echo  📍 Веб-версия:       http://localhost:8000/
echo  📍 Десктоп:          http://localhost:8000/desktop
echo  📍 Flutter:          http://localhost:8000/flutter
echo  📍 Landing:          http://localhost:8000/landing
echo  📍 API стат:         http://localhost:8000/api/stats
echo.
echo  ⏳ Индексация 286K анекдотов займёт ~30-60 секунд...
echo  🛑 Для остановки: Ctrl+C
echo.
echo  ══════════════════════════════════════════
echo.

:: Auto-open browser after delay
start "" /b cmd /c "timeout /t 30 /nobreak >nul && start http://localhost:8000/"

python main.py
if errorlevel 1 (
    echo.
    echo ❌ Ошибка запуска! Проверьте лог выше.
    echo.
    echo Попробуйте:
    echo   pip install fastapi uvicorn scikit-learn numpy pydantic python-multipart
    pause
)
