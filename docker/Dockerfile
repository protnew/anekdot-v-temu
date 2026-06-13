# ============================================================
# Анекдот в Тему v3.18.0 — Docker with faster_whisper STT
# Image: ~800MB (python + sklearn + faster_whisper + ffmpeg)
# ============================================================
FROM python:3.12-slim

# System: ffmpeg for audio conversion, wget for model download
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps (cached layer)
COPY docker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Download Silero VAD model (300KB) for voice activity detection
RUN mkdir -p /app/docker/models && \
    wget -q -O /app/docker/models/silero_vad.onnx \
    "https://github.com/snakers4/silero-vad/raw/refs/heads/master/files/silero_vad.onnx" || true

ENV PYTHONUNBUFFERED=1
ENV WHISPER_CLI_PATH=/usr/local/bin/whisper-cli
ENV WHISPER_MODEL_PATH=/app/docker/models/ggml-base.bin
ENV SILERO_VAD_PATH=/app/docker/models/silero_vad.onnx

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=120s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-u", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
