@echo off
chcp 65001 >nul
echo ============================================
echo   🔌 Добавляю порт 8000 для Анекдот API
echo ============================================
echo.
echo Текущий docker-compose.yml:
echo   ports: 8788 → 8787 (Hermes WebUI)
echo   Нужно добавить: 8000 → 8000 (Anekdot API)
echo.

set COMPOSE_FILE=C:\Hermes2\docker-compose.yml

:: Check if port 8000 already added
findstr "8000" "%COMPOSE_FILE%" >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Порт 8000 уже есть в конфиге!
    goto :start_api
)

echo Добавляю порт 8000...
powershell -Command "(Get-Content '%COMPOSE_FILE%') -replace '      - ""127.0.0.1:8788:8787""', '      - ""127.0.0.1:8788:8787""`n      - ""0.0.0.0:8000:8000""' | Set-Content '%COMPOSE_FILE%'"

echo ✅ Порт добавлен!
echo.
echo Перезапускаю контейнер...

cd /d C:\Hermes2
docker compose down
docker compose up -d

echo.
echo Жду запуск контейнера...
timeout /t 15 >nul

:start_api
echo.
echo Запускаю API сервер...
docker exec -d hermes2-webui bash -c "cd '/data/Сделать/Чейчер SCRUM/ии проекты/5806 Приложение анекдот в тему' && export WHISPER_CLI_PATH='/data/Сделать/Чейчер SCRUM/ии проекты/5806 Приложение анекдот в тему/docker/bin/whisper-cli' && export WHISPER_MODEL_PATH='/data/Сделать/Чейчер SCRUM/ии проекты/5806 Приложение анекдот в тему/docker/models/ggml-base.bin' && export SILERO_VAD_PATH='/data/Сделать/Чейчер SCRUM/ии проекты/5806 Приложение анекдот в тему/docker/models/silero_vad.onnx' && export LD_LIBRARY_PATH='/data/Сделать/Чейчер SCRUM/ии проекты/5806 Приложение анекдот в тему/docker/lib' && /app/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000"

echo.
echo Жду загрузку (~90 сек для TF-IDF на 200K шуток)...
timeout /t 90 >nul

echo.
echo Проверяю...
curl -s http://localhost:8000/api/stats | findstr "total_jokes" >nul 2>&1
if %errorlevel%==0 (
    echo ✅ API работает!
    echo.
    echo ============================================
    echo   🌐 Откройте в браузере:
    echo.
    echo   🎤 Эмулятор: http://localhost:8000/emulator
    echo   📊 API статус: http://localhost:8000/api/voice/status
    echo   😂 Шутка: http://localhost:8000/api/joke/random
    echo ============================================
) else (
    echo ⚠️ API ещё загружается. Подождите 30 сек и обновите страницу.
)

echo.
pause
