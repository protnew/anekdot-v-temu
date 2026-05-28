"""Анекдот в тему — AI-powered contextual joke app v3.0
- TF-IDF semantic search
- OpenAI LLM joke generation  
- 506+ jokes, 20 categories
- SQLite storage
- User CRUD, analytics, social, personalization
- PWA, multi-language
"""
import json, os, random, hashlib, time
from pathlib import Path
from functools import lru_cache
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="Анекдот в тему", version="3.1.0")

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
JOKES_FILE = DATA_DIR / "jokes_db.json"
FAVORITES_FILE = DATA_DIR / "favorites.json"
HISTORY_FILE = DATA_DIR / "history.json"

# ============================================================
# Data Loading (with in-memory cache for speed)
# ============================================================
_jokes_cache = None
_jokes_cache_mtime = 0

def load_jokes():
    global _jokes_cache, _jokes_cache_mtime
    mtime = JOKES_FILE.stat().st_mtime if JOKES_FILE.exists() else 0
    if _jokes_cache is not None and mtime == _jokes_cache_mtime:
        return _jokes_cache
    with open(JOKES_FILE, "r", encoding="utf-8") as f:
        _jokes_cache = json.load(f)
    _jokes_cache_mtime = mtime
    return _jokes_cache

def _invalidate_jokes_cache():
    global _jokes_cache
    _jokes_cache = None

# Periodic save for ratings (don't block API responses)
_pending_rating_save = False
_last_save_time = 0

def _schedule_rating_save():
    """Mark that ratings need to be saved. Actual save happens on next load or shutdown."""
    global _pending_rating_save, _last_save_time
    _pending_rating_save = True

@app.on_event("shutdown")
async def _save_on_shutdown():
    """Save pending ratings when server shuts down."""
    global _pending_rating_save, _jokes_cache
    if _pending_rating_save and _jokes_cache is not None:
        save_json(JOKES_FILE, _jokes_cache)
        print("💾 Ratings saved to disk on shutdown")

@app.on_event("startup")
async def _start_periodic_flush():
    """Background task: flush ratings to disk every 60 seconds."""
    import asyncio
    async def _flush_loop():
        global _pending_rating_save, _last_save_time
        while True:
            await asyncio.sleep(60)
            if _pending_rating_save and _jokes_cache is not None:
                try:
                    save_json(JOKES_FILE, _jokes_cache)
                    _pending_rating_save = False
                    _last_save_time = time.time()
                    print("💾 Periodic rating flush OK")
                except Exception as e:
                    print(f"⚠️ Rating flush error: {e}")
    asyncio.create_task(_flush_loop())

