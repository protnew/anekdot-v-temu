@echo off
chcp 65001 >nul
title 😂 Установка Анекдот в тему
color 0B

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║   😂 Анекдот в тему — Установка зависимостей  ║
echo  ╚═══════════════════════════════════════════╝
echo.

:: Check Python
where python >nul 2>nul
if errorlevel 1 (
    echo ❌ Python не установлен!
    echo    Скачайте: https://www.python.org/downloads/
    echo    ⚠️ При установке отметьте "Add Python to PATH"
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do echo ✅ %%i найден
echo.

:: Upgrade pip
echo 📦 Обновление pip...
python -m pip install --upgrade pip --quiet
echo.

:: Install core dependencies (минимум для работы)
echo 📦 Установка основных зависимостей...
echo    (fastapi, uvicorn, scikit-learn, numpy, pydantic)
echo.
pip install fastapi>=0.100.0 uvicorn>=0.23.0 scikit-learn>=1.3.0 numpy>=1.24.0 pydantic>=2.0.0 python-multipart>=0.0.6 --quiet
if errorlevel 1 (
    echo.
    echo ❌ Ошибка установки! Попробуйте:
    echo    pip install fastapi uvicorn scikit-learn numpy pydantic python-multipart
    pause
    exit /b 1
)

echo.
echo ✅ Основные зависимости установлены!
echo.

:: Optional: voice support
echo.
echo 🎤 Голосовые функции (опционально — можно пропустить):
echo    pip install faster-whisper gTTS SpeechRecognition
echo.
echo 🤖 AI генерация шуток (опционально):
echo    pip install openai
echo.

echo ══════════════════════════════════════════
echo ✅ Установка завершена!
echo.
echo Теперь запустите: start.bat
echo ══════════════════════════════════════════
echo.
pause
