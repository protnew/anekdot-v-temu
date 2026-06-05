@echo off
chcp 65001 >nul
title 😂 Анекдот в тему v3.8.0 — Desktop
color 0A

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   😂 Анекдот в тему — Desktop App    ║
echo  ║          Версия 3.8.0               ║
echo  ╚══════════════════════════════════════╝
echo.

:: Check Node.js
where node >nul 2>nul
if errorlevel 1 (
    echo ❌ Node.js не установлен!
    echo    Скачайте: https://nodejs.org/
    pause
    exit /b 1
)

:: Check Python
where python >nul 2>nul
if errorlevel 1 (
    echo ❌ Python не установлен!
    echo    Скачайте: https://python.org/
    pause
    exit /b 1
)

cd /d "%~dp0"

:: Install dependencies if needed
if not exist "node_modules\electron" (
    echo 📦 Установка Electron...
    call npm install
    if errorlevel 1 (
        echo ❌ Ошибка установки!
        pause
        exit /b 1
    )
)

echo 🚀 Запуск...
echo.
call npx electron .
if errorlevel 1 (
    echo.
    echo ❌ Ошибка запуска!
    pause
)