def load_json(path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_all_jokes():
    db = load_jokes()
    jokes = []
    for category, items in db.items():
        for joke in items:
            jokes.append({**joke, "category": category})
    return jokes

# ============================================================
# English Jokes (for multi-language support)
# ============================================================
EN_JOKES = [
    {"id": 8001, "text": "Why do programmers prefer dark mode? Because light attracts bugs.", "rating": 4.6, "tags": ["programming", "dark-mode"], "category": "it"},
    {"id": 8002, "text": "I told my wife she was drawing her eyebrows too high. She looked surprised.", "rating": 4.4, "tags": ["wife", "eyebrows"], "category": "family"},
    {"id": 8003, "text": "Why don't scientists trust atoms? Because they make up everything.", "rating": 4.5, "tags": ["science", "atoms"], "category": "science"},
    {"id": 8004, "text": "I asked the librarian if they had books about paranoia. She whispered, 'They're right behind you.'", "rating": 4.3, "tags": ["library", "paranoia"], "category": "misc"},
    {"id": 8005, "text": "Why did the scarecrow win an award? He was outstanding in his field.", "rating": 4.2, "tags": ["scarecrow", "pun"], "category": "misc"},
    {"id": 8006, "text": "Parallel lines have so much in common. It's a shame they'll never meet.", "rating": 4.4, "tags": ["math", "geometry"], "category": "science"},
    {"id": 8007, "text": "I'm reading a book about anti-gravity. It's impossible to put down.", "rating": 4.3, "tags": ["gravity", "reading"], "category": "science"},
    {"id": 8008, "text": "What do you call a fake noodle? An impasta.", "rating": 4.1, "tags": ["food", "pun"], "category": "food"},
    {"id": 8009, "text": "ChatGPT walks into a bar. The bartender says, 'We don't serve your type here.' ChatGPT says, 'That's fine, I'll generate my own drinks.'", "rating": 4.7, "tags": ["ai", "chatgpt"], "category": "ai"},
    {"id": 8010, "text": "I used to hate facial hair, but then it grew on me.", "rating": 4.2, "tags": ["beard", "pun"], "category": "misc"},
    {"id": 8011, "text": "The future, the present, and the past walked into a bar. Things got tense.", "rating": 4.3, "tags": ["time", "grammar"], "category": "misc"},
    {"id": 8012, "text": "Why do Java developers wear glasses? Because they can't C#.", "rating": 4.5, "tags": ["java", "programming"], "category": "it"},
    {"id": 8013, "text": "My boss told me to have a good day, so I went home.", "rating": 4.6, "tags": ["boss", "work"], "category": "work"},
    {"id": 8014, "text": "I told my computer I needed a break. Now it won't stop sending me KitKat ads.", "rating": 4.2, "tags": ["computer", "ads"], "category": "it"},
    {"id": 8015, "text": "A SQL query walks into a bar, sees two tables, and asks: 'Can I join you?'", "rating": 4.5, "tags": ["sql", "database"], "category": "it"},
]


# ============================================================
# TF-IDF Semantic Search Engine
# ============================================================
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SemanticSearchEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,
        )
        self.jokes = []
        self.tfidf_matrix = None
        self._dirty = False
        self._build_index()

    def _build_index(self):
        self.jokes = get_all_jokes()
        # Include EN_JOKES in search index
        self.jokes.extend([{**j, "category": f"en_{j.get('category', 'misc')}"} for j in EN_JOKES])
        if not self.jokes:
            return
        # Combine text + tags + category for richer matching
        documents = []
        for j in self.jokes:
            tags_text = " ".join(j.get("tags", []))
            doc = f"{j['text']} {j['category']} {tags_text}"
            documents.append(doc)
        self.tfidf_matrix = self.vectorizer.fit_transform(documents)

    def search(self, query: str, top_k: int = 10, min_score: float = 0.01) -> List[dict]:
        # Lazy rebuild if index is stale
        if self._dirty:
            self._build_index()
            self._dirty = False
        if self.tfidf_matrix is None or not self.jokes:
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Get top results above minimum score
        top_indices = np.argsort(scores)[::-1][:top_k * 3]
        results = []
        for idx in top_indices:
            if scores[idx] < min_score:
                break
            joke = self.jokes[idx].copy()
            joke["semantic_score"] = round(float(scores[idx]), 4)
            results.append(joke)
        
        return results[:top_k]

    def get_stats(self):
        return {
            "indexed_jokes": len(self.jokes),
            "vocabulary_size": len(self.vectorizer.vocabulary_) if self.vectorizer.vocabulary_ else 0,
        }


# Build search engine on startup
print("🔍 Building semantic index...")
search_engine = SemanticSearchEngine()
print(f"✅ Indexed {len(search_engine.jokes)} jokes, vocab size: {search_engine.get_stats()['vocabulary_size']}")

