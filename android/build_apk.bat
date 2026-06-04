@echo off
chcp 65001 >nul
echo ============================================
echo   Анекдот в Тему — Android APK Builder
echo   v3.7.0 + whisper.cpp + Voice Pipeline
echo ============================================
echo.
echo Требования:
echo   1. Android Studio (или Android SDK + JDK 17)
echo   2. internet connection (gradle dependencies)
echo.
echo Папка проекта:
cd /d "%~dp0.."
echo   %cd%
echo.

:: Check for Android SDK
if defined ANDROID_HOME (
    echo ✅ ANDROID_HOME = %ANDROID_HOME%
) else (
    echo ⚠️ ANDROID_HOME не установлен
    echo    Откройте Android Studio → Settings → Android SDK → запомните путь
    echo    set ANDROID_HOME=C:\Users\%%USERNAME%%\AppData\Local\Android\Sdk
    echo.
)

:: Check for Java
java -version >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Java найдена
) else (
    echo ❌ Java не найдена! Установите JDK 17+
    pause
    exit /b 1
)

echo.
echo Способ 1: Android Studio (рекомендуется)
echo   File → Open → выберите папку android/
echo   Build → Build Bundle(s)/APK(s) → Build APK(s)
echo   APK будет в: android/app/build/outputs/apk/debug/
echo.
echo Способ 2: Командная строка (нужен Android SDK)
echo   cd android
echo   gradlew assembleDebug
echo.

:: Try to create gradlew if it doesn't exist
cd android
if not exist gradlew (
    echo Создаю gradle wrapper...
    gradle wrapper --gradle-version 8.5 2>nul
    if %errorlevel% neq 0 (
        echo ❌ Gradle не найден. Установите Android Studio.
        pause
        exit /b 1
    )
)

echo.
echo Собираю debug APK...
call gradlew assembleDebug
if %errorlevel%==0 (
    echo.
    echo ============================================
    echo   ✅ APK собран!
    echo ============================================
    echo.
    echo 📱 Файл: android\app\build\outputs\apk\debug\app-debug.apk
    echo.
    echo Скиньте APK на телефон (USB / cloud / email)
    echo и установите (разрешите "Неизвестные источники")
    echo.
    
    :: Copy to project root for easy access
    copy /Y "app\build\outputs\apk\debug\app-debug.apk" "..\anekdot-v3.7.0-debug.apk" >nul
    echo 📋 Копия: anekdot-v3.7.0-debug.apk
) else (
    echo ❌ Ошибка сборки. Проверьте Android SDK и Java.
)

echo.
pause
