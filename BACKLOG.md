# 📋 БЭКЛОГ — Анекдот в тему v3.2

> Обновлено: 28.05.2026
> Статус: **28/28 автотестов ✅ + полный аудит API 26/26 ✅**
> GitHub: **https://github.com/protnew/anekdot-v-temu** (PRIVATE ✅)

---

## ✅ СДЕЛАНО (51 задача)

### v1.0 — MVP (8 задач)
| # | Задача | Статус |
|---|--------|--------|
| 1 | Исследование конкурентов (14 аналогов) | ✅ |
| 2 | Таблица сравнения конкурентов | ✅ |
| 3 | База анекдотов + категории | ✅ |
| 4 | Keyword matching (200+ слов) | ✅ |
| 5 | FastAPI бэкенд | ✅ |
| 6 | SPA фронтенд (тёмная тема, 5 табов) | ✅ |
| 7 | Избранное, рейтинг, поиск | ✅ |
| 8 | Автотесты | ✅ |

### v2.0 — Full Product (12 задач)
| # | Задача | Статус |
|---|--------|--------|
| 9 | TF-IDF Semantic Search (scikit-learn) | ✅ |
| 10 | Cosine similarity + keyword boosting | ✅ |
| 11 | OpenAI GPT-4o-mini генерация + fallback | ✅ |
| 12 | Semantic scores в UI | ✅ |
| 13 | 20 категорий, keyword map 200+ слов | ✅ |
| 14 | SQLite хранилище | ✅ |
| 15 | Telegram Bot | ✅ |
| 16 | Навык Алисы (webhook) | ✅ |
| 17 | Chrome Extension | ✅ |
| 18 | Docker (Dockerfile + compose) | ✅ |
| 19 | PWA (Service Worker + Manifest) | ✅ |
| 20 | README + BACKLOG | ✅ |

### v3.0 — Complete Product (10 задач)
| # | Задача | Статус |
|---|--------|--------|
| 21 | Пользовательские анекдоты (CRUD) | ✅ |
| 22 | Персонализация (liked/disliked категории) | ✅ |
| 23 | Социальные функции (лайки, топ) | ✅ |
| 24 | Аналитика (popular topics, stats) | ✅ |
| 25 | Монетизация stubs (ad, premium) | ✅ |
| 26 | Мультиязычность (15 англ. шуток) | ✅ |
| 27 | Голосовые stubs (STT/TTS) | ✅ |
| 28 | 29 API endpoints | ✅ |
| 29 | Валидация входных данных | ✅ |
| 30 | Docker + документация | ✅ |

### v3.1 — Voice + Bugfix (8 задач)
| # | Задача | Статус | Файл |
|---|--------|--------|------|
| 31 | **База расширена: 506 → 4782 шутки** | ✅ | data/jokes_db.json |
| 32 | **3 источника данных** (VK, Никулин, anekdot.ru) | ✅ | docs/ARCHITECTURE.md |
| 33 | **Voice Monitor** — слушает микрофон, распознаёт речь | ✅ | voice_monitor.py |
| 34 | **Overlay UI** — шутки поверх всех окон (tkinter) | ✅ | overlay.py |
| 35 | **Launcher** — запуск одной командой | ✅ | launcher.py |
| 36 | **Rate speed fix**: 3.0с → 0.26с (кеш + lazy rebuild) | ✅ | main.py |
| 37 | **Favorites per-user** — изоляция пользователей | ✅ | main.py |
| 38 | **8 багов исправлено** (двойной буст, коллизии ID, tags...) | ✅ | main.py |

### v3.2 — Persist + Integration (5 задач)
| # | Задача | Статус | Файл |
|---|--------|--------|------|
| 39 | **Rate Persist** — ratings сохраняются при shutdown + periodic flush 60сек | ✅ | main.py |
| 40 | **EN_JOKES в поисковом индексе** (4797 = 4782 + 15) | ✅ | main.py |
| 41 | **Overlay ↔ Voice Monitor bridge** (latest_joke.json) | ✅ | overlay.py + voice_monitor.py |
| 42 | **GitHub push** — приватный репо, remote настроен | ✅ | github.com/protnew/anekdot-v-temu |
| 43 | **28/28 автотестов** — все зелёные | ✅ | main.py |