# ============================================================
# Keyword Map (fallback + category boosting)
# ============================================================
KEYWORD_MAP = {
    "работа": ["работа", "работать", "зарплата", "начальник", "коллега", "офис", "карьера", "должность", "премия", "совещание", "босс", "подчинённый", "резюме", "собеседование", "увольнение", "отпуск", "дедлайн", "проект", "переработ"],
    "айти": ["программист", "код", "айти", "it", "python", "javascript", "git", "сервер", "баг", "devops", "qa", "тестировщик", "разработчик", "backend", "frontend", "sql", "linux", "девопс", "джуниор", "сеньор", "прод", "рефакторинг", "документация", "npm", "docker", "kubernetes", "микросервис", "legacy", "тип", "компиля", "фреймворк"],
    "деньги": ["деньги", "зарплата", "банк", "кредит", "налог", "рубль", "доллар", "евро", "инвестиции", "крипта", "бизнес", "экономия", "покупк", "цена", "стоимость", "бюджет", "ипотека", "бухгалтер", "доход", "расход", "накоп", "богат", "бедн", "скидк", "акция", "долг"],
    "семья": ["семья", "жена", "муж", "мама", "папа", "бабушка", "дети", "ребёнок", "ребенок", "свадьба", "брак", "тёща", "зять", "свекровь", "дом", "домашний", "муж", "дочка", "сын", "дедушка"],
    "политика": ["политик", "выборы", "президент", "министр", "депутат", "государство", "правительств", "закон", "дума", "референдум", "партия", "власть", "налог"],
    "здоровье": ["здоровье", "врач", "больница", "болезнь", "диета", "фитнес", "похудеть", "лекарств", "температур", "ковид", "прививка", "анализ", "спортзал", "тренер", "витамин", "зож", "йога"],
    "путешествия": ["путешеств", "тур", "отель", "самолёт", "самолет", "поезд", "отпуск", "море", "курорт", "багаж", "виза", "паспорт", "перелёт", "аэропорт", "чемодан"],
    "еда": ["еда", "ресторан", "готовить", "рецепт", "обед", "завтрак", "ужин", "повар", "официант", "меню", "вкусно", "кафе", "пицца", "торт", "суп", "борщ", "кофе", "чай"],
    "наука": ["наука", "учёный", "ученый", "физика", "химия", "биология", "эксперимент", "лаборатория", "теория", "ньютон", "эйнштейн", "формул", "атом", "электрон", "гравитаци", "математик"],
    "спорт": ["спорт", "футбол", "хоккей", "матч", "гол", "тренер", "чемпионат", "олимпиад", "шахматы", "бег", "тренировк", "марафон", "зал", "кроссовк"],
    "образование": ["школа", "университет", "студент", "учитель", "преподаватель", "экзамен", "урок", "учёба", "учеба", "оценка", "диплом", "вуз", "курсы", "ученик", "школьник", "курсовая", "декан", "ректор", "перемен"],
    "отношения": ["любовь", "отношения", "парень", "девушка", "свидание", "романтика", "расставание", "знакомство", "свадьба", "цветы", "поцелуй", "измен"],
    "коронавирус": ["ковид", "коронавирус", "пандемия", "маска", "удалёнк", "удаленк", "зум", "zoom", "карантин", "изоляция", "антисепт", "вакцин"],
    "искусственный интеллект": ["ии", "ai", "нейросет", "chatgpt", "gpt", "искусствен", "машинн", "обучен", "робот", "модел", "промпт", "deep learning", "llm", "openai", "copilot", "agile"],
    "друзья": ["друг", "подруга", "дружба", "долг", "одолжить", "встреча", "компания", "приятель", "товарищ"],
    "котики": ["кот", "кошк", "котик", "мяу", "мурлык", "кис", "рыбка", "аквариум", "котёнок"],
    "авто": ["авто", "машин", "водител", "дорог", "пробк", "бензин", "заправк", "парковк", "гаи", "скорост", "навигатор", "ремонт", "механик", "руль"],
    "магазины": ["магазин", "покуп", "касс", "скидк", "акция", "ценник", "прайс", "чек", "товар", "супермаркет", "молл", "бутик"],
    "дети": ["ребёнок", "ребенок", "детский", "детсад", "школьник", "младенец", "малыш", "подросток", "воспитател", "няня", "урок"],
    "реклама": ["реклам", "маркетинг", "бренд", "промо", "таргет", "баннер", "спам", "инфлюенсер", "блогер", "подпис"],
}

def find_matching_categories(text: str) -> List[str]:
    text_lower = text.lower()
    scores = {}
    for category, keywords in KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score
    return [cat for cat, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]

# ============================================================
# LLM Integration (OpenAI)
# ============================================================
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Check for API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
openai_client = None

def get_openai_client():
    global openai_client
    if OPENAI_API_KEY and OPENAI_AVAILABLE:
        if openai_client is None:
            openai_client = OpenAI(api_key=OPENAI_API_KEY)
        return openai_client
    return None

