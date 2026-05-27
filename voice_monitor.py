#!/usr/bin/env python3
"""
Voice Monitor — модуль постоянного мониторинга разговора через микрофон
для проекта «Анекдот в тему».

Слушает микрофон, распознаёт русскую речь через Google Speech Recognition API,
накапливает контекст разговора и периодически отправляет его на бэкенд
для подбора контекстных шуток.

Запуск:
    /app/venv/bin/python voice_monitor.py

Зависимости:
    pip install SpeechRecognition pyaudio requests
"""

import time
import threading
import logging
import sys
import re
from datetime import datetime
from collections import deque

import requests
import speech_recognition as sr

# ============================================================
# Настройки (конфигурация)
# ============================================================

# URL бэкенда «Анекдот в тему»
API_URL = "http://localhost:8000/api/jokes/context"

# Длительность одного «чанка» записи с микрофона (секунды)
# 5-10 секунд — оптимально для Google Speech API
CHUNK_DURATION_SECONDS = 7

# Пауза между отправками контекста на сервер (секунды)
# 15-30 секунд — баланс между оперативностью и нагрузкой
SEND_INTERVAL_SECONDS = 20

# Скользящее окно контекста: сколько последних секунд текста хранить
CONTEXT_WINDOW_SECONDS = 45

# Количество шуток, запрашиваемых у бэкенда
JOKES_COUNT = 3

# Минимальное количество слов в контексте для отправки на сервер
# Если слов меньше — считаем, что речь недостаточна для подбора шутки
MIN_WORDS_TO_SEND = 3

# Таймаут запроса к API (секунды)
API_TIMEOUT_SECONDS = 10

# Максимальное количество неудачных попыток распознавания подряд,
# после которого выводим предупреждение
MAX_SILENCE_CHUNKS_WARNING = 10


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
# Класс для хранения скользящего контекста разговора
# ============================================================

class ConversationContext:
    """
    Скользящее окно контекста разговора.
    Хранит распознанные фрагменты речи с временными метками
    и автоматически удаляет устаревшие записи.
    """

    def __init__(self, window_seconds: int = CONTEXT_WINDOW_SECONDS):
        self.window_seconds = window_seconds
        # Очередь: (timestamp, text)
        self._entries: deque = deque()

    def add(self, text: str) -> None:
        """Добавить распознанный фрагмент речи в контекст."""
        now = time.time()
        self._entries.append((now, text.strip()))
        # Удаляем устаревшие записи
        self._cleanup(now)
        logger.info(f"🎤 Услышано: «{text.strip()}»")

    def get_full_context(self) -> str:
        """
        Получить полный текст контекста (все записи в окне).
        Возвращает пустую строку если контекста нет.
        """
        self._cleanup(time.time())
        if not self._entries:
            return ""
        return " ".join(text for _, text in self._entries)

    def get_word_count(self) -> int:
        """Количество слов в текущем контексте."""
        context = self.get_full_context()
        if not context:
            return 0
        # Считаем слова (разделённые пробелами)
        return len(context.split())

    def is_empty(self) -> bool:
        """Пуст ли контекст."""
        self._cleanup(time.time())
        return len(self._entries) == 0

    def clear(self) -> None:
        """Очистить весь контекст."""
        self._entries.clear()

    def _cleanup(self, now: float) -> None:
        """Удалить записи старше window_seconds."""
        cutoff = now - self.window_seconds
        while self._entries and self._entries[0][0] < cutoff:
            self._entries.popleft()


# ============================================================
# Класс для отправки контекста на бэкенд и получения шуток
# ============================================================

