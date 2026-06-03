#!/usr/bin/env python3
"""Telegram Bot — Анекдот в тему

Команды:
    /start — приветствие
    /random — случайный анекдот
    /categories — список категорий
    /top — топ анекдотов
    /cat <название> — анекдоты из категории
    /stats — статистика базы

Inline mode:
    @bot <тема> — подборка шуток прямо в любом чате

Запуск:
    export TELEGRAM_BOT_TOKEN="токен_от_BotFather"
    export API_BASE="http://localhost:8000"
    python bot/telegram_bot.py
"""
import os, sys, json, logging, hashlib

try:
    import telebot
    from telebot import types
except ImportError:
    print("pip install pyTelegramBotAPI")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

if not TOKEN:
    print("TELEGRAM_BOT_TOKEN не задан. Получи токен у @BotFather в Telegram.")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)

# Категории эмодзи
CAT_EMOJIS = {
    'работа': '💼', 'айти': '💻', 'деньги': '💰', 'семья': '👨‍👩‍👧',
    'политика': '🏛️', 'здоровье': '🏥', 'путешествия': '✈️', 'еда': '🍽️',
    'наука': '🔬', 'спорт': '⚽', 'образование': '🎓', 'отношения': '💑',
    'коронавирус': '😷', 'искусственный интеллект': '🤖', 'друзья': '🤝',
    'котики': '🐱', 'авто': '🚗', 'магазины': '🛒', 'дети': '👶', 'реклама': '📢',
    'разное': '📖'
}


