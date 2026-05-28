#!/usr/bin/env python3
"""
Overlay — полупрозрачное всплывающее окно ПО ВЕРХ ВСЕХ ОКОН,
показывающее шутки из бэкенда «Анекдот в тему».

Запуск:
    python3 overlay.py
    # или с указанием Python из venv:
    /app/venv/bin/python overlay.py

Особенности:
  • tkinter — без тяжёлых зависимостей (PyQt/GTK)
  • always-on-top + полупрозрачность через wm_attributes
  • Fade-in анимация при появлении новой шутки
  • Автообновление каждые 15-20 секунд
  • Кнопка ✕ для закрытия
  • Маленькое окно в правом нижнем углу
"""

import tkinter as tk
import urllib.request
import urllib.error
import json
import random
import logging
import sys
import time
import os

# ============================================================
# Настройки
# ============================================================

# URL бэкенда для случайной шутки
API_URL = os.environ.get("BASE_URL", "http://localhost:8000") + "/api/joke/random"

# URL для контекстного подбора (если voice_monitor передал контекст)
API_CONTEXT_URL = os.environ.get("BASE_URL", "http://localhost:8000") + "/api/jokes/context"

# Интервал обновления шутки (секунды) — случайно 15..20
UPDATE_INTERVAL_MIN = 15
UPDATE_INTERVAL_MAX = 20

# Таймаут запроса к API (секунды)
API_TIMEOUT = 5

# Размеры окна
WINDOW_WIDTH = 380
WINDOW_HEIGHT = 180

# Отступ от краёв экрана (правый нижний угол)
MARGIN_RIGHT = 20
MARGIN_BOTTOM = 60

# Прозрачность фона (0.0 — полностью прозрачно, 1.0 — непрозрачно)
ALPHA_TARGET = 0.88

# Шаг fade-in анимации
FADE_STEP = 0.05
FADE_DELAY_MS = 30  # миллисекунды между шагами

# Шрифт для шутки
JOKE_FONT = ("Arial", 13, "bold")
JOKE_FG = "#FFFFFF"

# Цвета
BG_COLOR = "#1E1E2E"
CLOSE_BTN_FG = "#FF5555"
CLOSE_BTN_BG = "#313244"
BORDER_COLOR = "#45475A"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("overlay")


# ============================================================
# Функция загрузки шутки
# ============================================================