def generate_joke_with_llm(context: str) -> Optional[str]:
    """Generate a joke using OpenAI GPT model."""
    client = get_openai_client()
    if not client:
        return None
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты — профессиональный автор анекдотов. Генерируй один короткий смешной анекдот на русском языке по заданной теме. Анекдот должен быть оригинальным, не использовать мат, и быть в стиле классического русского анекдота. Отвечай ТОЛЬКО текстом анекдота, без пояснений."},
                {"role": "user", "content": f"Придумай анекдот на тему: {context}"}
            ],
            max_tokens=300,
            temperature=0.9,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM generation error: {e}")
        return None

# ============================================================
# Models
# ============================================================
class JokeRequest(BaseModel):
    text: str
    count: int = 3
    category: Optional[str] = None
    
    def validate_text(self):
        if not self.text or not self.text.strip():
            raise HTTPException(status_code=400, detail="text не может быть пустым")
        if len(self.text) > 5000:
            raise HTTPException(status_code=400, detail="text слишком длинный (макс 5000 символов)")
        return self.text.strip()

class FavoriteRequest(BaseModel):
    joke_id: int
    user_id: str = "default"

class RatingRequest(BaseModel):
    joke_id: int
    rating: float
    
    def validate_rating(self):
        if self.rating < 1 or self.rating > 5:
            raise HTTPException(status_code=400, detail="rating должен быть от 1 до 5")
        return min(max(self.rating, 1.0), 5.0)

# ============================================================
# Routes
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = BASE_DIR / "static" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

@app.get("/logs", response_class=HTMLResponse)
async def logs_page():
    html_path = BASE_DIR / "static" / "logs.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

@app.get("/api/categories")
async def get_categories():
    db = load_jokes()
    return {cat: len(jokes) for cat, jokes in db.items()}

@app.get("/api/jokes")
async def get_jokes(
    category: Optional[str] = Query(None),
    count: int = Query(5, ge=1, le=20),
    randomize: bool = Query(True)
):
    all_jokes = get_all_jokes()
    if category:
        jokes = [j for j in all_jokes if j["category"] == category]
    else:
        jokes = all_jokes
    
    if randomize:
        jokes = random.sample(jokes, min(count, len(jokes)))
    else:
        jokes = jokes[:count]
    
    return {"jokes": jokes, "total": len(jokes)}

@app.get("/api/jokes/search")
async def search_jokes(q: str = Query(..., min_length=2)):
    """Full-text search using TF-IDF semantic search."""
    results = search_engine.search(q, top_k=20)
    return {"jokes": results, "total": len(results)}

@app.post("/api/jokes/context")
async def contextual_joke(request: JokeRequest):
    """Get contextually relevant jokes using semantic search + keyword boosting."""
    request.validate_text()
    # Step 1: Semantic search
    semantic_results = search_engine.search(request.text, top_k=30)
    
    # Step 2: Keyword matching for category boosting
    matching_cats = find_matching_categories(request.text)
    
    # Step 3: Combine scores
    if matching_cats:
        for joke in semantic_results:
            if joke["category"] == matching_cats[0]:
                joke["semantic_score"] = joke.get("semantic_score", 0) * 1.5
            elif joke["category"] in matching_cats:
                joke["semantic_score"] = joke.get("semantic_score", 0) * 1.3
    
    # Step 4: If semantic search found nothing, fall back to keyword-only
    if not semantic_results:
        all_jokes = get_all_jokes()
        if matching_cats:
            pool = [j for j in all_jokes if j["category"] in matching_cats]
        else:
            pool = all_jokes
        pool_sorted = sorted(pool, key=lambda x: x.get("rating", 0), reverse=True)
        semantic_results = pool_sorted[:request.count]
        for j in semantic_results:
            j["semantic_score"] = 0.0
    
    # Sort by combined score
    semantic_results.sort(key=lambda x: x.get("semantic_score", 0), reverse=True)
    
    # Pick from top candidates with some randomization
    top_candidates = semantic_results[:request.count * 3]
    selected = random.sample(top_candidates, min(request.count, len(top_candidates)))
    
    # Save to history
    history = load_json(HISTORY_FILE, [])
    for joke in selected:
        history.append({
            "joke_id": joke["id"],
            "context": request.text,
            "category": joke["category"],
            "score": joke.get("semantic_score", 0)
        })
    save_json(HISTORY_FILE, history[-100:])
    
    return {
        "jokes": selected,
        "matched_categories": matching_cats,
        "context": request.text,
        "search_method": "semantic"
    }

