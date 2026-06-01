#!/bin/bash
# === Деплой «Анекдот в тему» на VPS ===
# Запуск: bash deploy.sh
#
# Требования: Docker + Docker Compose на VPS
# Переменные (.env файл или export):
#   OPENAI_API_KEY=sk-...
#   TELEGRAM_BOT_TOKEN=123456:ABC...
#   PORT=8000 (опционально)

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "========================================"
echo "  Анекдот в тему — Деплой"
echo "========================================"
echo ""

# 1. Проверяем .env
if [ ! -f .env ]; then
    echo "📝 Создаю .env файл..."
    cat > .env << 'ENVEOF'
# Обязательные (заполните перед запуском):
OPENAI_API_KEY=
TELEGRAM_BOT_TOKEN=
# Опциональные:
PORT=8000
ENVEOF
    echo "⚠️  Заполните .env и запустите снова:"
    echo "   nano $PROJECT_DIR/.env"
    exit 1
fi

source .env

# 2. Проверяем ключи
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️  TELEGRAM_BOT_TOKEN не задан — бот НЕ запустится (API будет работать)"
fi

# 3. Билдим
echo "🔨 Билдим Docker образы..."
docker compose -f docker/docker-compose.yml build

# 4. Останавливаем старые
echo "🛑 Останавливаем старые контейнеры..."
docker compose -f docker/docker-compose.yml down 2>/dev/null || true

# 5. Запускаем
echo "🚀 Запускаем..."
docker compose -f docker/docker-compose.yml up -d

# 6. Ждём healthcheck
echo "⏳ Ждём запуска API (до 60 сек)..."
for i in $(seq 1 30); do
    if curl -s http://localhost:${PORT:-8000}/api/stats > /dev/null 2>&1; then
        echo "✅ API запущен!"
        break
    fi
    sleep 2
done

# 7. Статус
echo ""
echo "========================================"
echo "  Статус:"
echo "========================================"
docker compose -f docker/docker-compose.yml ps
echo ""
echo "🌐 API:    http://localhost:${PORT:-8000}"
echo "📱 Веб:    http://localhost:${PORT:-8000}/static/index.html"
echo "📊 Логи:   http://localhost:${PORT:-8000}/logs"
echo ""
echo "📋 Команды управления:"
echo "   docker compose -f docker/docker-compose.yml logs -f   # логи"
echo "   docker compose -f docker/docker-compose.yml restart   # рестарт"
echo "   docker compose -f docker/docker-compose.yml down      # стоп"
