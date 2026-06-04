# 📋 БЭКЛОГ — Анекдот в тему v3.6.0

> Обновлено: 03.06.2026
> Статус: **200 000 шуток, 132 категории, 10 языков, v3.6.0**
> Тесты: **51/51 ✅** (25 backend + 26 moderation) + **138 глубоких проверок, 137 PASS**
> GitHub: **https://github.com/protnew/anekdoot-v-temu** (PRIVATE ✅)

---

## ✅ СДЕЛАНО (75 задач)

### Backend Core (65)
v1.0 MVP (8) → v2.0 Full (12) → v3.0 Complete (10) → v3.1 Voice (8) → v3.2 Persist (5) → v3.3 QA (12) → v3.4 Data+TTS (2) → v3.5 Audit+Multilang (4) → v3.5.1 Fix+Tests (4)

### v3.6.0 — 200K + 10 языков (6)
| # | Задача | Статус |
|---|--------|--------|
| 74 | База 200K: 88K новых шуток, RU→118K, EN→38K, ES→10K, DE→8K, FR→8K | ✅ |
| 75 | 91 новая категория: 132 total (ES/DE/FR/PT/ZH/JA/AR/HI по 10-11) | ✅ |
| 76 | KEYWORD_MAP: 91 мультиязычная категория с keywords | ✅ |
| 77 | Moderation API: /api/moderate, /profanity, /spam | ✅ |
| 78 | Landing route: GET /landing | ✅ |
| 79 | SEO Landing, Discord бот, VK Mini App, Moderation module | ✅ |

### Android v1.1 (4)
| # | Задача | Статус |
|---|--------|--------|
| 66 | Android проект: Kotlin MVVM, Retrofit2, Material3, 64 файла | ✅ |
| 67 | TTS Player, AI-генерация, Топ, быстрые темы, копирование | ✅ |
| 68 | 177 автотестов (MockWebServer + Espresso + ViewModel) | ✅ |
| 69 | start.bat v3.5, .env.example, deploy.sh | ✅ |

---

## 🔧 ОСТАЛОСЬ

### 🔴 Требует участия Алексея (3 задачи)

| # | Задача | Что нужно | Время |
|---|--------|-----------|-------|
| 80 | **Voice Monitor + Overlay тест** | `start.bat` → микрофон → шутка | 10 мин |
| 81 | **Деплой на VPS** | VPS (500₽/мес) + домен → `bash deploy.sh` | 30 мин |
| 82 | **OpenAI API ключ** | Ключ → `.env` → настоящая AI генерация | 5 мин |

### 🟡 Telegram + Discord — нужны токены (2 задачи)

| # | Задача | Что нужно | Инструкция |
|---|--------|-----------|------------|
| 83 | **Telegram бот → прод** | Токен от @BotFather | `/newbot` → скопировать токен → `python bot/telegram_bot.py` |
| 84 | **Discord бот → прод** | Discord Developer токен | См. `docs/DISCORD_BOT_GUIDE.md` — 5 минут, пошагово |

---

## 📊 Статистика v3.6.0

| Метрика | Значение |
|---------|----------|
| Анекдотов | **200 000** |
| Категорий | **132** |
| Языки | **10** (RU, EN, ES, DE, FR, PT, ZH, JA, AR, HI) |
| API endpoints | **34** |
| Backend тесты | **25/25 ✅** |
| Moderation тесты | **26/26 ✅** |
| Глубокий аудит | **138 проверок, 137 PASS** |
| Android тесты | **177** |
| Discord команды | **6** (/joke, /search, /top, /cat, /categories, /stats) |
| Commits | **30+** |

### По языкам

| Язык | Шуток | Категорий |
|------|-------|-----------|
| 🇷🇺 Русский | 117 845 | 21 |
| 🇬🇧 English | 38 025 | 27 |
| 🇪🇸 Español | 10 000 | 10 |
| 🇩🇪 Deutsch | 8 200 | 10 |
| 🇫🇷 Français | 8 000 | 10 |
| 🇧🇷 Português | 5 050 | 10 |
| 🇨🇳 中文 | 3 220 | 11 |
| 🇯🇵 日本語 | 3 220 | 11 |
| 🇸🇦 العربية | 3 220 | 11 |
| 🇮🇳 हिन्दी | 3 220 | 11 |

---

## 📚 Документация

| Файл | Описание |
|------|----------|
| `docs/ROADMAP_1YEAR.md` | Дорожная карта на год |
| `docs/DISCORD_BOT_GUIDE.md` | Discord бот: бизнес-сценарий + инструкция |
| `BACKLOG.md` | Этот файл |
| `.env.example` | Шаблон конфигурации |

## 🚀 Как запустить

```bash
# VPS деплой:
git clone https://github.com/protnew/anekdoot-v-temu.git
cd anekdoot-v-temu
cp .env.example .env && nano .env
bash deploy.sh

# Discord бот:
export DISCORD_BOT_TOKEN="токен"
export API_BASE="http://localhost:8000"
pip install -r bot/discord_requirements.txt
python bot/discord_bot.py

# Telegram бот:
export TELEGRAM_BOT_TOKEN="токен"
python bot/telegram_bot.py
```
