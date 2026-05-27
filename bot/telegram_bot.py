#!/usr/bin/env python3
"""Telegram Bot — Анекдот в тему @anekdot_v_temu_bot

Запуск:
    export TELEGRAM_BOT_TOKEN="123456:ABC..."
    export API_BASE="http://localhost:8000"  # или URL сервера
    python bot/telegram_bot.py
"""
import os, sys, json, logging
import requests

try:
    import telebot
except ImportError:
    print("Установите pyTelegramBotAPI: pip install pyTelegramBotAPI")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

if not TOKEN:
    print("❌ Установите TELEGRAM_BOT_TOKEN")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)


def api(path, method="GET", json_data=None):
    """Call the backend API."""
    url = f"{API_BASE}{path}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=10)
        else:
            r = requests.post(url, json=json_data, timeout=10)
        return r.json()
    except Exception as e:
        logger.error(f"API error: {e}")
        return None


@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.reply_to(msg,
        "😂 <b>Анекдот в тему!</b>\n\n"
        "Просто напиши мне ситуацию или тему — я подберу подходящий анекдот!\n\n"
        "📋 <b>Команды:</b>\n"
        "/start — это сообщение\n"
        "/random — случайный анекдот\n"
        "/categories — список категорий\n"
        "/top — топ анекдотов дня\n"
        "/cat &lt;название&gt; — анекдоты из категории",
        parse_mode="HTML"
    )


@bot.message_handler(commands=["random"])
def cmd_random(msg):
    data = api("/api/joke/random")
    if data:
        text = f"😂 {data['text']}\n\n📂 {data['category']} | ⭐ {data.get('rating', '?')}"
        bot.reply_to(msg, text)
    else:
        bot.reply_to(msg, "😔 Не удалось получить анекдот. Попробуйте позже.")


@bot.message_handler(commands=["categories"])
def cmd_categories(msg):
    data = api("/api/categories")
    if data:
        lines = ["📂 <b>Категории анекдотов:</b>\n"]
        emojis = {
            'работа': '💼', 'айти': '💻', 'деньги': '💰', 'семья': '👨‍👩‍👧',
            'политика': '🏛️', 'здоровье': '🏥', 'путешествия': '✈️', 'еда': '🍽️',
            'наука': '🔬', 'спорт': '⚽', 'образование': '🎓', 'отношения': '💑',
            'коронавирус': '😷', 'искусственный интеллект': '🤖', 'друзья': '🤝',
            'котики': '🐱', 'авто': '🚗', 'магазины': '🛒', 'дети': '👶', 'реклама': '📢'
        }
        for cat, count in sorted(data.items(), key=lambda x: -x[1]):
            e = emojis.get(cat, '📖')
            lines.append(f"{e} /cat_{cat} — {count} шт.")
        bot.reply_to(msg, "\n".join(lines), parse_mode="HTML")
    else:
        bot.reply_to(msg, "😔 Не удалось загрузить категории.")


@bot.message_handler(commands=["top"])
def cmd_top(msg):
    data = api("/api/jokes/social/top?period=day&count=5")
    if data and data.get("jokes"):
        lines = ["🏆 <b>Топ анекдотов дня:</b>\n"]
        for i, j in enumerate(data["jokes"][:5], 1):
            lines.append(f"{i}. {j['text'][:100]}...\n⭐ {j.get('rating',0)} | ❤️ {j.get('likes',0)}\n")
        bot.reply_to(msg, "\n".join(lines), parse_mode="HTML")
    else:
        # Fallback to random popular
        data = api("/api/jokes?count=5")
        if data:
            lines = ["🎲 <b>Популярные анекдоты:</b>\n"]
            for i, j in enumerate(data["jokes"][:5], 1):
                lines.append(f"{i}. {j['text'][:120]}\n📂 {j['category']} | ⭐ {j.get('rating','?')}\n")
            bot.reply_to(msg, "\n".join(lines), parse_mode="HTML")


@bot.message_handler(func=lambda m: m.text and m.text.startswith("/cat"))
def cmd_category(msg):
    cat = msg.text.replace("/cat", "").strip().replace("_", " ")
    if not cat:
        bot.reply_to(msg, "Укажите категорию: /cat айти")
        return
    data = api(f"/api/jokes?category={cat}&count=3")
    if data and data.get("jokes"):
        for j in data["jokes"]:
            text = f"😂 {j['text']}\n\n📂 {j['category']} | ⭐ {j.get('rating', '?')}"
            bot.send_message(msg.chat.id, text)
    else:
        bot.reply_to(msg, f"😔 Категория «{cat}» не найдена. Смотри /categories")


@bot.message_handler(content_types=["text"])
def on_text(msg):
    """Main handler — find contextual joke for any text."""
    text = msg.text
    if text.startswith("/"):
        return

    data = api("/api/jokes/context", method="POST", json_data={"text": text, "count": 3})
    if data and data.get("jokes"):
        joke = data["jokes"][0]
        response = f"😂 {joke['text']}\n\n📂 {joke['category']} | ⭐ {joke.get('rating', '?')}"
        if joke.get("semantic_score"):
            response += f" | 🎯 {int(joke['semantic_score']*100)}%"
        bot.reply_to(msg, response)
    else:
        # Fallback random
        data = api("/api/joke/random")
        if data:
            bot.reply_to(msg, f"🤷 Не нашёл подходящий, но вот:\n\n😂 {data['text']}")
        else:
            bot.reply_to(msg, "😔 Что-то пошло не так. Попробуйте /random")


if __name__ == "__main__":
    logger.info("🤖 Starting Анекдот в тему Telegram Bot...")
    logger.info(f"API: {API_BASE}")
    bot.infinity_polling()
