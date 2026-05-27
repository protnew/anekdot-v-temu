#!/usr/bin/env python3
"""
😂 Анекдот в тему — Launcher
Запускает бэкенд + voice monitor + overlay одной командой
"""
import subprocess, sys, os, time, signal, threading

BASE = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

processes = []

def start_process(name, cmd, cwd=BASE):
    """Запустить процесс и сохранить ссылку."""
    print(f"  ▶ Запуск {name}...")
    p = subprocess.Popen(cmd, cwd=cwd)
    processes.append((name, p))
    return p

def stop_all():
    """Остановить все процессы."""
    for name, p in processes:
        print(f"  ⏹ Остановка {name} (PID {p.pid})...")
        p.terminate()
        try:
            p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            p.kill()

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    
    print("😂 Анекдот в тему v3.1 — Launcher")
    print("=" * 50)
    print(f"Режим: {mode}")
    print()
    
    # 1. Бэкенд (всегда нужен)
    print("1️⃣ Бэкенд (FastAPI)")
    start_process("backend", [PYTHON, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"])
    time.sleep(2)
    
    if mode in ["full", "voice"]:
        # 2. Voice Monitor
        print("2️⃣ Голосовой монитор (микрофон)")
        start_process("voice", [PYTHON, "voice_monitor.py"])
    
    if mode in ["full", "overlay"]:
        # 3. Overlay
        print("3️⃣ Overlay (всплывающие шутки)")
        start_process("overlay", [PYTHON, "overlay.py"])
    
    if mode == "server":
        print("Только бэкенд. Открой http://localhost:8000")
    
    print()
    print("=" * 50)
    print("✅ Всё запущено! Нажми Ctrl+C для остановки")
    print("=" * 50)
    
    try:
        while True:
            # Check if any process died
            for name, p in processes:
                if p.poll() is not None:
                    print(f"⚠️ {name} завершился с кодом {p.returncode}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹ Остановка...")
        stop_all()
        print("✅ Всё остановлено.")

if __name__ == "__main__":
    main()