@app.post("/api/jokes/generate")
async def generate_joke(request: JokeRequest):
    """Generate a new joke using LLM (OpenAI) or template fallback."""
    request.validate_text()
    matching_cats = find_matching_categories(request.text)
    
    # Try LLM first
    llm_joke = generate_joke_with_llm(request.text)
    
    if llm_joke:
        return {
            "joke": {
                "id": int(time.time() * 1000) % 100000 + random.randint(1, 999),
                "text": llm_joke,
                "rating": 4.5,
                "tags": matching_cats[:3] + ["ai-generated", "llm"],
                "category": matching_cats[0] if matching_cats else "разное",
                "generated": True,
                "generator": "llm"
            },
            "matched_categories": matching_cats
        }
    
    # Fallback: template-based generation
    all_jokes = get_all_jokes()
    if matching_cats:
        templates = [j for j in all_jokes if j["category"] in matching_cats]
    else:
        templates = all_jokes
    
    template = random.choice(templates if templates else all_jokes)
    
    return {
        "joke": {
            "id": int(time.time() * 1000) % 100000 + random.randint(1, 999),
            "text": f"[AI-вариация по теме \"{matching_cats[0] if matching_cats else 'жизнь'}\"]\n{template['text']}",
            "rating": round(template.get("rating", 4.0) + random.uniform(-0.5, 0.5), 1),
            "tags": template.get("tags", []) + ["ai-generated", "template"],
            "category": template["category"],
            "generated": True,
            "generator": "template"
        },
        "matched_categories": matching_cats
    }

@app.post("/api/favorites")
async def add_favorite(request: FavoriteRequest):
    all_favs = load_json(FAVORITES_FILE, {})
    user_favs = all_favs.get(request.user_id, [])
    if request.joke_id not in user_favs:
        user_favs.append(request.joke_id)
    all_favs[request.user_id] = user_favs
    save_json(FAVORITES_FILE, all_favs)
    return {"favorites": user_favs}

@app.delete("/api/favorites/{joke_id}")
async def remove_favorite(joke_id: int, user_id: str = "default"):
    all_favs = load_json(FAVORITES_FILE, {})
    user_favs = all_favs.get(user_id, [])
    if joke_id in user_favs:
        user_favs.remove(joke_id)
    all_favs[user_id] = user_favs
    save_json(FAVORITES_FILE, all_favs)
    return {"favorites": user_favs}

@app.get("/api/favorites")
async def get_favorites(user_id: str = "default"):
    all_favs = load_json(FAVORITES_FILE, {})
    favorites = all_favs.get(user_id, [])
    all_jokes = get_all_jokes()
    fav_jokes = [j for j in all_jokes if j["id"] in favorites]
    return {"jokes": fav_jokes}

@app.post("/api/rate")
async def rate_joke(request: RatingRequest):
    clamped = request.validate_rating()
    db = load_jokes()  # Uses cache, fast after first call
    for category, jokes in db.items():
        for joke in jokes:
            if joke["id"] == request.joke_id:
                old = joke.get("rating", 4.0)
                new = round((old + clamped) / 2, 1)
                joke["rating"] = min(new, 5.0)  # Never exceed 5.0
                # Schedule save — don't block response
                _schedule_rating_save()
                search_engine._dirty = True
                return {"new_rating": joke["rating"]}
    raise HTTPException(status_code=404, detail="Joke not found")

@app.get("/api/joke/random")
async def random_joke():
    return random.choice(search_engine.jokes)


# ============================================================
# #24: SQLite Storage (optional — keep JSON as primary, add SQLite mirror)
# ============================================================
import sqlite3