def fetch_joke() -> str:
    """
    Получить шутку — сначала из voice_monitor (latest_joke.json),
    если нет свежей — случайную с бэкенда.
    """
    # 1. Проверяем есть ли свежая шутка от voice_monitor
    try:
        bridge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "latest_joke.json")
        if os.path.exists(bridge_path):
            with open(bridge_path, "r", encoding="utf-8") as f:
                bridge = json.load(f)
            ts = bridge.get("timestamp", 0)
            joke = bridge.get("joke", {})
            # Если шутка свежая (< 30 сек) — берём её
            if joke and (time.time() - ts) < 30:
                text = joke.get("text", "").strip()
                if text:
                    logger.info("📍 Контекстная шутка от voice_monitor (cat=%s)", joke.get("category"))
                    return text
    except Exception:
        pass

    # 2. Fallback — случайная шутка с бэкенда
    try:
        req = urllib.request.Request(
            API_URL,
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # Бэкенд возвращает: {"id": ..., "text": ..., "category": ..., ...}
        if isinstance(data, dict) and "text" in data:
            joke_text = data["text"].strip()
            if joke_text:
                logger.info("Получена шутка (id=%s, cat=%s)",
                            data.get("id"), data.get("category"))
                return joke_text

        # Если пришел список (маловероятно, но обработаем)
        if isinstance(data, list) and len(data) > 0:
            first = data[0]
            if isinstance(first, dict) and "text" in first:
                return first["text"].strip()

        logger.warning("Неожиданный формат ответа: %s", type(data))
        return "Шутка загружается…"

    except urllib.error.URLError as e:
        logger.warning("Сервер недоступен (%s): %s", API_URL, e)
        return "⏳ Сервер не отвечает…"
    except Exception as e:
        logger.error("Ошибка при получении шутки: %s", e)
        return f"⚠️ Ошибка: {e}"


# ============================================================
# Класс Overlay-окна
# ============================================================

class JokeOverlay:
    """Полупрозрачное overlay-окно для показа шуток."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Анекдот в тему")
        self.root.withdraw()  # скрываем до завершения настройки

        # Убираем рамку окна
        self.root.overrideredirect(True)

        # Поверх всех окон
        self.root.attributes("-topmost", True)

        # Начальная прозрачность = 0 (для fade-in)
        self.root.attributes("-alpha", 0.0)

        # Фон
        self.root.configure(bg=BG_COLOR)

        # Позиция — правый нижний угол
        self._position_window()

        # Отслеживаем изменение размера экрана
        self.root.bind("<Configure>", self._on_configure)

        # Создаём виджеты
        self._create_widgets()

        # Drag-and-drop — перетаскивание окна за заголовок
        self._drag_data = {"x": 0, "y": 0}
        self.header_frame.bind("<ButtonPress-1>", self._drag_start)
        self.header_frame.bind("<B1-Motion>", self._drag_move)

        # Показываем окно
        self.root.deiconify()
        self.root.update_idletasks()

        # Первая шутка
        self.current_joke = ""
        self._load_and_show_joke()

        # Пытаемся периодически поднимать окно наверх
        self._keep_on_top()

    # ----------------------------------------------------------
    # Позиционирование
    # ----------------------------------------------------------

    def _position_window(self):
        """Разместить окно в правом нижнем углу экрана."""
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - WINDOW_WIDTH - MARGIN_RIGHT
        y = screen_h - WINDOW_HEIGHT - MARGIN_BOTTOM
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    def _on_configure(self, event):
        """Переразмещение при изменении экрана."""
        pass  # позиция фиксирована при старте

    # ----------------------------------------------------------
    # Виджеты
    # ----------------------------------------------------------

    def _create_widgets(self):
        """Создать все виджеты overlay-окна."""

        # Рамка-контейнер с бордером
        self.outer_frame = tk.Frame(
            self.root, bg=BORDER_COLOR, padx=2, pady=2
        )
        self.outer_frame.pack(fill="both", expand=True)

        # Внутренний контейнер
        self.inner_frame = tk.Frame(
            self.outer_frame, bg=BG_COLOR
        )
        self.inner_frame.pack(fill="both", expand=True)

        # Шапка: заголовок + кнопка закрытия
        self.header_frame = tk.Frame(self.inner_frame, bg=BG_COLOR)
        self.header_frame.pack(fill="x", padx=(8, 4), pady=(6, 2))

        self.title_label = tk.Label(
            self.header_frame,
            text="😄 Анекдот в тему",
            font=("Arial", 9),
            fg="#A6ADC8",
            bg=BG_COLOR,
            anchor="w",
        )
        self.title_label.pack(side="left")

        # Кнопка «✕» закрытия
        self.close_btn = tk.Label(
            self.header_frame,
            text=" ✕ ",
            font=("Arial", 11, "bold"),
            fg=CLOSE_BTN_FG,
            bg=CLOSE_BTN_BG,
            cursor="hand2",
        )
        self.close_btn.pack(side="right", padx=2)
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.config(bg="#585B70"))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.config(bg=CLOSE_BTN_BG))
        self.close_btn.bind("<ButtonPress-1>", lambda e: self._close())

        # Текст шутки (основной контент)
        self.joke_label = tk.Label(
            self.inner_frame,
            text="Загрузка шутки…",
            font=JOKE_FONT,
            fg=JOKE_FG,
            bg=BG_COLOR,
            wraplength=WINDOW_WIDTH - 40,
            justify="center",
            anchor="center",
        )
        self.joke_label.pack(
            fill="both", expand=True, padx=12, pady=(4, 10)
        )

    # ----------------------------------------------------------
    # Drag-and-drop (перетаскивание окна)
    # ----------------------------------------------------------

    def _drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _drag_move(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    # ----------------------------------------------------------
    # Анимация fade-in
    # ----------------------------------------------------------

    def _fade_in(self, current_alpha: float = 0.0):
        """Плавное появление окна (fade in)."""
        if current_alpha < ALPHA_TARGET:
            current_alpha = min(current_alpha + FADE_STEP, ALPHA_TARGET)
            self.root.attributes("-alpha", current_alpha)
            self.root.after(FADE_DELAY_MS, lambda: self._fade_in(current_alpha))

    def _fade_out_and_update(self):
        """Плавное исчезновение → обновление шутки → появление."""
        current = self.root.attributes("-alpha")
        if current and float(current) > 0.02:
            new_alpha = float(current) - FADE_STEP
            self.root.attributes("-alpha", max(new_alpha, 0.0))
            self.root.after(FADE_DELAY_MS, self._fade_out_and_update)
        else:
            # Обновляем текст
            self.joke_label.config(text=self.current_joke)
            self._fade_in(0.0)

    # ----------------------------------------------------------
    # Загрузка и отображение шутки
    # ----------------------------------------------------------

    def _load_and_show_joke(self):
        """Загрузить шутку и показать с fade-in анимацией."""
        self.current_joke = fetch_joke()

        # Если окно уже видимо — fade out, потом обновим
        current_alpha = float(self.root.attributes("-alpha"))
        if current_alpha > 0.1:
            self._fade_out_and_update()
        else:
            self.joke_label.config(text=self.current_joke)
            self._fade_in(0.0)

        # Планируем следующее обновление
        next_interval = random.randint(UPDATE_INTERVAL_MIN, UPDATE_INTERVAL_MAX) * 1000
        self.root.after(next_interval, self._load_and_show_joke)

    # ----------------------------------------------------------
    # Keep on top (периодический подъём окна)
    # ----------------------------------------------------------

    def _keep_on_top(self):
        """Периодически поднимать окно наверх (каждые 5 секунд)."""
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
        except tk.TclError:
            return  # окно уже закрыто
        self.root.after(5000, self._keep_on_top)

    # ----------------------------------------------------------
    # Закрытие
    # ----------------------------------------------------------

    def _close(self):
        """Закрыть overlay."""
        logger.info("Закрытие overlay по запросу пользователя")
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    # ----------------------------------------------------------
    # Запуск
    # ----------------------------------------------------------

    def run(self):
        """Запустить главный цикл Tk."""
        logger.info("Overlay запущен (tkinter, always-on-top)")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self._close()


# ============================================================
# Точка входа
# ============================================================

if __name__ == "__main__":
    overlay = JokeOverlay()
    overlay.run()
