# 📋 БЭКЛОГ — Анекдот в тему v3.5

> Обновлено: 03.06.2026
> Статус: **25/25 тестов ✅, 12/12 API проверок ✅, 112 360 шуток, 41 категория (10 языков)**
> Тестировщики: **187 проверок Android + 187 проверок backend**
> GitHub: **https://github.com/protnew/anekdot-v-temu** (PRIVATE ✅)

---

## ✅ СДЕЛАНО (69 задач)

### Backend (65)
v1.0 MVP (8) → v2.0 Full (12) → v3.0 Complete (10) → v3.1 Voice (8) → v3.2 Persist (5) → v3.3 QA (12) → v3.4 Data+TTS (2) → v3.5 Audit+Multilang (4) → v3.5.1 Fix+Tests (4)

### Android v1.1 (4)
| # | Задача | Статус |
|---|--------|--------|
| 66 | Android проект: Kotlin MVVM, Retrofit2, Material3, 5 экранов, 64 файла, 6300+ строк | ✅ |
| 67 | TTS Player (MediaPlayer), AI-генерация, Топ, быстрые темы, копирование, бейджи | ✅ |
| 68 | 177 автотестов (MockWebServer + Espresso + ViewModel + Model + Repository) | ✅ |
| 69 | start.bat обновлён v3.5, .env.example, deploy.sh проверен | ✅ |

---

## 🔧 ОСТАЛОСЬ (2 задачи)

### 🔴 Проверить на ПК (требует участия Алексея)

| # | Задача | Как проверить |
|---|--------|---------------|
| 70 | **Voice Monitor с микрофоном** | `start.bat` → [2] → говори → шутка через 20 сек |
| 71 | **Overlay на десктопе** | `start.bat` → [4] → окно в углу экрана |

### 🟡 Следующий этап (нужны внешние ресурсы)

| # | Задача | Что нужно |
|---|--------|-----------|
| 72 | **Деплой на VPS** | Домен + HTTPS → `bash deploy.sh` |
| 73 | **Telegram бот live** | Токен от @BotFather → `export TELEGRAM_BOT_TOKEN=... && python bot/telegram_bot.py` |

---

## 📊 Статистика

| Метрика | Значение |
|---------|----------|
| Анекдотов | **112 360** |
| Категорий | **41** |
| Языки | **10** (RU, EN, ES, DE, FR, PT, ZH, JA, AR, HI) |
| API endpoints | **31** |
| Backend тесты | **25/25 ✅** |
| API проверки | **12/12 ✅** |
| Android тесты | **177** |
| TTS | ✅ gTTS (MP3, русский) |
| Whisper | base 138MB + small 461MB |
| Docker | ✅ Dockerfile + compose |
| Android | ✅ v1.1, 5 экранов |
| Commits | **28** |

---

## 📱 Как запустить Android

```bash
# В Android Studio:
File → Open → android/
Sync Gradle → Run
# Минимум SDK 24 (Android 7.0)
```

## 🚀 Как запустить VPS

```bash
# На VPS:
git clone https://github.com/protnew/anekdot-v-temu.git
cd anekdot-v-temu
cp .env.example .env
nano .env  # заполнить TELEGRAM_BOT_TOKEN
bash deploy.sh
```

## 🤖 Как запустить Telegram бота

```bash
# Получить токен у @BotFather: /newbot → скопировать токен
export TELEGRAM_BOT_TOKEN="123456:ABC..."
python bot/telegram_bot.py
```
