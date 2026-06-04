@echo off
chcp 65001 >nul
echo ============================================
echo   🔌 Анекдот в Тему — Проброс портов
echo ============================================
echo.

:: The problem: Hermes container only exposes port 8787→8788
:: We need to expose 8000 (API) from the same container
:: Solution: use socat inside the container, then portproxy

echo Проверяю Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker не запущен! Запустите Docker Desktop.
    pause & exit /b 1
)
echo ✅ Docker работает

:: Install socat in container (if not present)
echo.
echo Устанавливаю socat в контейнер...
docker exec hermes2-webui bash -c "which socat || (apt-get update -qq && apt-get install -y -qq socat 2>/dev/null)" >nul 2>&1

:: The REAL solution: Docker proxy via iptables inside container
:: OR: just use docker port forwarding by recreating with additional -p
:: SIMPLEST: docker exec socat forward

echo.
echo Пробрасываю порты...
:: Forward container:8000 → container itself (already listening)
:: We need HOST:8000 → container:8000

:: Use Docker's own network: create a proxy container
docker rm -f anekdot-proxy >nul 2>&1
docker run -d --name anekdot-proxy --network container:hermes2-webui alpine/socat TCP-LISTEN:9000,fork TCP:localhost:8000 >nul 2>&1

:: Actually this won't work with --network container: mode
:: Let's try the direct iptables approach

echo.
echo ============================================
echo   ⚠️ Автоматический проброс не удался.
echo   Используйте ручной способ:
echo.
echo   1. Откройте Docker Desktop
echo   2. Остановите hermes2-webui
echo   3. Измените порты: добавьте 8000:8000
echo   4. Запустите контейнер
echo.
echo   ИЛИ введите команду в PowerShell (Admin):
echo   docker stop hermes2-webui
echo   docker commit hermes2-webui hermes2-backup
echo   docker run -d -p 8788:8787 -p 8000:8000 -p 8080:8080 --name hermes2-webui-new hermes2-backup
echo ============================================
echo.
pause