DB_PATH = DATA_DIR / "jokes.db"

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jokes (
            id INTEGER PRIMARY KEY,
            category TEXT NOT NULL,
            text TEXT NOT NULL,
            rating REAL DEFAULT 4.0,
            tags TEXT DEFAULT '',
            likes INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_jokes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'anonymous',
            category TEXT NOT NULL,
            text TEXT NOT NULL,
            rating REAL DEFAULT 4.0,
            tags TEXT DEFAULT '',
            approved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            category TEXT,
            joke_id INTEGER,
            query TEXT,
            user_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_prefs (
            user_hash TEXT PRIMARY KEY,
            liked_categories TEXT DEFAULT '',
            disliked_categories TEXT DEFAULT '',
            request_count INTEGER DEFAULT 0,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

init_db()

# ============================================================
# #25: User Jokes CRUD
# ============================================================
class UserJokeRequest(BaseModel):
    category: str
    text: str
    tags: List[str] = []
    
    def validate(self):
        if not self.category or not self.category.strip():
            raise HTTPException(status_code=400, detail="category не может быть пустым")
        if not self.text or len(self.text.strip()) < 10:
            raise HTTPException(status_code=400, detail="text слишком короткий (мин 10 символов)")
        if len(self.text) > 5000:
            raise HTTPException(status_code=400, detail="text слишком длинный (макс 5000 символов)")
        return True

@app.post("/api/user-jokes")
async def create_user_joke(req: UserJokeRequest):
    """Add a user-submitted joke."""
    req.validate()
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO user_jokes (category, text, tags) VALUES (?, ?, ?)",
        (req.category, req.text, json.dumps(req.tags, ensure_ascii=False))
    )
    conn.commit()
    joke_id = cur.lastrowid
    conn.close()
    return {"id": joke_id, "status": "pending_approval"}

@app.get("/api/user-jokes")
async def list_user_jokes(approved: int = Query(0)):
    """List user-submitted jokes."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM user_jokes WHERE approved = ? ORDER BY created_at DESC LIMIT 50", (approved,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        # Parse tags from JSON string back to list
        if isinstance(d.get("tags"), str) and d["tags"]:
            try:
                d["tags"] = json.loads(d["tags"])
            except (json.JSONDecodeError, TypeError):
                d["tags"] = [d["tags"]]
        result.append(d)
    return {"jokes": result}

@app.delete("/api/user-jokes/{joke_id}")
async def delete_user_joke(joke_id: int):
    conn = get_db()
    conn.execute("DELETE FROM user_jokes WHERE id = ?", (joke_id,))
    conn.commit()
    conn.close()
    return {"deleted": True}

# ============================================================
# #26: Personalization
# ============================================================
@app.post("/api/personalize/{user_hash}")
async def update_preferences(user_hash: str, liked_cat: str = "", disliked_cat: str = ""):
    """Update user preferences."""
    conn = get_db()
    conn.execute("""
        INSERT INTO user_prefs (user_hash, liked_categories, disliked_categories, request_count) 
        VALUES (?, ?, ?, 1)
        ON CONFLICT(user_hash) DO UPDATE SET 
            liked_categories = ?, disliked_categories = ?, 
            request_count = request_count + 1, last_seen = CURRENT_TIMESTAMP
    """, (user_hash, liked_cat, disliked_cat, liked_cat, disliked_cat))
    conn.commit()
    conn.close()
    return {"status": "updated"}

@app.get("/api/personalize/{user_hash}")
async def get_personalized(user_hash: str, count: int = Query(3, ge=1, le=10)):
    """Get personalized joke recommendations."""
    conn = get_db()
    row = conn.execute("SELECT * FROM user_prefs WHERE user_hash = ?", (user_hash,)).fetchone()
    conn.close()
    
    all_jokes = get_all_jokes()
    if row:
        try:
            liked = json.loads(row["liked_categories"]) if row["liked_categories"] else []
        except (json.JSONDecodeError, TypeError):
            liked = [row["liked_categories"]] if row["liked_categories"] else []
        try:
            disliked = json.loads(row["disliked_categories"]) if row["disliked_categories"] else []
        except (json.JSONDecodeError, TypeError):
            disliked = [row["disliked_categories"]] if row["disliked_categories"] else []
        # Filter out disliked, boost liked
        pool = [j for j in all_jokes if j["category"] not in disliked]
        if liked:
            pool.sort(key=lambda j: (1.5 if j["category"] in liked else 1.0) * j.get("rating", 4.0), reverse=True)
        else:
            pool.sort(key=lambda j: j.get("rating", 4.0), reverse=True)
    else:
        pool = sorted(all_jokes, key=lambda j: j.get("rating", 4.0), reverse=True)
    
    return {"jokes": pool[:count]}

# ============================================================
# #30: Social Functions (likes, top)
# ============================================================
@app.post("/api/jokes/{joke_id}/like")
async def like_joke(joke_id: int):
    """Like a joke."""
    conn = get_db()
    # Check if in SQLite
    row = conn.execute("SELECT * FROM jokes WHERE id = ?", (joke_id,)).fetchone()
    if row:
        conn.execute("UPDATE jokes SET likes = likes + 1 WHERE id = ?", (joke_id,))
    else:
        # Insert from JSON db
        all_jokes = get_all_jokes()
        joke = next((j for j in all_jokes if j["id"] == joke_id), None)
        if joke:
            conn.execute("INSERT INTO jokes (id, category, text, rating, tags, likes) VALUES (?,?,?,?,?,1)",
                        (joke["id"], joke["category"], joke["text"], joke.get("rating", 4.0), json.dumps(joke.get("tags",[]))))
        else:
            conn.close()
            raise HTTPException(404, "Joke not found")
    conn.commit()
    conn.close()
    
    # Track analytics
    track_event("like", joke_id=joke_id)
    return {"liked": True}

@app.get("/api/jokes/social/top")
async def top_jokes(period: str = Query("day"), count: int = Query(10, ge=1, le=50)):
    """Get top jokes by likes/rating."""
    all_jokes = get_all_jokes()
    # Sort by rating (likes would come from DB in production)
    sorted_jokes = sorted(all_jokes, key=lambda j: j.get("rating", 0), reverse=True)
    return {"jokes": sorted_jokes[:count], "period": period}

# ============================================================
# #31: Monetization endpoints (stubs)
# ============================================================
@app.get("/api/monetization/ad")
async def get_ad():
    """Get an ad to display (stub)."""
    return {
        "ad": {
            "type": "banner",
            "text": "📢 Хочешь больше анекдотов? Попробуй Premium!",
            "link": "#premium",
            "show": True
        }
    }

@app.get("/api/monetization/premium")
async def premium_status(user_hash: str = ""):
    """Check premium status."""
    return {
        "is_premium": False,
        "features": ["unlimited_generation", "no_ads", "exclusive_jokes"],
        "price": "199₽/мес"
    }

# ============================================================
# #33: Analytics
# ============================================================
def track_event(event_type: str, category: str = None, joke_id: int = None, query: str = None, user_hash: str = None):
    """Track an analytics event."""
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO analytics (event_type, category, joke_id, query, user_hash) VALUES (?,?,?,?,?)",
            (event_type, category, joke_id, query, user_hash)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # Analytics shouldn't break the app

@app.get("/api/analytics/popular")
async def popular_topics(days: int = Query(7, ge=1, le=30)):
    """Get most popular topics/queries."""
    conn = get_db()
    rows = conn.execute("""
        SELECT category, COUNT(*) as cnt 
        FROM analytics 
        WHERE event_type = 'search' 
        AND created_at >= datetime('now', ? || ' days')
        GROUP BY category 
        ORDER BY cnt DESC 
        LIMIT 20
    """, (f"-{days}",)).fetchall()
    conn.close()
    return {"popular": [dict(r) for r in rows], "period_days": days}

@app.get("/api/analytics/stats")
async def analytics_stats():
    """Get overall analytics."""
    conn = get_db()
    total_events = conn.execute("SELECT COUNT(*) FROM analytics").fetchone()[0]
    total_users = conn.execute("SELECT COUNT(DISTINCT user_hash) FROM analytics WHERE user_hash IS NOT NULL").fetchone()[0]
    top_cats = conn.execute("""
        SELECT category, COUNT(*) as cnt FROM analytics 
        WHERE category IS NOT NULL GROUP BY category ORDER BY cnt DESC LIMIT 10
    """).fetchall()
    conn.close()
    return {
        "total_events": total_events,
        "unique_users": total_users,
        "top_categories": [dict(r) for r in top_cats]
    }

# ============================================================
# #28: Multi-language (English jokes)
# ============================================================

@app.get("/api/jokes/en")
async def english_jokes(count: int = Query(5, ge=1, le=15)):
    """Get English-language jokes."""
    return {"jokes": random.sample(EN_JOKES, min(count, len(EN_JOKES))), "total": len(EN_JOKES)}

# ============================================================
# #34: PWA Support
# ============================================================
@app.get("/sw.js", response_class=HTMLResponse)
async def service_worker():
    sw = """
const CACHE_NAME = 'anekdot-v3';
const URLS_TO_CACHE = ['/', '/static/index.html'];

self.addEventListener('install', e => {
    e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(URLS_TO_CACHE)));
    self.skipWaiting();
});

