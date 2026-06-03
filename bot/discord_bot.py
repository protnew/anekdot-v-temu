"""
Анекдот в Тему — Discord Bot
Slash-команды: /joke, /top, /stats, /categories, /cat
Кнопки: 🔀 Ещё, ⭐ Оценить, 🗑 Удалить
"""

import os
import logging
import requests
import discord
from discord import Embed, Colour
from discord.ext import commands
from discord.ui import View, Button

# ── Логирование ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("joke_bot")

# ── Конфиг из env ────────────────────────────────────────────
TOKEN = os.environ["DISCORD_BOT_TOKEN"]
API_BASE = os.environ.get("API_BASE", "http://localhost:8000").rstrip("/")

# ── Цвет брендинга ───────────────────────────────────────────
PURPLE = Colour(0x7B2FF7)

# ── Bot setup ────────────────────────────────────────────────
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ── Хелперы API ──────────────────────────────────────────────
def api_get(path: str, params: dict | None = None, timeout: int = 10):
    """GET-запрос к API. Возвращает JSON или None."""
    url = f"{API_BASE}{path}"
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        log.error("API GET %s failed: %s", url, exc)
        return None


def api_post(path: str, json: dict | None = None, timeout: int = 10):
    """POST-запрос к API. Возвращает JSON или None."""
    url = f"{API_BASE}{path}"
    try:
        r = requests.post(url, json=json, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        log.error("API POST %s failed: %s", url, exc)
        return None


def joke_embed(data: dict) -> Embed:
    """Создать Embed для шутки."""
    text = data.get("text") or data.get("joke") or data.get("content") or "😅 Не удалось загрузить текст"
    category = data.get("category") or data.get("tags") or ""
    rating = data.get("rating") or data.get("score") or 0
    joke_id = data.get("id", "?")

    embed = Embed(
        title="😂 Анекдот в Тему",
        description=text,
        colour=PURPLE,
    )
    if category:
        embed.add_field(name="📂 Категория", value=str(category), inline=True)
    embed.add_field(name="⭐ Рейтинг", value=f"**{rating}**", inline=True)
    embed.set_footer(text=f"ID: {joke_id}")
    return embed


# ── Views / Кнопки ──────────────────────────────────────────
class JokeView(View):
    """Кнопки под сообщением с шуткой."""

    def __init__(self, joke_id, category: str | None = None, topic: str | None = None):
        super().__init__(timeout=120)
        self.joke_id = joke_id
        self.category = category
        self.topic = topic

    @Button(label="🔀 Ещё", style=discord.ButtonStyle.secondary, emoji="🔀")
    async def btn_more(self, interaction: discord.Interaction, _button: Button):
        """Показать ещё одну шутку."""
        if self.topic:
            data = api_get("/api/jokes/context", params={"q": self.topic})
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

    @Button(label="⭐ Оценить", style=discord.ButtonStyle.primary, emoji="⭐")
    async def btn_rate(self, interaction: discord.Interaction, _button: Button):
        """Поставить +1 к рейтингу."""
        result = api_post(f"/api/joke/{self.joke_id}/rate", json={"score": 1})
        if result and result.get("ok"):
            await interaction.response.send_message("⭐ Спасибо за оценку!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Не удалось оценить.", ephemeral=True)

    @Button(label="🗑 Удалить", style=discord.ButtonStyle.danger, emoji="🗑")
    async def btn_delete(self, interaction: discord.Interaction, _button: Button):
        """Удалить сообщение с шуткой."""
        await interaction.message.delete()


# ── Slash-команды ────────────────────────────────────────────
@bot.slash_command(name="joke", description="Получить анекдот")
async def cmd_joke(
    interaction: discord.Interaction,
    topic: str = commands.Param(
        default=None,
        description="Тема / контекст для подбора анекдота",
    ),
):
    """Случайная шутка или шутка по теме."""
    if topic:
        data = api_get("/api/jokes/context", params={"q": topic})
    else:
        data = api_get("/api/joke/random")

    if not data:
        await interaction.response.send_message("⚠️ Сервис временно недоступен.", ephemeral=True)
        return

    embed = joke_embed(data)
    joke_id = data.get("id", 0)
    view = JokeView(joke_id, topic=topic)
    await interaction.response.send_message(embed=embed, view=view)


@bot.slash_command(name="top", description="Топ-5 анекдотов по рейтингу")
async def cmd_top(interaction: discord.Interaction):
    """Показать 5 лучших шуток."""
    data = api_get("/api/jokes/social/top", params={"limit": 5})
    if not data or not isinstance(data, list):
        await interaction.response.send_message("⚠️ Не удалось загрузить топ.", ephemeral=True)
        return

    embed = Embed(title="🏆 Топ-5 Анекдотов", colour=PURPLE)
    for i, joke in enumerate(data[:5], start=1):
        text = (joke.get("text") or joke.get("joke") or "")[:200]
        rating = joke.get("rating") or joke.get("score") or 0
        embed.add_field(name=f"#{i}  ⭐ {rating}", value=text, inline=False)

    await interaction.response.send_message(embed=embed)


@bot.slash_command(name="stats", description="Статистика сервиса")
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


@bot.slash_command(name="categories", description="Список всех категорий")
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


@bot.slash_command(name="cat", description="Анекдот из конкретной категории")
async def cmd_cat(
    interaction: discord.Interaction,
    name: str = commands.Param(description="Название категории"),
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


# ── Запуск ───────────────────────────────────────────────────
@bot.event
async def on_ready():
    log.info("Бот %s запущен (%s)", bot.user, bot.user.id)


if __name__ == "__main__":
    bot.run(TOKEN)
