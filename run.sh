#!/bin/bash
cd "/data/Сделать/Чейчер SCRUM/ии проекты/5806 Приложение анекдот в тему"
exec /app/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 "$@"
