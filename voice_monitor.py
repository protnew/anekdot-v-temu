#!/usr/bin/env python3
"""
Voice Monitor v2 — с поддержкой Whisper (оффлайн) и Google Speech API (fallback)

Слушает микрофон, распознаёт русскую речь, накапливает контекст разговора
и периодически отправляет его на бэкенд для подбора контекстных шуток.

STT движки (автовыбор):
  1. faster-whisper (ОФФЛАЙН, модель base/small) — если установлен
  2. Google Speech API (онлайн, бесплатный) — fallback

Запуск:
    python voice_monitor.py

Зависимости:
    pip install SpeechRecognition pyaudio requests faster-whisper
"""

import time
import threading
import logging
import sys
import os
import json
import re
from datetime import datetime
from collections import deque

import requests

# ============================================================
# Автовыбор STT движка
# ============================================================

STT_ENGINE = "google"  # default fallback

try:
    from faster_whisper import WhisperModel
    STT_ENGINE = "whisper"
    logger_tmp = logging.getLogger("whisper_check")
    logger_tmp.info("faster-whisper найден — используем оффлайн STT")
except ImportError:
    pass

import speech_recognition as sr

# ============================================================
# Настройки (конфигурация)
# ============================================================

# URL бэкенда «Анекдот в тему»
API_URL = os.environ.get("BASE_URL", "http://localhost:8000") + "/api/jokes/context"

# Длительность одного «чанка» записи с микрофона (секунды)
CHUNK_DURATION_SECONDS = 7

# Пауза между отправками контекста на сервер (секунды)
SEND_INTERVAL_SECONDS = 20

# Скользящее окно контекста
CONTEXT_WINDOW_SECONDS = 45

# Количество шуток, запрашиваемых у бэкенда
JOKES_COUNT = 3

# Минимальное количество слов для отправки
MIN_WORDS_TO_SEND = 3

# Таймаут запроса к API (секунды)
API_TIMEOUT_SECONDS = 10

# Максимальное количество тихих чанков подряд
MAX_SILENCE_CHUNKS_WARNING = 10

# Whisper модель (tiny/base/small/medium/large)
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL", "base")

# Whisper: device (cpu/cuda)
WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")

# Whisper: compute_type (int8 для CPU, float16 для GPU)
WHISPER_COMPUTE = "int8" if WHISPER_DEVICE == "cpu" else "float16"

# ============================================================
# Настройка логирования
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("voice_monitor")


# ============================================================
# Whisper STT Engine (оффлайн)
# ============================================================

class WhisperEngine:
    """Оффлайн распознавание речи через faster-whisper."""
    
    def __init__(self, model_size: str = WHISPER_MODEL_SIZE):
        logger.info(f"📦 Загрузка Whisper модели '{model_size}'...")
        self.model = WhisperModel(
            model_size,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE
        )
        logger.info(f"✅ Whisper '{model_size}' загружен ({WHISPER_DEVICE}/{WHISPER_COMPUTE})")
    
    def transcribe_audio(self, audio_data: sr.AudioData) -> str | None:
        """
        Распознать речь из AudioData.
        Возвращает текст или None.
        """
        try:
            # Конвертируем AudioData → numpy array (16kHz, mono)
            import numpy as np
            raw = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
            np_array = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Транскрибация
            segments, info = self.model.transcribe(
                np_array,
                language="ru",
                beam_size=3,
                vad_filter=True,  # Voice Activity Detection — отсекает тишину
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200
                )
            )
            
            # Собираем текст из всех сегментов
            text = " ".join(seg.text.strip() for seg in segments).strip()
            
            if text:
                logger.debug(f"Whisper: «{text}» (язык={info.language}, prob={info.language_probability:.2f})")
                return text
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Whisper ошибка: {e}")
            return None


# ============================================================
# Скользящее окно контекста
# ============================================================