### v3.3 — QA + Hardening (8 задач)
| # | Задача | Статус | Файл |
|---|--------|--------|------|
| 44 | **BAT без emoji** — `start.bat` без emoji (не ломает CMD) | ✅ | start.bat |
| 45 | **Веб-логи** — `/logs` с кнопкой «Копировать всё» + фильтры | ✅ | static/logs.html |
| 46 | **Инструкция тестирования** — docs/КАК_ТЕСТИРОВАТЬ.md | ✅ | docs/ |
| 47 | **Whisper base установлен** — faster-whisper base 138MB, оффлайн | ✅ | ~/.cache/huggingface/ |
| 48 | **Полный API аудит** — 26/26 endpoints проверены | ✅ | — |
| 49 | **Hardcoded URL fix** — localhost:8000 → BASE_URL + PORT env vars | ✅ | main.py + voice_monitor.py + overlay.py |
| 50 | **Emoji cleanup** — убраны emoji из startup message (ломали CMD) | ✅ | main.py |
| 51 | **Deep code audit** — 6 py files, syntax OK, imports OK | ✅ | — |

---

## 🔧 ОСТАЛОСЬ СДЕЛАТЬ

### 🔴 Критичное (нужен реальный ПК)

| # | Задача | Описание | Почему не сделано |
|---|--------|----------|-------------------|
| 52 | **Voice Monitor тест с микрофоном** | voice_monitor.py не тестировался с реальным микрофоном | Нужен реальный ПК с микрофоном |
| 53 | **Overlay тест на десктопе** | tkinter + topmost не тестировался на реальном десктопе | Нужен реальный ПК с GUI |

### 🟡 Важное (улучшает продукт)

| # | Задача | Описание | Сложность |
|---|--------|----------|-----------|
| 54 | **Android-версия** | Kotlin + Android Speech API + overlay notification | 1-2 недели |
| 55 | **Парсинг ещё 5000+ анекдотов** | nekdo.ru, bash.im — расширить базу до 10K+ | 3 часа |
| 56 | **Real OpenAI ключ** | С ключом — настоящая генерация анекдотов | 5 мин (нужен ключ) |
| 57 | **Whisper small модель** | 500MB, качество ru=⭐⭐⭐⭐⭐ (сейчас base ⭐⭐⭐⭐) | 10 мин |

### 🟢 Желательное (nice to have)

| # | Задача | Описание | Сложность |
|---|--------|----------|-----------|
| 58 | **Деплой на продакшн** | VPS + Docker + домен + HTTPS | 2 часа |
| 59 | **Навык Алисы — сертификат** | Регистрация в Yandex Dialogs | 1 час |
| 60 | **Telegram бот — реальный токен** | Нужен токен бота @BotFather | 5 мин |
| 61 | **Google Play публикация** | APK/AAB, политика микрофона | 2-3 дня |
| 62 | **TTS озвучка шуток** | Яндекс/Google TTS API | 1 час |

---

## 📊 Актуальная статистика

| Метрика | Значение |
|---------|----------|
| Анекдотов | **4 782** (+ 15 EN) |
| В поисковом индексе | **4 797** |
| Категорий | **20** |
| API endpoints | **29** |
| TF-IDF словарь | **5 000 слов** |
| Автотестов | **28/28 ✅** |
| API аудит | **26/26 ✅** |
| Синтаксис | **6/6 файлов OK** |
| Hardcoded URL | **0** (все через env) |
| Emoji в CMD | **0** (убраны) |
| Голосовой монитор | ✅ (faster-whisper base, оффлайн) |
| Overlay UI | ✅ (tkinter) |
| Веб-логи | ✅ (/logs + copy button) |
| Git коммитов | **12** |
| GitHub | **protnew/anekdot-v-temu** (PRIVATE) |

---

## 🧪 Результаты последнего аудита (28.05.2026)

### API — 26/26 ✅
Все endpoints проверены: GET, POST, edge cases (пустой текст, 1 символ, длинный текст, gibberish).

### Код — 6/6 ✅
| Файл | Размер | Синтаксис |
|------|--------|-----------|
| main.py | 40 KB | ✅ |
| voice_monitor.py | 18 KB | ✅ |
| overlay.py | 14 KB | ✅ |
| launcher.py | 2 KB | ✅ |
| test_app.py | 4 KB | ✅ |
| bot/telegram_bot.py | 6 KB | ✅ |