class JokeFetcher:
    """Отправляет контекст на бэкенд и получает подходящие шутки."""

    def __init__(self, api_url: str = API_URL, count: int = JOKES_COUNT):
        self.api_url = api_url
        self.count = count
        self._last_sent_context = ""  # чтобы не отправлять тот же контекст дважды

    def fetch_jokes(self, context: str) -> dict | None:
        """
        Отправить контекст на сервер и получить шутки.
        
        Args:
            context: Текст контекста разговора
            
        Returns:
            Словарь с ответом API или None при ошибке.
            Формат ответа: {
                "jokes": [...],
                "matched_categories": [...],
                "context": "...",
                "search_method": "semantic"
            }
        """
        # Проверяем, что контекст изменился с прошлого раза
        if context.strip() == self._last_sent_context.strip():
            logger.debug("Контекст не изменился с прошлой отправки — пропускаем")
            return None

        payload = {
            "text": context.strip(),
            "count": self.count
        }

        try:
            logger.info(f"📤 Отправляем контекст на сервер ({len(context)} символов)...")
            logger.info(f"   Контекст: «{context[:100]}{'...' if len(context) > 100 else ''}»")

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=API_TIMEOUT_SECONDS
            )
            response.raise_for_status()

            data = response.json()
            self._last_sent_context = context.strip()

            # Логируем результат
            jokes = data.get("jokes", [])
            categories = data.get("matched_categories", [])
            logger.info(f"📥 Получено {len(jokes)} шуток, категории: {categories}")

            return data

        except requests.exceptions.ConnectionError:
            logger.warning(f"⚠️  Не удалось подключиться к серверу {self.api_url}")
            logger.warning("   Убедитесь, что бэкенд запущен (main.py)")
            return None
        except requests.exceptions.Timeout:
            logger.warning("⚠️  Таймаут при запросе к серверу")
            return None
        except requests.exceptions.HTTPError as e:
            logger.warning(f"⚠️  Ошибка HTTP: {e}")
            return None
        except Exception as e:
            logger.warning(f"⚠️  Неожиданная ошибка при запросе: {e}")
            return None


# ============================================================
# Функция для красивого вывода шуток в консоль
# ============================================================