class ConversationContext:
    """
    Скользящее окно контекста разговора.
    Хранит распознанные фрагменты речи с временными метками.
    """

    def __init__(self, window_seconds: int = CONTEXT_WINDOW_SECONDS):
        self.window_seconds = window_seconds
        self._entries: deque = deque()

    def add(self, text: str) -> None:
        now = time.time()
        self._entries.append((now, text.strip()))
        self._cleanup(now)
        logger.info(f"🎤 Услышано: «{text.strip()}»")

    def get_full_context(self) -> str:
        self._cleanup(time.time())
        if not self._entries:
            return ""
        return " ".join(text for _, text in self._entries)

    def get_word_count(self) -> int:
        context = self.get_full_context()
        if not context:
            return 0
        return len(context.split())

    def is_empty(self) -> bool:
        self._cleanup(time.time())
        return len(self._entries) == 0

    def clear(self) -> None:
        self._entries.clear()

    def _cleanup(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._entries and self._entries[0][0] < cutoff:
            self._entries.popleft()


# ============================================================
# Отправка контекста на бэкенд
# ============================================================

class JokeFetcher:
    """Отправляет контекст на бэкенд и получает подходящие шутки."""

    def __init__(self, api_url: str = API_URL, count: int = JOKES_COUNT):
        self.api_url = api_url
        self.count = count
        self._last_sent_context = ""

    def fetch_jokes(self, context: str) -> dict | None:
        if context.strip() == self._last_sent_context.strip():
            logger.debug("Контекст не изменился — пропускаем")
            return None

        payload = {"text": context.strip(), "count": self.count}

        try:
            logger.info(f"📤 Отправляем контекст ({len(context)} символов)...")
            logger.info(f"   «{context[:100]}{'...' if len(context) > 100 else ''}»")

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=API_TIMEOUT_SECONDS
            )
            response.raise_for_status()

            data = response.json()
            self._last_sent_context = context.strip()

            jokes = data.get("jokes", [])
            categories = data.get("matched_categories", [])
            logger.info(f"📥 Получено {len(jokes)} шуток, категории: {categories}")

            return data

        except requests.exceptions.ConnectionError:
            logger.warning(f"⚠️  Не удалось подключиться к серверу {self.api_url}")
            logger.warning("   Убедитесь, что бэкенд запущен: python main.py")
            return None
        except requests.exceptions.Timeout:
            logger.warning("⚠️  Таймаут при запросе к серверу")
            return None
        except Exception as e:
            logger.warning(f"⚠️  Ошибка: {e}")
            return None


# ============================================================
# Вывод шуток + bridge для overlay
# ============================================================

def display_jokes(data: dict) -> None:
    """Красиво вывести шутки + записать в bridge-файл для overlay."""
    jokes = data.get("jokes", [])
    categories = data.get("matched_categories", [])

    # Bridge: записываем лучшую шутку для overlay
    if jokes:
        try:
            bridge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "latest_joke.json")
            best = jokes[0]
            with open(bridge_path, "w", encoding="utf-8") as f:
                json.dump({"joke": best, "timestamp": time.time()}, f, ensure_ascii=False)
        except Exception:
            pass

    if not jokes:
        logger.info("😶 Шуток не найдено для данного контекста")
        return

    print("\n" + "=" * 70)
    print(f"😂 АНЕКДОТЫ В ТЕМУ ({datetime.now().strftime('%H:%M:%S')})")
    if categories:
        print(f"   Категории: {', '.join(categories)}")
    print("=" * 70)

    for i, joke in enumerate(jokes, 1):
        text = joke.get("text", joke.get("joke", ""))
        category = joke.get("category", "—")
        score = joke.get("semantic_score", 0)
        rating = joke.get("rating", "—")

        print(f"\n  #{i} [{category}] (релевантность: {score:.2f}, рейтинг: {rating})")
        words = text.split()
        line = "    "
        for word in words:
            if len(line) + len(word) + 1 > 65:
                print(line)
                line = "    "
            line += word + " "
        if line.strip():
            print(line)

    print("\n" + "=" * 70 + "\n")


# ============================================================
# Основной класс VoiceMonitor
# ============================================================

