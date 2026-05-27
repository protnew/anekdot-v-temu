# 🚀 Как выложить код на GitHub

## Способ 1: Через командную строку (рекомендуется)

```bash
# 1. Зайди на github.com и создай НОВЫЙ репозиторий
#    (НЕ ставь галочку "Initialize with README")
#    Назови например: anekdot-v-temu

# 2. В терминале (из папки проекта):
cd "C:\Сделать\Чейчер SCRUM\ии проекты\5806 Приложение анекдот в тему"

git remote add origin https://github.com/ТВОЙ_ЛОГИН/anekdot-v-temu.git
git branch -M main
git push -u origin main
```

## Способ 2: Через GitHub Desktop (проще)

1. Скачай GitHub Desktop: https://desktop.github.com/
2. File → Add Local Repository
3. Выбери папку: `C:\Сделать\Чейчер SCRUM\ии проекты\5806 Приложение анекдот в тему`
4. Publish Repository → готово!

## Способ 3: Через браузер

1. Создай репозиторий на github.com (НЕ ставь README)
2. Нажми "uploading an existing file"
3. Перетащи все файлы из папки проекта
4. Commit

---

## ⚠️ Проблема: .gitignore

Файл `data/jokes_db.json` (2.8MB) уже в коммите. GitHub принимает до 100MB — проходит.
Но если хочешь убрать его из git:

```bash
git rm --cached data/jokes_db.json
git commit -m "remove large JSON from tracking"
```

---

## 📋 Что уже закоммичено

```
commit 0dadf4f "v3.1: voice monitor + overlay + 4782 jokes"

  .gitignore                    — игнор лишних файлов
  main.py                       — бэкенд (830 строк, 29 API)
  voice_monitor.py              — голосовой монитор (454 строки)
  overlay.py                    — overlay с шутками (354 строки)
  launcher.py                   — запуск всего одной командой
  run.sh                        — скрипт запуска бэкенда
  requirements.txt              — зависимости Python
  test_app.py                   — 24 автотеста
  README.md                     — документация
  BACKLOG.md                    — бэклог задач
  static/index.html             — веб-интерфейс
  data/jokes_db.json            — 4782 анекдота (2.8MB)
  bot/telegram_bot.py           — Telegram бот
  extension/manifest.json       — Chrome Extension
  extension/popup.html
  extension/content.js
  extension/background.js
  docker/Dockerfile             — Docker
  docker/docker-compose.yml
  docs/ARCHITECTURE.md          — архитектура
  docs/competitor_analysis.md   — анализ конкурентов
```
