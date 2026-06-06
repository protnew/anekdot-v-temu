"""
Анекдот в Тему — Discord Bot
Команды: /joke, /top, /stats, /categories, /cat, /search
Кнопки: 🔀 Ещё, ⭐ Оценить, 🗑 Удалить
"""

import os
import logging
import requests
import discord
from discord import Embed
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button

# ── Логирование ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("joke_bot")

# ── Конфиг ──────────────────────────────────────────────────
API_BASE = os.environ.get("JOKE_API", "http://localhost:8000")
TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
PURPLE = Colour.from_rgb(88, 101, 242)

# ── API helpers ─────────────────────────────────────────────
def api_get(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning("GET %s error: %s", path, e)
        return None

def api_post(path: str, json_data: dict | None = None):
    try:
        r = requests.post(f"{API_BASE}{path}", json=json_data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning("POST %s error: %s", path, e)
        return None

def joke_embed(joke: dict) -> Embed:
    text = joke.get("text", "…")[:4096]
    rating = joke.get("rating", 0)
    category = joke.get("category", "")
    embed = Embed(
        title=f"😂 Анекдот ({category})" if category else "😂 Анекдот",
        description=text,
        colour=PURPLE,
    )
    embed.set_footer(text=f"⭐ {rating}  |  ID: {joke.get('id', '?')}")
    return embed

# ── Bot setup (discord.py + app_commands) ───────────────────
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


class JokeView(View):
    """Кнопки под сообщением с шуткой."""

    def __init__(self, joke_id, category: str | None = None, topic: str | None = None):
        super().__init__(timeout=120)
        self.joke_id = joke_id
        self.category = category
        self.topic = topic

    @discord.ui.button(label="🔀 Ещё", style=discord.ButtonStyle.secondary, emoji="🔀")
    async def btn_more(self, interaction: discord.Interaction, _button: Button):
        """Показать ещё одну шутку."""
        if self.topic:
            data = api_post("/api/jokes/context", json_data={"text": self.topic, "count": 1})
            if data and data.get("jokes"):
                data = data["jokes"][0]
        elif self.category:
            data = api_get("/api/joke/random", params={"category": self.category})
        else:
            data = api_get("/api/joke/random")

        if not data:
            await interaction.response.send_message("⚠️ Не удалось получить шутку.", ephemeral=True)
            return

        jid = data.get("id", 0)
        embed = joke_embed(data)
        view = JokeView(jid, category=self.category, topic=self.topic)
        await interaction.response.send_message(embed=embed, view=view)

    @discord.ui.button(label="⭐ Оценить", style=discord.ButtonStyle.primary, emoji="⭐")
    async def btn_rate(self, interaction: discord.Interaction, _button: Button):
        """Поставить +1 к рейтингу."""
        result = api_post("/api/rate", json_data={"joke_id": self.joke_id, "rating": 5})
        if result:
            await interaction.response.send_message("⭐ Спасибо за оценку!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Не удалось оценить.", ephemeral=True)

    @discord.ui.button(label="🗑 Удалить", style=discord.ButtonStyle.danger, emoji="🗑")
    async def btn_delete(self, interaction: discord.Interaction, _button: Button):
        """Удалить сообщение с шуткой."""
        await interaction.message.delete()


# ── Slash-команды (app_commands) ────────────────────────────
@bot.tree.command(name="joke", description="Получить анекдот")
async def cmd_joke(
    interaction: discord.Interaction,
    topic: str = None,
):
    """Случайная шутка или шутка по теме."""
    if topic:
        data = api_post("/api/jokes/context", json_data={"text": topic, "count": 1})
        if data and data.get("jokes"):
            data = data["jokes"][0]
    else:
        data = api_get("/api/joke/random")

    if not data:
        await interaction.response.send_message("⚠️ Сервис временно недоступен.", ephemeral=True)
        return

    embed = joke_embed(data)
    joke_id = data.get("id", 0)
    view = JokeView(joke_id, topic=topic)
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="top", description="Топ-5 анекдотов по рейтингу")
async def cmd_top(interaction: discord.Interaction):
    """Показать 5 лучших шуток."""
    data = api_get("/api/jokes/social/top", params={"limit": 5})
    if not data or not isinstance(data, dict) or "jokes" not in data:
        await interaction.response.send_message("⚠️ Не удалось загрузить топ.", ephemeral=True)
        return

    jokes = data["jokes"]
    embed = Embed(title="🏆 Топ-5 Анекдотов", colour=PURPLE)
    for i, joke in enumerate(jokes[:5], start=1):
        text = (joke.get("text") or joke.get("joke") or "")[:200]
        rating = joke.get("rating") or joke.get("score") or 0
        embed.add_field(name=f"#{i}  ⭐ {rating}", value=text, inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="stats", description="Статистика сервиса")
async def cmd_stats(interaction: discord.Interaction):
    """Статистика: количество шуток, категорий и т.д."""
    data = api_get("/api/stats")
    if not data:
        await interaction.response.send_message("⚠️ Не удалось получить статистику.", ephemeral=True)
        return

    embed = Embed(title="📊 Статистика", colour=PURPLE)
    for key, value in data.items():
        embed.add_field(name=key, value=str(value), inline=True)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="categories", description="Список всех категорий")
async def cmd_categories(interaction: discord.Interaction):
    """Показать доступные категории."""
    data = api_get("/api/categories")
    if not data:
        await interaction.response.send_message("⚠️ Не удалось загрузить категории.", ephemeral=True)
        return

    # Поддержка формата list и dict
    if isinstance(data, list):
        cats = data
    elif isinstance(data, dict):
        cats = list(data.keys()) if "categories" not in data else data["categories"]
    else:
        cats = []

    text = ", ".join(str(c) for c in cats[:60]) or "Пусто"
    embed = Embed(title="📂 Категории", description=text, colour=PURPLE)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="cat", description="Анекдот из конкретной категории")
async def cmd_cat(
    interaction: discord.Interaction,
    name: str,
):
    """Случайная шутка из заданной категории."""
    data = api_get("/api/joke/random", params={"category": name})
    if not data:
        await interaction.response.send_message(f"⚠️ Категория **{name}** не найдена.", ephemeral=True)
        return

    embed = joke_embed(data)
    joke_id = data.get("id", 0)
    view = JokeView(joke_id, category=name)
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="search", description="Поиск анекдотов по тексту")
async def cmd_search(
    interaction: discord.Interaction,
    query: str,
):
    """Полнотекстовый поиск шуток."""
    data = api_get("/api/jokes/search", params={"q": query, "limit": 3})
    if not data or not data.get("jokes"):
        await interaction.response.send_message(f"🔍 По запросу **{query}** ничего не найдено.", ephemeral=True)
        return

    embed = Embed(title=f"🔍 Результаты: {query}", colour=PURPLE)
    for i, joke in enumerate(data["jokes"][:3], start=1):
        text = joke.get("text", "")[:200]
        rating = joke.get("rating", 0)
        embed.add_field(name=f"#{i}  ⭐ {rating}", value=text, inline=False)

    await interaction.response.send_message(embed=embed)


# ── Запуск ───────────────────────────────────────────────────
@bot.event
async def on_ready():
    await bot.tree.sync()
    log.info("Бот %s запущен (%s)", bot.user, bot.user.id)


if __name__ == "__main__":
    bot.run(TOKEN)
