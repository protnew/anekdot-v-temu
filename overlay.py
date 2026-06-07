#!/usr/bin/env python3
"""
Overlay — a semi-transparent popup window ON TOP OF ALL WINDOWS,
showing jokes from the «Анекдот в тему» backend.

Usage:
    python3 overlay.py
    # or with Python from venv:
    /app/venv/bin/python overlay.py

Features:
  • tkinter — no heavy dependencies (PyQt/GTK)
  • always-on-top + transparency via wm_attributes
  • Fade-in animation when a new joke appears
  • Auto-update every 15-20 seconds
  • ✕ button to close
  • Small window in the bottom-right corner
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
# Settings
# ============================================================

# Backend URL for a random joke
API_URL = os.environ.get("BASE_URL", "http://localhost:8000") + "/api/joke/random"

# URL for context-based matching (if voice_monitor provided context)
API_CONTEXT_URL = os.environ.get("BASE_URL", "http://localhost:8000") + "/api/jokes/context"

# Joke update interval (seconds) — random 15..20
UPDATE_INTERVAL_MIN = 15
UPDATE_INTERVAL_MAX = 20

# API request timeout (seconds)
API_TIMEOUT = 5

# Window dimensions
WINDOW_WIDTH = 380
WINDOW_HEIGHT = 180

# Margin from screen edges (bottom-right corner)
MARGIN_RIGHT = 20
MARGIN_BOTTOM = 60

# Background transparency (0.0 — fully transparent, 1.0 — opaque)
ALPHA_TARGET = 0.88

# Fade-in animation step
FADE_STEP = 0.05
FADE_DELAY_MS = 30  # milliseconds between steps

# Joke font
JOKE_FONT = ("Arial", 13, "bold")
JOKE_FG = "#FFFFFF"

# Colors
BG_COLOR = "#1E1E2E"
CLOSE_BTN_FG = "#FF5555"
CLOSE_BTN_BG = "#313244"
BORDER_COLOR = "#45475A"

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("overlay")


# ============================================================
# Joke fetching function
# ============================================================

def fetch_joke() -> str:
    """
    Fetch a joke — first from voice_monitor (latest_joke.json),
    if no fresh one is available — a random one from the backend.
    """
    # 1. Check if there is a fresh joke from voice_monitor
    try:
        bridge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "latest_joke.json")
        if os.path.exists(bridge_path):
            with open(bridge_path, "r", encoding="utf-8") as f:
                bridge = json.load(f)
            ts = bridge.get("timestamp", 0)
            joke = bridge.get("joke", {})
            # If the joke is fresh (< 30 sec) — use it
            if joke and (time.time() - ts) < 30:
                text = joke.get("text", "").strip()
                if text:
                    logger.info("📍 Contextual joke from voice_monitor (cat=%s)", joke.get("category"))
                    return text
    except Exception:
        pass

    # 2. Fallback — random joke from the backend
    try:
        req = urllib.request.Request(
            API_URL,
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # Backend returns: {"id": ..., "text": ..., "category": ..., ...}
        if isinstance(data, dict) and "text" in data:
            joke_text = data["text"].strip()
            if joke_text:
                logger.info("Joke received (id=%s, cat=%s)",
                            data.get("id"), data.get("category"))
                return joke_text

        # If a list was returned (unlikely, but handle it)
        if isinstance(data, list) and len(data) > 0:
            first = data[0]
            if isinstance(first, dict) and "text" in first:
                return first["text"].strip()

        logger.warning("Unexpected response format: %s", type(data))
        return "Loading joke…"

    except urllib.error.URLError as e:
        logger.warning("Server unavailable (%s): %s", API_URL, e)
        return "⏳ Server is not responding…"
    except Exception as e:
        logger.error("Error fetching joke: %s", e)
        return f"⚠️ Error: {e}"


# ============================================================
# Overlay window class
# ============================================================

class JokeOverlay:
    """Semi-transparent overlay window for displaying jokes."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Анекдот в тему")
        self.root.withdraw()  # hide until setup is complete

        # Remove window frame
        self.root.overrideredirect(True)

        # On top of all windows
        self.root.attributes("-topmost", True)

        # Initial transparency = 0 (for fade-in)
        self.root.attributes("-alpha", 0.0)

        # Background
        self.root.configure(bg=BG_COLOR)

        # Position — bottom-right corner
        self._position_window()

        # Track screen size changes
        self.root.bind("<Configure>", self._on_configure)

        # Create widgets
        self._create_widgets()

        # Drag-and-drop — drag the window by the header
        self._drag_data = {"x": 0, "y": 0}
        self.header_frame.bind("<ButtonPress-1>", self._drag_start)
        self.header_frame.bind("<B1-Motion>", self._drag_move)

        # Show the window
        self.root.deiconify()
        self.root.update_idletasks()

        # First joke
        self.current_joke = ""
        self._load_and_show_joke()

        # Try to periodically raise the window to the top
        self._keep_on_top()

    # ----------------------------------------------------------
    # Positioning
    # ----------------------------------------------------------

    def _position_window(self):
        """Place the window in the bottom-right corner of the screen."""
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - WINDOW_WIDTH - MARGIN_RIGHT
        y = screen_h - WINDOW_HEIGHT - MARGIN_BOTTOM
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    def _on_configure(self, event):
        """Reposition on screen change."""
        pass  # position is fixed at startup

    # ----------------------------------------------------------
    # Widgets
    # ----------------------------------------------------------

    def _create_widgets(self):
        """Create all overlay window widgets."""

        # Border container frame
        self.outer_frame = tk.Frame(
            self.root, bg=BORDER_COLOR, padx=2, pady=2
        )
        self.outer_frame.pack(fill="both", expand=True)

        # Inner container
        self.inner_frame = tk.Frame(
            self.outer_frame, bg=BG_COLOR
        )
        self.inner_frame.pack(fill="both", expand=True)

        # Header: title + close button
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

        # Close button "✕"
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

        # Joke text (main content)
        self.joke_label = tk.Label(
            self.inner_frame,
            text="Loading joke…",
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
    # Drag-and-drop (window dragging)
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
    # Fade-in animation
    # ----------------------------------------------------------

    def _fade_in(self, current_alpha: float = 0.0):
        """Smooth window appearance (fade in)."""
        if current_alpha < ALPHA_TARGET:
            current_alpha = min(current_alpha + FADE_STEP, ALPHA_TARGET)
            self.root.attributes("-alpha", current_alpha)
            self.root.after(FADE_DELAY_MS, lambda: self._fade_in(current_alpha))

    def _fade_out_and_update(self):
        """Smooth disappearance → update joke → appearance."""
        current = self.root.attributes("-alpha")
        if current and float(current) > 0.02:
            new_alpha = float(current) - FADE_STEP
            self.root.attributes("-alpha", max(new_alpha, 0.0))
            self.root.after(FADE_DELAY_MS, self._fade_out_and_update)
        else:
            # Update the text
            self.joke_label.config(text=self.current_joke)
            self._fade_in(0.0)

    # ----------------------------------------------------------
    # Loading and displaying the joke
    # ----------------------------------------------------------

    def _load_and_show_joke(self):
        """Load a joke and show it with fade-in animation."""
        self.current_joke = fetch_joke()

        # If the window is already visible — fade out, then update
        current_alpha = float(self.root.attributes("-alpha"))
        if current_alpha > 0.1:
            self._fade_out_and_update()
        else:
            self.joke_label.config(text=self.current_joke)
            self._fade_in(0.0)

        # Schedule the next update
        next_interval = random.randint(UPDATE_INTERVAL_MIN, UPDATE_INTERVAL_MAX) * 1000
        self.root.after(next_interval, self._load_and_show_joke)

    # ----------------------------------------------------------
    # Keep on top (periodic window raise)
    # ----------------------------------------------------------

    def _keep_on_top(self):
        """Periodically raise the window to the top (every 5 seconds)."""
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
        except tk.TclError:
            return  # window already closed
        self.root.after(5000, self._keep_on_top)

    # ----------------------------------------------------------
    # Closing
    # ----------------------------------------------------------

    def _close(self):
        """Close the overlay."""
        logger.info("Closing overlay at user request")
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    # ----------------------------------------------------------
    # Run
    # ----------------------------------------------------------

    def run(self):
        """Start the Tk main loop."""
        logger.info("Overlay started (tkinter, always-on-top)")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self._close()


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    overlay = JokeOverlay()
    overlay.run()