def display_jokes(data: dict) -> None:
    """
    Красиво вывести полученные шутки в консоль.
    Позже эта функция будет заменена на overlay UI.
    """
    jokes = data.get("jokes", [])
    categories = data.get("matched_categories", [])

    if not jokes:
        logger.info("😶 Шуток не найдено для данного контекста")
        return

    # Разделительная линия
    print("\n" + "=" * 70)
    print(f"😂 АНЕКДОТЫ В ТЕМУ ({datetime.now().strftime('%H:%M:%S')})")
    if categories:
        print(f"   Подходящие категории: {', '.join(categories)}")
    print("=" * 70)

    for i, joke in enumerate(jokes, 1):
        text = joke.get("text", joke.get("joke", ""))
        category = joke.get("category", "—")
        score = joke.get("semantic_score", 0)
        rating = joke.get("rating", "—")

        print(f"\n  #{i} [{category}] (релевантность: {score:.2f}, рейтинг: {rating})")
        # Разбиваем длинный текст на строки с отступом
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
    
    Слушает микрофон, распознаёт речь, накапливает контекст
    и периодически запрашивает шутки у бэкенда.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.context = ConversationContext()
        self.fetcher = JokeFetcher()
        self._running = False
        self._silence_counter = 0  # счётчик «тихих» чанков подряд

        # Настройка параметров распознавателя
        # Уровень энергии для определения тишины/речи
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # секунды тишины = конец фразы

    def _init_microphone(self) -> bool:
        """
        Инициализировать микрофон.
        Возвращает True если микрофон найден и доступен.
        """
        try:
            mic_list = sr.Microphone.list_microphone_names()
            if not mic_list:
                logger.error("❌ Микрофоны не найдены!")
                return False

            logger.info(f"🔊 Найдено микрофонов: {len(mic_list)}")
            for i, name in enumerate(mic_list):
                logger.info(f"   [{i}] {name}")

            # Используем микрофон по умолчанию (индекс None)
            self.microphone = sr.Microphone()

            # Калибровка уровня шума (адаптация к окружающей среде)
            logger.info("🔧 Калибровка уровня шума (пожалуйста, не говорите)...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            logger.info(f"✅ Калибровка завершена. Порог энергии: {self.recognizer.energy_threshold}")

            return True

        except OSError as e:
            logger.error(f"❌ Ошибка доступа к микрофону: {e}")
            logger.error("   Возможные причины:")
            logger.error("   — Микрофон не подключён")
            logger.error("   — Нет разрешения на доступ к микрофону")
            logger.error("   — Не установлен PortAudio (portaudio19-dev)")
            return False
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при инициализации микрофона: {e}")
            return False

    def _listen_chunk(self) -> str | None:
        """
        Записать один чанк аудио с микрофона и распознать речь.
        
        Returns:
            Распознанный текст или None если речь не обнаружена.
        """
        try:
            with self.microphone as source:
                # Слушаем указанное количество секунд
                audio = self.recognizer.listen(
                    source,
                    timeout=CHUNK_DURATION_SECONDS + 5,  # максимальное ожидание
                    phrase_time_limit=CHUNK_DURATION_SECONDS
                )

            # Распознаём через Google Speech Recognition (русская речь)
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            return text

        except sr.WaitTimeoutError:
            # Таймаут — ничего не было сказано
            return None
        except sr.UnknownValueError:
            # Речь есть, но не удалось распознать
            logger.debug("🔇 Речь обнаружена, но не распознана (неразборчиво)")
            return None
        except sr.RequestError as e:
            # Ошибка сети при обращении к Google API
            logger.warning(f"⚠️  Ошибка Google Speech API: {e}")
            return None
        except Exception as e:
            logger.warning(f"⚠️  Ошибка при распознавании: {e}")
            return None

    def _send_context_periodically(self) -> None:
        """
        Фоновый поток: каждые SEND_INTERVAL_SECONDS секунд
        проверяет контекст и отправляет его на сервер.
        """
        logger.info(f"⏰ Поток отправки запущен (интервал: {SEND_INTERVAL_SECONDS}с)")

        while self._running:
            time.sleep(SEND_INTERVAL_SECONDS)

            if not self._running:
                break

            # Проверяем: есть ли контекст и достаточно ли слов
            if self.context.is_empty():
                logger.debug("Контекст пуст — нечего отправлять")
                continue

            word_count = self.context.get_word_count()
            if word_count < MIN_WORDS_TO_SEND:
                logger.debug(f"Мало слов в контексте ({word_count}) — пропускаем")
                continue

            # Получаем полный контекст
            full_context = self.context.get_full_context()
            logger.info(f"📊 Контекст ({word_count} слов, {len(full_context)} символов)")

            # Отправляем на сервер
            result = self.fetcher.fetch_jokes(full_context)
            if result:
                display_jokes(result)

    def start(self) -> None:
        """
        Запустить мониторинг голоса.
        Блокирующий вызов — работает до KeyboardInterrupt.
        """
        print()
        print("╔══════════════════════════════════════════════════════╗")
        print("║     🎙️  АНЕКДОТ В ТЕМУ — Голосовой монитор          ║")
        print("║     Слушаю разговор и подбираю шутки в тему         ║")
        print("╚══════════════════════════════════════════════════════╝")
        print()

        # Инициализация микрофона
        if not self._init_microphone():
            logger.error("Не удалось инициализировать микрофон. Завершение.")
            logger.error("Проверьте:")
            logger.error("  1. Микрофон подключён")
            logger.error("  2. Установлен portaudio19-dev (sudo apt install portaudio19-dev)")
            logger.error("  3. Установлен pyaudio (pip install pyaudio)")
            return

        # Запускаем фоновый поток отправки контекста
        self._running = True
        sender_thread = threading.Thread(
            target=self._send_context_periodically,
            name="ContextSender",
            daemon=True  # поток завершится при выходе из основного
        )
        sender_thread.start()

        logger.info(f"🎙️  Мониторинг запущен (чанк: {CHUNK_DURATION_SECONDS}с, "
                     f"отправка: каждые {SEND_INTERVAL_SECONDS}с, "
                     f"окно контекста: {CONTEXT_WINDOW_SECONDS}с)")
        logger.info("Нажмите Ctrl+C для остановки\n")

        try:
            while self._running:
                # Слушаем один чанк
                text = self._listen_chunk()

                if text:
                    # Речь распознана — добавляем в контекст
                    self.context.add(text)
                    self._silence_counter = 0
                else:
                    # Тишина или неразборчивая речь
                    self._silence_counter += 1

                    if self._silence_counter == MAX_SILENCE_CHUNKS_WARNING:
                        logger.info("💤 Длительная тишина — жду речь...")
                    elif self._silence_counter % 30 == 0:
                        # Каждые ~3.5 минуты полной тишины
                        logger.info("🔇 Слишком долго нет речи. Проверьте микрофон.")

        except KeyboardInterrupt:
            logger.info("\n🛑 Остановка мониторинга по запросу пользователя")
        finally:
            self._running = False
            logger.info("✅ Мониторинг остановлен")


# ============================================================
# Точка входа
# ============================================================

def main():
    """Главная функция — запуск голосового монитора."""
    monitor = VoiceMonitor()
    monitor.start()


if __name__ == "__main__":
    main()
