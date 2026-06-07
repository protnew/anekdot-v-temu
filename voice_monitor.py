#!/usr/bin/env python3
"""
Voice Monitor v2 — with Whisper (offline) and Google Speech API (fallback) support

Listens to the microphone, recognizes Russian speech, accumulates conversation context
and periodically sends it to the backend for matching contextual jokes.

STT engines (auto-selection):
  1. faster-whisper (OFFLINE, base/small model) — if installed
  2. Google Speech API (online, free) — fallback

Usage:
    python voice_monitor.py

Dependencies:
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
# Auto-select STT engine
# ============================================================

STT_ENGINE = "google"  # default fallback

try:
    from faster_whisper import WhisperModel
    STT_ENGINE = "whisper"
    logger_tmp = logging.getLogger("whisper_check")
    logger_tmp.info("faster-whisper found — using offline STT")
except ImportError:
    pass

import speech_recognition as sr

# ============================================================
# Settings (configuration)
# ============================================================

# Backend URL for "Anekdot v temu"
API_URL = os.environ.get("BASE_URL", "http://localhost:8000") + "/api/jokes/context"

# Duration of a single microphone recording chunk (seconds)
CHUNK_DURATION_SECONDS = 7

# Pause between sending context to the server (seconds)
SEND_INTERVAL_SECONDS = 20

# Sliding context window
CONTEXT_WINDOW_SECONDS = 45

# Number of jokes to request from the backend
JOKES_COUNT = 3

# Minimum number of words to send
MIN_WORDS_TO_SEND = 3

# API request timeout (seconds)
API_TIMEOUT_SECONDS = 10

# Maximum number of consecutive silent chunks
MAX_SILENCE_CHUNKS_WARNING = 10

# Whisper model (tiny/base/small/medium/large)
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL", "base")

# Whisper: device (cpu/cuda)
WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")

# Whisper: compute_type (int8 for CPU, float16 for GPU)
WHISPER_COMPUTE = "int8" if WHISPER_DEVICE == "cpu" else "float16"

# ============================================================
# Logging configuration
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
# Whisper STT Engine (offline)
# ============================================================

class WhisperEngine:
    """Offline speech recognition via faster-whisper."""
    
    def __init__(self, model_size: str = WHISPER_MODEL_SIZE):
        logger.info(f"📦 Loading Whisper model '{model_size}'...")
        self.model = WhisperModel(
            model_size,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE
        )
        logger.info(f"✅ Whisper '{model_size}' loaded ({WHISPER_DEVICE}/{WHISPER_COMPUTE})")
    
    def transcribe_audio(self, audio_data: sr.AudioData) -> str | None:
        """
        Recognize speech from AudioData.
        Returns text or None.
        """
        try:
            # Convert AudioData → numpy array (16kHz, mono)
            import numpy as np
            raw = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
            np_array = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcription
            segments, info = self.model.transcribe(
                np_array,
                language="ru",
                beam_size=3,
                vad_filter=True,  # Voice Activity Detection — cuts silence
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200
                )
            )
            
            # Collect text from all segments
            text = " ".join(seg.text.strip() for seg in segments).strip()
            
            if text:
                logger.debug(f"Whisper: \"{text}\" (language={info.language}, prob={info.language_probability:.2f})")
                return text
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Whisper error: {e}")
            return None


# ============================================================
# Sliding context window
# ============================================================

class ConversationContext:
    """
    Sliding window of conversation context.
    Stores recognized speech fragments with timestamps.
    """

    def __init__(self, window_seconds: int = CONTEXT_WINDOW_SECONDS):
        self.window_seconds = window_seconds
        self._entries: deque = deque()

    def add(self, text: str) -> None:
        now = time.time()
        self._entries.append((now, text.strip()))
        self._cleanup(now)
        logger.info(f"🎤 Heard: \"{text.strip()}\"")

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
# Sending context to the backend
# ============================================================

class JokeFetcher:
    """Sends context to the backend and receives matching jokes."""

    def __init__(self, api_url: str = API_URL, count: int = JOKES_COUNT):
        self.api_url = api_url
        self.count = count
        self._last_sent_context = ""

    def fetch_jokes(self, context: str) -> dict | None:
        if context.strip() == self._last_sent_context.strip():
            logger.debug("Context unchanged — skipping")
            return None

        payload = {"text": context.strip(), "count": self.count}

        try:
            logger.info(f"📤 Sending context ({len(context)} characters)...")
            logger.info(f"   \"{context[:100]}{'...' if len(context) > 100 else ''}\"")

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
            logger.info(f"📥 Received {len(jokes)} jokes, categories: {categories}")

            return data

        except requests.exceptions.ConnectionError:
            logger.warning(f"⚠️  Failed to connect to server {self.api_url}")
            logger.warning("   Make sure the backend is running: python main.py")
            return None
        except requests.exceptions.Timeout:
            logger.warning("⚠️  Timeout when requesting server")
            return None
        except Exception as e:
            logger.warning(f"⚠️  Error: {e}")
            return None


# ============================================================
# Displaying jokes + bridge for overlay
# ============================================================

def display_jokes(data: dict) -> None:
    """Pretty-print jokes + write to bridge file for overlay."""
    jokes = data.get("jokes", [])
    categories = data.get("matched_categories", [])

    # Bridge: write best joke for overlay
    if jokes:
        try:
            bridge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "latest_joke.json")
            best = jokes[0]
            with open(bridge_path, "w", encoding="utf-8") as f:
                json.dump({"joke": best, "timestamp": time.time()}, f, ensure_ascii=False)
        except Exception:
            pass

    if not jokes:
        logger.info("😶 No jokes found for this context")
        return

    print("\n" + "=" * 70)
    print(f"😂 ANEKDOTY V TEMU ({datetime.now().strftime('%H:%M:%S')})")
    if categories:
        print(f"   Categories: {', '.join(categories)}")
    print("=" * 70)

    for i, joke in enumerate(jokes, 1):
        text = joke.get("text", joke.get("joke", ""))
        category = joke.get("category", "—")
        score = joke.get("semantic_score", 0)
        rating = joke.get("rating", "—")

        print(f"\n  #{i} [{category}] (relevance: {score:.2f}, rating: {rating})")
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
# Main VoiceMonitor class
# ============================================================

class VoiceMonitor:
    """
    Main voice monitoring class.
    
    Listens to microphone → recognizes speech (Whisper or Google) →
    accumulates context → sends to backend → receives jokes.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.context = ConversationContext()
        self.fetcher = JokeFetcher()
        self._running = False
        self._silence_counter = 0
        self.whisper_engine = None

        # Recognizer parameters
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

        # Initialize Whisper if available
        if STT_ENGINE == "whisper":
            try:
                self.whisper_engine = WhisperEngine()
            except Exception as e:
                logger.warning(f"⚠️ Failed to load Whisper: {e}")
                logger.warning("   Switching to Google Speech API")
                self.whisper_engine = None

    @property
    def stt_name(self) -> str:
        if self.whisper_engine:
            return f"Whisper ({WHISPER_MODEL_SIZE})"
        return "Google Speech API"

    def _init_microphone(self) -> bool:
        """Initialize microphone."""
        try:
            mic_list = sr.Microphone.list_microphone_names()
            if not mic_list:
                logger.error("❌ No microphones found!")
                return False

            logger.info(f"🔊 Microphones found: {len(mic_list)}")
            for i, name in enumerate(mic_list):
                logger.info(f"   [{i}] {name}")

            self.microphone = sr.Microphone()

            logger.info("🔧 Calibrating noise (stay silent for 2 seconds)...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            logger.info(f"✅ Calibration OK. Threshold: {self.recognizer.energy_threshold}")

            return True

        except OSError as e:
            logger.error(f"❌ Microphone error: {e}")
            logger.error("   Solutions:")
            logger.error("   — Check microphone connection")
            logger.error("   — Linux: sudo apt install portaudio19-dev")
            logger.error("   — pip install pyaudio")
            return False
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False

    def _listen_chunk(self) -> str | None:
        """Record one chunk and recognize speech."""
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=CHUNK_DURATION_SECONDS + 5,
                    phrase_time_limit=CHUNK_DURATION_SECONDS
                )

            # First try Whisper (offline)
            if self.whisper_engine:
                text = self.whisper_engine.transcribe_audio(audio)
                if text:
                    return text

            # Fallback: Google Speech API (online)
            try:
                text = self.recognizer.recognize_google(audio, language="ru-RU")
                return text if text else None
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                logger.warning(f"⚠️ Google API error: {e}")
                return None

        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            logger.warning(f"⚠️ Error: {e}")
            return None

    def _send_context_periodically(self) -> None:
        """Background thread: sends context every N seconds."""
        logger.info(f"⏰ Sending every {SEND_INTERVAL_SECONDS}s")

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
        """Start monitoring. Blocking call."""
        print()
        print("╔══════════════════════════════════════════════════════╗")
        print("║     🎙️  ANEKDOT V TEMU — Voice Monitor v2          ║")
        print("║     Listening to conversation and finding jokes     ║")
        print("╚══════════════════════════════════════════════════════╝")
        print(f"   STT engine: {self.stt_name}")
        print(f"   Whisper model: {WHISPER_MODEL_SIZE}" if self.whisper_engine else "")
        print()

        if not self._init_microphone():
            logger.error("Microphone unavailable. Exiting.")
            return

        self._running = True
        sender_thread = threading.Thread(
            target=self._send_context_periodically,
            name="ContextSender",
            daemon=True
        )
        sender_thread.start()

        logger.info(f"🎙️ Monitoring started ({self.stt_name})")
        logger.info(f"   chunk: {CHUNK_DURATION_SECONDS}s, sending: every {SEND_INTERVAL_SECONDS}s")
        logger.info("   Press Ctrl+C to stop\n")

        try:
            while self._running:
                text = self._listen_chunk()

                if text:
                    self.context.add(text)
                    self._silence_counter = 0
                else:
                    self._silence_counter += 1
                    if self._silence_counter == MAX_SILENCE_CHUNKS_WARNING:
                        logger.info("💤 Prolonged silence...")
                    elif self._silence_counter % 30 == 0:
                        logger.info("🔇 No speech for a long time. Check the microphone.")

        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping...")
        finally:
            self._running = False
            logger.info("✅ Monitoring stopped")


# ============================================================
# Entry point
# ============================================================

def main():
    monitor = VoiceMonitor()
    monitor.start()


if __name__ == "__main__":
    main()