class VoiceMonitor:
    """
    Главный класс мониторинга голоса.
    
    Слушает микрофон → распознаёт речь (Whisper или Google) → 
    накапливает контекст → отправляет на бэкенд → получает шутки.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.context = ConversationContext()
        self.fetcher = JokeFetcher()
        self._running = False
        self._silence_counter = 0
        self.whisper_engine = None

        # Параметры распознавателя
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

        # Инициализируем Whisper если доступен
        if STT_ENGINE == "whisper":
            try:
                self.whisper_engine = WhisperEngine()
            except Exception as e:
                logger.warning(f"⚠️ Не удалось загрузить Whisper: {e}")
                logger.warning("   Переключаюсь на Google Speech API")
                self.whisper_engine = None

    @property
    def stt_name(self) -> str:
        if self.whisper_engine:
            return f"Whisper ({WHISPER_MODEL_SIZE})"
        return "Google Speech API"

    def _init_microphone(self) -> bool:
        """Инициализировать микрофон."""
        try:
            mic_list = sr.Microphone.list_microphone_names()
            if not mic_list:
                logger.error("❌ Микрофоны не найдены!")
                return False

            logger.info(f"🔊 Найдено микрофонов: {len(mic_list)}")
            for i, name in enumerate(mic_list):
                logger.info(f"   [{i}] {name}")

            self.microphone = sr.Microphone()

            logger.info("🔧 Калибровка шума (помолчите 2 секунды)...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            logger.info(f"✅ Калибровка OK. Порог: {self.recognizer.energy_threshold}")

            return True

        except OSError as e:
            logger.error(f"❌ Ошибка микрофона: {e}")
            logger.error("   Решения:")
            logger.error("   — Проверьте подключение микрофона")
            logger.error("   — Linux: sudo apt install portaudio19-dev")
            logger.error("   — pip install pyaudio")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return False

    def _listen_chunk(self) -> str | None:
        """Записать один чанк и распознать речь."""
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=CHUNK_DURATION_SECONDS + 5,
                    phrase_time_limit=CHUNK_DURATION_SECONDS
                )

            # Сначала пробуем Whisper (оффлайн)
            if self.whisper_engine:
                text = self.whisper_engine.transcribe_audio(audio)
                if text:
                    return text

            # Fallback: Google Speech API (онлайн)
            try:
                text = self.recognizer.recognize_google(audio, language="ru-RU")
                return text if text else None
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                logger.warning(f"⚠️ Google API ошибка: {e}")
                return None

        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            logger.warning(f"⚠️ Ошибка: {e}")
            return None

    def _send_context_periodically(self) -> None:
        """Фоновый поток: каждые N секунд отправляет контекст."""
        logger.info(f"⏰ Отправка каждые {SEND_INTERVAL_SECONDS}с")

        while self._running:
            time.sleep(SEND_INTERVAL_SECONDS)
            if not self._running:
                break

            if self.context.is_empty():
                continue

            word_count = self.context.get_word_count()
            if word_count < MIN_WORDS_TO_SEND:
                continue

            full_context = self.context.get_full_context()
            result = self.fetcher.fetch_jokes(full_context)
            if result:
                display_jokes(result)

    def start(self) -> None:
        """Запустить мониторинг. Блокирующий вызов."""
        print()
        print("╔══════════════════════════════════════════════════════╗")
        print("║     🎙️  АНЕКДОТ В ТЕМУ — Голосовой монитор v2      ║")
        print("║     Слушаю разговор и подбираю шутки в тему         ║")
        print("╚══════════════════════════════════════════════════════╝")
        print(f"   STT движок: {self.stt_name}")
        print(f"   Whisper модель: {WHISPER_MODEL_SIZE}" if self.whisper_engine else "")
        print()

        if not self._init_microphone():
            logger.error("Микрофон недоступен. Завершение.")
            return

        self._running = True
        sender_thread = threading.Thread(
            target=self._send_context_periodically,
            name="ContextSender",
            daemon=True
        )
        sender_thread.start()

        logger.info(f"🎙️ Мониторинг запущен ({self.stt_name})")
        logger.info(f"   чанк: {CHUNK_DURATION_SECONDS}с, отправка: каждые {SEND_INTERVAL_SECONDS}с")
        logger.info("   Ctrl+C для остановки\n")

        try:
            while self._running:
                text = self._listen_chunk()

                if text:
                    self.context.add(text)
                    self._silence_counter = 0
                else:
                    self._silence_counter += 1
                    if self._silence_counter == MAX_SILENCE_CHUNKS_WARNING:
                        logger.info("💤 Длительная тишина...")
                    elif self._silence_counter % 30 == 0:
                        logger.info("🔇 Нет речи давно. Проверьте микрофон.")

        except KeyboardInterrupt:
            logger.info("\n🛑 Остановка...")
        finally:
            self._running = False
            logger.info("✅ Мониторинг остановлен")


# ============================================================
# Точка входа
# ============================================================

def main():
    monitor = VoiceMonitor()
    monitor.start()


if __name__ == "__main__":
    main()
