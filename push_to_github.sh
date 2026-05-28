#!/bin/bash
# ============================================================
# 🚀 ВЫЛОЖИТЬ КОД НА GITHUB — 2 КОМАНДЫ
# ============================================================
# 
# ПЕРЕД ЭТИМ:
# 1. Зайди на https://github.com/new
# 2. Создай репозиторий с названием "anekdot-v-temu"
# 3. НЕ ставь галочку "Initialize with README"
# 4. Нажми "Create repository"
# 5. Скопируй URL (будет вида https://github.com/ТВОЙ_ЛОГИН/anekdot-v-temu.git)
#
# ПОТОМ В ТЕРМИНАЛЕ (из папки проекта):
# ============================================================

# Вариант A: Если у тебя Linux/WSL терминал
cd "/data/Сделать/Чейчер SCRUM/ии проекты/5806 Приложение анекдот в тему"
git remote add origin https://github.com/ТВОЙ_ЛОГИН/anekdot-v-temu.git
git push -u origin main

# Вариант B: Если у тебя PowerShell на Windows
cd "C:\Сделать\Чейчер SCRUM\ии проекты\5806 Приложение анекдот в тему"
git remote add origin https://github.com/ТВОЙ_ЛОГИН/anekdot-v-temu.git
git push -u origin main

# ============================================================
# ЕСЛИ НУЖЕН ТОКЕН (GitHub запросит логин/пароль):
#
# 1. Зайди на https://github.com/settings/tokens
# 2. "Generate new token (classic)"
# 3. Поставь галочку "repo" (полный контроль)
# 4. Сгенерируй, скопируй
# 5. При git push: логин = твой GitHub логин, пароль = ТОКЕН
# ============================================================

echo "✅ Готово! Репозиторий: https://github.com/ТВОЙ_ЛОГИН/anekdot-v-temu"
