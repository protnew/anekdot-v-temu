@echo off
chcp 65001 >nul 2>nul
title Anekdot v Temu

echo.
echo ========================================
echo    ANEKDOT V TEMU - Zapusk
echo    Slutshu razgovor, podbirayu shutki
echo ========================================
echo.

REM Papka proekta = papka etogo bat-fayla
cd /d "%~dp0"

REM Proveryaem Python
python --version >nul 2>&1
if errorlevel 1 (
    echo OSHIBKA: Python ne nayden! Ustanovi Python 3.10+ s python.org
    pause
    exit /b 1
)

REM Proveryaem venv
if not exist "venv\Scripts\python.exe" (
    echo Pervyy zapusk - sozdayu okruzhenie i stavyu zavisimosti...
    echo Eto zaymet 1-2 minuty.
    echo.
    python -m venv venv
    if errorlevel 1 (
        echo OSHIBKA: ne udalos sozdat venv
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    if errorlevel 1 (
        echo OSHIBKA: ne udalos ustanovit zavisimosti
        pause
        exit /b 1
    )
) else (
    call venv\Scripts\activate.bat
)

echo.
echo Vyberi rezhim:
echo   [1] Veb-interfeys - otkroy http://localhost:8000
echo   [2] Golos - govorish v mikrofon, shutki cherez 20 sek
echo   [3] Polnyy - golos + shutki poverh vseh okon
echo   [4] Vyhod
echo.

set /p mode="Vvedi nomer (1-4): "

if "%mode%"=="1" (
    echo.
    echo Otkroy v brauzere http://localhost:8000
    echo.
    python launcher.py server
) else if "%mode%"=="2" (
    echo.
    echo Govori v mikrofon - shutki poyavyatsya cherez 20 sek!
    echo.
    python launcher.py voice
) else if "%mode%"=="3" (
    echo.
    echo Vse zapushcheno - overlay poyavitsya v uglu ekrana
    echo.
    python launcher.py full
) else (
    exit /b 0
)

pause
