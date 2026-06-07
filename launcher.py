#!/usr/bin/env python3
"""
😂 Joke on Topic — Launcher
Starts backend + voice monitor + overlay with a single command
"""
import subprocess, sys, os, time, signal, threading

BASE = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

processes = []

def start_process(name, cmd, cwd=BASE):
    """Start a process and keep a reference to it."""
    print(f"  ▶ Starting {name}...")
    p = subprocess.Popen(cmd, cwd=cwd)
    processes.append((name, p))
    return p

def stop_all():
    """Stop all processes."""
    for name, p in processes:
        print(f"  ⏹ Stopping {name} (PID {p.pid})...")
        p.terminate()
        try:
            p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            p.kill()

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    
    print("😂 Joke on Topic v3.1 — Launcher")
    print("=" * 50)
    print(f"Mode: {mode}")
    print()
    
    # 1. Backend (always needed)
    print("1️⃣ Backend (FastAPI)")
    start_process("backend", [PYTHON, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", os.environ.get("PORT", "8000")])
    time.sleep(2)
    
    if mode in ["full", "voice"]:
        # 2. Voice Monitor
        print("2️⃣ Voice Monitor (microphone)")
        start_process("voice", [PYTHON, "voice_monitor.py"])
    
    if mode in ["full", "overlay"]:
        # 3. Overlay
        print("3️⃣ Overlay (popup jokes)")
        start_process("overlay", [PYTHON, "overlay.py"])
    
    if mode == "server":
        port = os.environ.get("PORT", "8000"); print(f"Backend only. Open http://localhost:{port}")
    
    print()
    print("=" * 50)
    print("✅ Everything is running! Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        while True:
            # Check if any process died
            for name, p in processes:
                if p.poll() is not None:
                    print(f"⚠️ {name} exited with code {p.returncode}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹ Stopping...")
        stop_all()
        print("✅ Everything stopped.")

if __name__ == "__main__":
    main()