def api(path, method="GET", json_data=None):
    """Call backend API."""
    url = f"{API_BASE}{path}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=10)
        else:
            r = requests.post(url, json=json_data, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        logger.error(f"API error: {e}")
        return None


def format_joke(joke):
    """Format joke for Telegram message."""
    emoji = CAT_EMOJIS.get(joke.get('category', ''), '📖')
    text = f"{emoji} {joke['text']}"
    meta_parts = [joke.get('category', '?')]
    if joke.get('rating'):
        meta_parts.append(f"⭐{joke['rating']}")
    if joke.get('semantic_score'):
        meta_parts.append(f"🎯{int(joke['semantic_score']*100)}%")
    if joke.get('generated'):
        meta_parts.append("🤖AI")
    meta = " | ".join(str(p) for p in meta_parts if p)
    return f"{text}\n\n{meta}"


# ========= COMMANDS =========

@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.reply_to(msg,
        "😂 <b>Анекдот в тему!</b>\n\n"
        "Напиши мне ситуацию или тему — подберу анекдот!\n\n"
        "📋 <b>Команды:</b>\n"
        "/random — случайный анекдот\n"
        "/categories — список категорий\n"
        "/top — топ анекдотов\n"
        "/cat работа — анекдоты из категории\n"
        "/stats — статистика базы\n\n"
        "💡 <b>Inline:</b> напиши @bot тема в любом чате",
        parse_mode="HTML"
    )


@bot.message_handler(commands=["random"])
def cmd_random(msg):
    data = api("/api/joke/random")
    if data:
        bot.reply_to(msg, format_joke(data))
    else:
        bot.reply_to(msg, "😔 Не удалось получить анекдот.")


@bot.message_handler(commands=["categories"])
def cmd_categories(msg):
    data = api("/api/categories")
    if not data:
        bot.reply_to(msg, "😔 Не удалось загрузить категории.")
        return
    lines = ["📂 <b>Категории:</b>\n"]
    for cat, count in sorted(data.items(), key=lambda x: -x[1]):
        e = CAT_EMOJIS.get(cat, '📖')
        lines.append(f"{e} /cat_{cat.replace(' ', '_')} — {count}")
    bot.reply_to(msg, "\n".join(lines), parse_mode="HTML")


@bot.message_handler(commands=["top"])
def cmd_top(msg):
    data = api("/api/jokes/social/top")
    if data and data.get("jokes"):
        lines = ["🏆 <b>Топ анекдотов:</b>\n"]
        for i, j in enumerate(data["jokes"][:5], 1):
            lines.append(f"{i}. {j['text'][:150]}\n📂 {j.get('category','')} | ⭐{j.get('rating','?')}\n")
        bot.reply_to(msg, "\n".join(lines), parse_mode="HTML")
    else:
        cmd_random(msg)


@bot.message_handler(commands=["stats"])
def cmd_stats(msg):
    data = api("/api/stats")
    if data:
        text = (
            f"📊 <b>Статистика базы</b>\n\n"
            f"📚 Анекдотов: {data['total_jokes']}\n"
            f"📂 Категорий: {data['categories']}\n"
            f"🔍 Слов в индексе: {data.get('vocabulary_size', '?')}\n"
            f"⭐ Средний рейтинг: {data.get('avg_rating', '?')}\n"
            f"🏷 Версия: {data.get('version', '?')}"
        )
        bot.reply_to(msg, text, parse_mode="HTML")
    else:
        bot.reply_to(msg, "😔 API недоступен.")


@bot.message_handler(func=lambda m: m.text and m.text.startswith("/cat"))
def cmd_category(msg):
    cat = msg.text.replace("/cat", "").strip().replace("_", " ")
    if not cat:
        bot.reply_to(msg, "Укажи категорию: /cat работа\nСмотри /categories")
        return
    data = api(f"/api/jokes?category={cat}&count=3")
    if data and data.get("jokes"):
        for j in data["jokes"]:
            bot.send_message(msg.chat.id, format_joke(j))
    else:
        bot.reply_to(msg, f"Категория «{cat}» не найдена. /categories")


# ========= INLINE MODE =========

@bot.inline_handler(lambda q: True)
def inline_query(query):
    """Inline mode — работает в любом чате."""
    text = query.query.strip()
    results = []

    if not text:
        # Без запроса — случайные шутки
        data = api("/api/joke/random")
        if data:
            results.append(types.InlineQueryResultArticle(
                id="random",
                title=f"😂 {data['text'][:60]}...",
                description=f"📂 {data['category']}",
                input_message_content=types.InputTextMessageContent(
                    message_text=format_joke(data)
                )
            ))
    else:
        # С запросом — контекстный поиск
        data = api("/api/jokes/context", method="POST", json_data={"text": text, "count": 5})
        if data and data.get("jokes"):
            for i, joke in enumerate(data["jokes"][:5]):
                score = int(joke.get('semantic_score', 0) * 100)
                results.append(types.InlineQueryResultArticle(
                    id=f"joke_{i}_{hashlib.md5(joke['text'].encode()).hexdigest()[:8]}",
                    title=f"😂 {joke['text'][:50]}...",
                    description=f"📂 {joke['category']} | 🎯 {score}%",
                    input_message_content=types.InputTextMessageContent(
                        message_text=format_joke(joke)
                    )
                ))

    if not results:
        # Fallback
        data = api("/api/joke/random")
        if data:
            results.append(types.InlineQueryResultArticle(
                id="fallback",
                title="😂 Не нашёл в тему, но вот:",
                description=data['text'][:80],
                input_message_content=types.InputTextMessageContent(
                    message_text=format_joke(data)
                )
            ))

    try:
        bot.answer_inline_query(query.id, results, cache_time=10)
    except Exception as e:
        logger.error(f"Inline error: {e}")


# ========= TEXT HANDLER =========

@bot.message_handler(content_types=["text"])
def on_text(msg):
    """Любой текст → контекстный поиск шутки."""
    text = msg.text
    if text.startswith("/"):
        return

    data = api("/api/jokes/context", method="POST", json_data={"text": text, "count": 3})
    if data and data.get("jokes"):
        joke = data["jokes"][0]
        bot.reply_to(msg, format_joke(joke))
    else:
        data = api("/api/joke/random")
        if data:
            bot.reply_to(msg, f"🤷 Не нашёл подходящий, но вот:\n\n{format_joke(data)}")
        else:
            bot.reply_to(msg, "😔 API недоступен. Попробуй позже.")


# ========= ERROR HANDLER =========

@bot.message_handler(func=lambda m: True)
def fallback(msg):
    bot.reply_to(msg, "Отправь мне текст, тему или /random")


if __name__ == "__main__":
    logger.info("Starting Telegram Bot...")
    logger.info(f"API: {API_BASE}")
    # Set inline mode on
    try:
        bot.set_my_commands([
            types.BotCommand("random", "🎲 Случайный анекдот"),
            types.BotCommand("categories", "📂 Все категории"),
            types.BotCommand("top", "🏆 Топ анекдотов"),
            types.BotCommand("stats", "📊 Статистика"),
        ])
    except Exception:
        pass
    bot.infinity_polling()
