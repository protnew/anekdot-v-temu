# 🚀 Анекдот в тему — Инструкция для ПК

> Полное руководство по запуску и тестированию на Windows/Linux/macOS

---

## 📋 Что нужно

| Компонент | Минимум | Рекомендуется |
|-----------|---------|---------------|
| Python | 3.10+ | 3.11+ |
| RAM | 2 GB | 4 GB |
| Микрофон | Любой | USB или гарнитура |
| Интернет | Для Google API | Для Whisper — НЕ нужен |

---

## ⚡ Быстрый старт (3 шага)

### Шаг 1: Скачай проект

```bash
# Вариант A: git clone
git clone https://github.com/protnew/anekdot-v-temu.git
cd anekdot-v-temu

# Вариант B: скачать ZIP с GitHub
# https://github.com/protnew/anekdot-v-temu → Code → Download ZIP
```

### Шаг 2: Установи зависимости

```bash
# Создаём виртуальное окружение
python -m venv venv

# Активируем
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Устанавливаем зависимости
pip install fastapi uvicorn scikit-learn numpy requests pydantic

# Для голосового мониторинга:
pip install SpeechRecognition pyaudio

# Для ОФФЛАЙН распознавания (рекомендуется):
pip install faster-whisper

# Если pyaudio не ставится на Linux:
sudo apt install portaudio19-dev && pip install pyaudio

# Если pyaudio не ставится на Windows:
pip install pipwin && pipwin install pyaudio
```

### Шаг 3: Запусти

```bash
# Режим 1: Только бэкенд + веб-интерфейс (без микрофона)
python launcher.py server
# Открой http://localhost:8000

# Режим 2: Бэкенд + голосовой монитор (микрофон → шутки в консоль)
python launcher.py voice

# Режим 3: Полный (бэкенд + голос + overlay поверх окон)
python launcher.py full
```

---

## 🎙️ Голосовой монитор — как работает

```
Микрофон → [7 сек чанк] → Whisper/Google → Текст
                                                    ↓
                                        Скользящее окно 45 сек
                                                    ↓
                                    Каждые 20 сек → POST /api/jokes/context
                                                    ↓
                                            😂 Шутки на экране
```

### STT движки (автовыбор)

| Движок | Интернет | Качество (русский) | Скорость | Размер |
|--------|----------|-------------------|----------|--------|
| **faster-whisper base** | ❌ Оффлайн | ⭐⭐⭐⭐ | ~1 сек | 150 MB |
| **faster-whisper small** | ❌ Оффлайн | ⭐⭐⭐⭐⭐ | ~2 сек | 500 MB |
| Google Speech API | ✅ Онлайн | ⭐⭐⭐⭐ | ~1 сек | 0 MB |

Модель скачивается **автоматически** при первом запуске (один раз).

### Выбор модели Whisper

```bash
# По умолчанию: base (150MB, хороший баланс)
python voice_monitor.py

# Модель small (500MB, отличный русский):
WHISPER_MODEL=small python voice_monitor.py

# Модель tiny (75MB, быстро но хуже русский):
WHISPER_MODEL=tiny python voice_monitor.py

# С видеокартой (NVIDIA CUDA):
WHISPER_DEVICE=cuda WHISPER_MODEL=small python voice_monitor.py
```

---

## 🧪 Тестирование

### Тест 1: Бэкенд (без микрофона)

```bash
# Запускаем сервер
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# В другом терминале — проверяем
curl http://localhost:8000/api/stats

# Должен вернуть:
# {"total_jokes": 4782, "categories": 20, "version": "3.1.0", ...}

# Тест поиска контекстных шуток
curl -X POST http://localhost:8000/api/jokes/context \
  -H "Content-Type: application/json" \
  -d '{"text": "начальник орал на подчинённых", "count": 3}'

# Веб-интерфейс: http://localhost:8000
```

### Тест 2: Голосовой монитор

```bash
# Запускаем бэкенд
python -m uvicorn main:app --port 8000 &

# Запускаем монитор (скачает модель при первом запуске)
python voice_monitor.py

# Говорите в микрофон что-нибудь:
# "Представляешь, начальник опять орал сегодня"
# "Жена сказала что я мало зарабатываю"
# Через 20 секунд появятся шутки в тему!
```

### Тест 3: Полный (overlay)

```bash
# Запускает всё одной командой
python launcher.py full

# Overlay = полупрозрачное окно с шуткой в углу экрана
# Работает только на десктопе (tkinter)
```

---

## 🔧 Решение проблем

### «Микрофон не найден»

```bash
# Linux: проверь что микрофон виден системой
arecord -l

# Если нет portaudio:
sudo apt install portaudio19-dev

# Если нет pyaudio:
pip install pyaudio
# На Ubuntu 22.04+ может потребоваться:
sudo apt install python3-pyaudio
```

### «Whisper модель не скачивается» (нет интернета)

```bash
# Модели хранятся здесь:
# Linux:   ~/.cache/huggingface/hub/
# Windows: C:\Users\<твой_юзер>\.cache\huggingface\hub\

# Скачай заранее на машине с интернетом:
# base: https://huggingface.co/Systran/faster-whisper-base/resolve/main/model.bin
# small: https://huggingface.co/Systran/faster-whisper-small/resolve/main/model.bin

# Или используй Google Speech API (не нужен whisper):
pip uninstall faster-whisper
python voice_monitor.py  # автоматически переключится на Google
```

### «PyAudio не устанавливается на Windows»

```bash
# Вариант 1: pipwin
pip install pipwin
pipwin install pyaudio

# Вариант 2: скачать .whl вручную
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install PyAudio‑0.2.14‑cp311‑cp311‑win_amd64.whl
```

### «PortAudio error» на Linux

```bash
sudo apt install portaudio19-dev python3-pyaudio
pip install --upgrade pyaudio
```

### «Тишина, ничего не распознаётся»

1. Проверь что микрофон **не отключён** в настройках ОС
2. Проверь что выбран **правильный микрофон** (если их несколько)
3. Увеличь чувствительность: в voice_monitor.py поменяй `energy_threshold = 300` → `energy_threshold = 150`
4. Попробуй модель побольше: `WHISPER_MODEL=small`

---

## 📂 Структура проекта

```
anekdot-v-temu/
├── main.py              ← Бэкенд (FastAPI, 29 API, TF-IDF)
├── voice_monitor.py     ← Голосовой монитор (Whisper + Google)
├── overlay.py           ← Overlay поверх окон (tkinter)
├── launcher.py          ← Запуск одной командой
├── requirements.txt     ← Зависимости
├── static/
│   └── index.html       ← SPA фронтенд (тёмная тема)
├── data/
│   ├── jokes_db.json    ← 4782 анекдота (2.8 MB)
│   └── latest_joke.json ← Bridge: voice → overlay
└── docs/
    └── INSTALL_PC.md    ← Эта инструкция
```

---

## 🎯 Что проверить на ПК

- [ ] Бэкенд запускается (`python -m uvicorn main:app`)
- [ ] Веб-интерфейс работает (`http://localhost:8000`)
- [ ] Поиск шуток работает (вкладка «Поиск» → ввести «работа»)
- [ ] Микрофон виден программой
- [ ] Whisper модель скачалась (при первом запуске, ~150MB)
- [ ] Распознаёт русскую речь (скажите что-нибудь)
- [ ] Через ~20 сек появляются контекстные шутки
- [ ] Overlay показывается поверх окон (если `launcher.py full`)