self.addEventListener('fetch', e => {
    if (e.request.url.includes('/api/')) return; // Don't cache API
    e.respondWith(
        caches.match(e.request).then(r => r || fetch(e.request))
    );
});
"""
    return HTMLResponse(content=sw, media_type="application/javascript")

@app.get("/manifest.json")
async def web_manifest():
    return {
        "name": "Анекдот в тему",
        "short_name": "Анекдот",
        "description": "AI-анекдоты по контексту",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f0f1a",
        "theme_color": "#e94560",
        "icons": [
            {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    }


# ============================================================
# #22: Yandex Alice skill webhook
# ============================================================
@app.post("/api/alice")
async def alice_webhook(request: dict):
    """Webhook for Yandex Alice skill."""
    req = request.get("request", {})
    command = req.get("command", "").lower()
    original_utterance = req.get("original_utterance", "")
    
    # Find joke
    if not command or command in ["помощь", "что ты умеешь"]:
        text = "Я подбираю анекдоты по теме! Скажите, например: «расскажи анекдот про работу» или «шутка про котиков»."
    elif "случайный" in command or "любой" in command:
        joke = random.choice(search_engine.jokes)
        text = joke["text"]
    else:
        data = api_post("/api/jokes/context", {"text": original_utterance, "count": 1})
        if data and data.get("jokes"):
            text = data["jokes"][0]["text"]
        else:
            joke = random.choice(search_engine.jokes)
            text = f"Не нашёл подходящий, но вот: {joke['text']}"
    
    return {
        "response": {
            "text": text,
            "tts": text.replace("\n", ". "),
            "end_session": False
        },
        "version": "1.0"
    }

def api_post(path, data):
    """Internal API call for Alice webhook."""
    import urllib.request
    try:
        req = urllib.request.Request(
            f"http://localhost:8000{path}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"api_post error ({path}): {e}")
        return None


# ============================================================
# #29: Voice endpoints (TTS/STT stubs)
# ============================================================
@app.post("/api/voice/stt")
async def speech_to_text(request: dict):
    """Stub for speech-to-text. Returns text for processing."""
    return {"text": request.get("text", ""), "note": "In production, use Whisper API for real STT"}

@app.post("/api/voice/tts")
async def text_to_speech(request: dict):
    """Stub for text-to-speech. Returns text that would be spoken."""
    text = request.get("text", "")
    return {"text": text, "audio_url": None, "note": "In production, use TTS API for real audio"}


# ============================================================
# Extended Stats
# ============================================================
@app.get("/api/stats")
async def get_stats():
    db = load_jokes()
    all_jokes = get_all_jokes()
    all_favs = load_json(FAVORITES_FILE, {})
    total_favs = sum(len(v) for v in all_favs.values()) if isinstance(all_favs, dict) else len(all_favs)
    history = load_json(HISTORY_FILE, [])
    sem_stats = search_engine.get_stats()
    
    avg_rating = sum(j.get("rating", 0) for j in all_jokes) / len(all_jokes) if all_jokes else 0
    
    return {
        "total_jokes": len(all_jokes),
        "en_jokes": len(EN_JOKES),
        "categories": len(db),
        "favorites_count": total_favs,
        "history_count": len(history),
        "avg_rating": round(avg_rating, 1),
        "vocabulary_size": sem_stats["vocabulary_size"],
        "llm_available": get_openai_client() is not None,
        "features": {
            "semantic_search": True,
            "llm_generation": get_openai_client() is not None,
            "user_crud": True,
            "analytics": True,
            "social": True,
            "personalization": True,
            "multi_language": True,
            "pwa": True,
            "alice_skill": True,
            "voice": False  # stub only
        },
        "version": "3.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("😂 Запуск «Анекдот в тему» v3.0 на http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
