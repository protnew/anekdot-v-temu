"""Анекдот в тему — AI-powered contextual joke app v3.9.0
- TF-IDF semantic search
- whisper.cpp local STT (74MB, 99 langs)
- Silero VAD voice activity detection (300KB)
- 200K jokes, 132 categories, 10 languages
- SQLite storage
- User CRUD, analytics, social, personalization
- PWA, multi-language, moderation
"""
import json, os, random, hashlib, time, subprocess, tempfile, base64, asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from moderation import ProfanityFilter, SpamDetector, ContentModerator


async def _run_subprocess(args, timeout=30):
    """Non-blocking subprocess run."""
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout, stderr
    except asyncio.TimeoutError:
        proc.kill()
        raise TimeoutError(f"Command timed out: {args[0]}")

app = FastAPI(title="Анекдот в тему", version="3.9.0")

# Allow CORS for local development (emulator from file://)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    def search(self, query: str, top_k: int = 10, min_score: float = 0.05) -> List[dict]:
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


# Lazy search engine — don't build TF-IDF index until first search request
# This lets the server start INSTANTLY instead of waiting 60-90 seconds
search_engine = None

def _get_search_engine():
    global search_engine
    if search_engine is None:
        print("🔍 Building semantic index (first request)...")
        search_engine = SemanticSearchEngine()
        print(f"✅ Indexed {len(search_engine.jokes)} jokes, vocab size: {search_engine.get_stats()['vocabulary_size']}")
    return search_engine

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
    # Multilingual keywords - Spanish
    "es_varios": ["espanol", "chiste", "broma", "humor", "gracioso", "divertido"],
    "es_familia": ["familia", "madre", "padre", "hijo", "hija", "esposa", "marido", "abuela"],
    "es_trabajo": ["trabajo", "jefe", "oficina", "empleado", "entrevista", "sueldo", "empresa", "compañero"],
    "es_comida": ["comida", "restaurante", "cocina", "cocinero", "receta", "almuerzo", "cena", "desayuno"],
    "es_tecnologia": ["tecnologia", "programador", "ordenador", "codigo", "internet", "app", "software"],
    "es_animales": ["animal", "perro", "gato", "mascota", "veterinario", "pájaro", "pez"],
    "es_relaciones": ["amor", "novio", "novia", "cita", "pareja", "relacion", "corazon"],
    "es_salud": ["salud", "doctor", "hospital", "enfermedad", "medicina", "dieta", "ejercicio"],
    "es_ninos": ["niño", "escuela", "maestro", "estudiante", "deberes", "colegio"],
    "es_dinero": ["dinero", "banco", "credito", "ahorro", "inversion", "impuesto"],
    # German
    "de_verschiedenes": ["witz", "humor", "lustig", "spass", "deutsch"],
    "de_familie": ["familie", "mutter", "vater", "kind", "frau", "mann", "oma"],
    "de_arbeit": ["arbeit", "chef", "büro", "kollege", "gehalt", "meeting", "firma", "bewerbung"],
    "de_essen": ["essen", "restaurant", "küche", "koch", "rezept", "mittag", "abendessen", "brot"],
    "de_technologie": ["technologie", "programmierer", "computer", "code", "internet", "software"],
    "de_tiere": ["tier", "hund", "katze", "haustier", "vogel", "fisch"],
    "de_beziehungen": ["liebe", "beziehung", "freund", "freundin", "date", "partner"],
    "de_gesundheit": ["gesundheit", "arzt", "krankenhaus", "krankheit", "medizin", "diät", "sport"],
    "de_kinder": ["kind", "schule", "lehrer", "schüler", "hausaufgabe", "unterricht"],
    "de_geld": ["geld", "bank", "kredit", "sparen", "investition", "steuer", "gehalt"],
    # French
    "fr_divers": ["blague", "humour", "drôle", "français"],
    "fr_famille": ["famille", "mère", "père", "enfant", "femme", "mari", "grand-mère"],
    "fr_travail": ["travail", "patron", "bureau", "collègue", "salaire", "réunion", "entreprise"],
    "fr_cuisine": ["cuisine", "restaurant", "chef", "recette", "déjeuner", "dîner", "fromage", "vin"],
    "fr_technologie": ["technologie", "programmeur", "ordinateur", "code", "internet", "logiciel"],
    "fr_animaux": ["animal", "chien", "chat", "oiseau", "poisson"],
    "fr_relations": ["amour", "copain", "copine", "rendez-vous", "couple", "relation"],
    "fr_sante": ["santé", "médecin", "hôpital", "maladie", "médicament", "régime"],
    "fr_enfants": ["enfant", "école", "professeur", "élève", "devoir", "classe"],
    "fr_argent": ["argent", "banque", "crédit", "épargne", "investissement", "impôt"],
    # Portuguese
    "pt_variado": ["piada", "humor", "engraçado", "brasileiro"],
    "pt_familia": ["família", "mãe", "pai", "filho", "esposa", "marido"],
    "pt_trabalho": ["trabalho", "chefe", "escritório", "entrevista", "salário", "empresa"],
    "pt_comida": ["comida", "restaurante", "cozinha", "cozinheiro", "almoço", "jantar", "feijoada"],
    "pt_tecnologia": ["tecnologia", "programador", "computador", "código", "internet"],
    "pt_animais": ["animal", "cachorro", "gato", "papagaio", "peixe"],
    "pt_relacionamento": ["amor", "namorado", "namorada", "casal", "relacionamento"],
    "pt_saude": ["saúde", "médico", "hospital", "doença", "remédio", "dieta"],
    "pt_crianca": ["criança", "escola", "professor", "aluno", "lição"],
    "pt_dinheiro": ["dinheiro", "banco", "crédito", "economia", "investimento"],
    # Chinese
    "zh_misc": ["笑话", "幽默", "搞笑", "段子"],
    "zh_family": ["家庭", "妈妈", "爸爸", "孩子", "老婆", "老公"],
    "zh_work": ["工作", "老板", "同事", "加班", "面试", "工资", "996"],
    "zh_food": ["美食", "餐厅", "做饭", "厨师", "午餐", "晚餐", "火锅"],
    "zh_tech": ["程序员", "代码", "电脑", "互联网", "软件", "bug"],
    "zh_animals": ["动物", "狗", "猫", "宠物", "鱼"],
    "zh_life": ["生活", "日常", "人生"],
    "zh_health": ["健康", "医生", "医院", "锻炼", "减肥"],
    "zh_school": ["学校", "老师", "学生", "考试", "作业"],
    "zh_money": ["钱", "银行", "工资", "投资", "信用卡"],
    # Japanese
    "ja_misc": ["冗談", "ユーモア", "面白い", "笑"],
    "ja_family": ["家族", "お母さん", "お父さん", "子供", "妻", "夫"],
    "ja_work": ["仕事", "上司", "同僚", "残業", "面接", "給料", "サラリーマン"],
    "ja_food": ["食べ物", "レストラン", "料理", "昼ごはん", "晩ごはん", "ラーメン"],
    "ja_tech": ["プログラマー", "コード", "パソコン", "インターネット"],
    "ja_animals": ["動物", "犬", "猫", "ペット", "魚"],
    "ja_life": ["生活", "日常", "人生"],
    "ja_health": ["健康", "医者", "病院", "ダイエット", "運動"],
    "ja_school": ["学校", "先生", "学生", "宿題", "試験"],
    "ja_money": ["お金", "銀行", "給料", "投資", "貯金"],
    # Arabic
    "ar_misc": ["نكتة", "فكاهة", "مضحك", "سخرية"],
    "ar_family": ["عائلة", "أم", "أب", "طفل", "زوجة", "زوج"],
    "ar_work": ["عمل", "مدير", "موظف", "راتب", "مقابلة", "شركة"],
    "ar_food": ["طعام", "مطعم", "طبخ", "غداء", "عشاء"],
    "ar_tech": ["تكنولوجيا", "مبرمج", "حاسوب", "إنترنت", "كود"],
    "ar_animals": ["حيوان", "كلب", "قطة", "حیوان"],
    "ar_life": ["حياة", "يومي", "عيش"],
    "ar_health": ["صحة", "طبيب", "مستشفى", "مرض", "دواء"],
    "ar_school": ["مدرسة", "معلم", "طالب", "امتحان", "واجب"],
    "ar_money": ["مال", "بنك", "راتب", "استثمار", "قرض"],
    # Hindi
    "hi_misc": ["chutkula", "mazak", "hasi", "joke", "funny"],
    "hi_family": ["parivar", "maa", "papa", "baccha", "patni", "pati"],
    "hi_work": ["kaam", "boss", "naukri", "salary", "office", "interview", "company"],
    "hi_food": ["khana", "restaurant", "cooking", "lunch", "dinner", "biryani"],
    "hi_tech": ["programmer", "code", "computer", "internet", "software"],
    "hi_animals": ["janwar", "kutta", "billi", "pet"],
    "hi_life": ["zindagi", "daily", "life"],
    "hi_health": ["sehat", "doctor", "hospital", "bimari", "dawai"],
    "hi_school": ["school", "teacher", "student", "exam", "homework"],
    "hi_money": ["paisa", "bank", "salary", "investment", "loan"],
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
        if self.count < 0:
            raise HTTPException(status_code=400, detail="count не может быть отрицательным")
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

@app.get("/emulator", response_class=HTMLResponse)
async def emulator_page():
    html_path = BASE_DIR / "static" / "emulator.html"
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
async def search_jokes(q: str = Query(..., min_length=2), limit: int = Query(10, ge=1, le=50)):
    """Full-text search using TF-IDF semantic search."""
    results = _get_search_engine().search(q, top_k=limit)
    return {"jokes": results, "total": len(results)}

@app.post("/api/jokes/context")
async def contextual_joke(request: JokeRequest):
    """Get contextually relevant jokes using semantic search + keyword boosting."""
    request.validate_text()
    # Step 1: Semantic search
    semantic_results = _get_search_engine().search(request.text, top_k=30)
    
    # Step 2: Keyword matching for category boosting
    matching_cats = find_matching_categories(request.text)
    
    # Step 3: Combine scores
    if matching_cats:
        for joke in semantic_results:
            if joke["category"] == matching_cats[0]:
                joke["semantic_score"] = joke.get("semantic_score", 0) * 1.5
            elif joke["category"] in matching_cats:
                joke["semantic_score"] = joke.get("semantic_score", 0) * 1.3
    
    # Step 4: Filter out zero-score results (no semantic match)
    semantic_results = [j for j in semantic_results if j.get("semantic_score", 0) > 0.01]
    
    # Step 5: If semantic search found nothing, fall back to keyword-only
    if not semantic_results and matching_cats:
        all_jokes = get_all_jokes()
        pool = [j for j in all_jokes if j["category"] in matching_cats]
        pool_sorted = sorted(pool, key=lambda x: x.get("rating", 0), reverse=True)
        semantic_results = pool_sorted[:request.count]
        for j in semantic_results:
            j["semantic_score"] = 0.3  # keyword fallback score
    
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
    llm_joke = await asyncio.to_thread(generate_joke_with_llm, request.text)
    
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
                # Weighted average with increasing confidence
                votes = joke.get("votes", 1) + 1
                new = round((old * (votes - 1) + clamped) / votes, 1)
                joke["rating"] = min(max(new, 1.0), 5.0)
                joke["votes"] = votes
                # Schedule save — don't block response
                _schedule_rating_save()
                return {"new_rating": joke["rating"], "votes": votes}
    raise HTTPException(status_code=404, detail="Joke not found")

@app.get("/api/joke/random")
async def random_joke(category: Optional[str] = Query(None), lang: Optional[str] = Query(None)):
    # Fast random: pick a random category then a random joke from it
    # No need to load ALL 286K jokes into memory
    db = load_jokes()
    cats = list(db.keys())
    if not cats:
        raise HTTPException(404, "No jokes")
    
    if category and category in db:
        jokes = db[category]
        if jokes:
            j = random.choice(jokes)
            return {**j, "category": category}
    
    # Filter categories by language
    _FOREIGN = ("en_", "es_", "de_", "fr_", "pt_", "zh_", "ja_", "ar_", "hi_")
    if lang == "en":
        cats = [c for c in cats if c.startswith("en_")]
    elif lang and lang != "ru":
        cats = [c for c in cats if c.startswith(f"{lang}_")]
    else:
        # Russian: exclude all foreign-prefixed categories
        cats = [c for c in cats if not c.startswith(_FOREIGN)]
    
    if not cats:
        cats = list(db.keys())
    
    # Pick random category, then random joke
    cat = random.choice(cats)
    jokes = db.get(cat, [])
    if not jokes:
        cat = random.choice(list(db.keys()))
        jokes = db[cat]
    
    if not jokes:
        raise HTTPException(404, "No jokes found")
    
    j = random.choice(jokes)
    return {**j, "category": cat}


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
    try:
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
    finally:
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
    # Moderation check
    mod = _moderator.moderate(req.text)
    if not mod["approved"]:
        raise HTTPException(status_code=422, detail=f"Контент отклонён: {'; '.join(mod['reasons'])}")
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO user_jokes (category, text, tags) VALUES (?, ?, ?)",
            (req.category, req.text, json.dumps(req.tags, ensure_ascii=False))
        )
        conn.commit()
        joke_id = cur.lastrowid
    finally:
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
    try:
        conn.execute("DELETE FROM user_jokes WHERE id = ?", (joke_id,))
        conn.commit()
    finally:
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
    try:
        row = conn.execute("SELECT * FROM user_prefs WHERE user_hash = ?", (user_hash,)).fetchone()
    finally:
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
    try:
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
                raise HTTPException(404, "Joke not found")
        conn.commit()
    finally:
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
    except Exception as e:
        print(f"⚠️ Analytics error: {e}")  # Log instead of silent pass

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
async def english_jokes(count: int = Query(5, ge=1, le=50)):
    """Get English-language jokes from database (en_* categories)."""
    all_jokes = get_all_jokes()
    en = [j for j in all_jokes if j.get("category", "").startswith("en_")]
    if not en:
        en = EN_JOKES  # fallback to hardcoded
    selected = random.sample(en, min(count, len(en)))
    return {"jokes": selected, "total": len(en)}

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
        db = load_jokes()
        cat = random.choice(list(db.keys()))
        joke = random.choice(db[cat])
        text = joke["text"]
    else:
        data = api_post("/api/jokes/context", {"text": original_utterance, "count": 1})
        if data and data.get("jokes"):
            text = data["jokes"][0]["text"]
        else:
            db = load_jokes()
            cat = random.choice(list(db.keys()))
            joke = random.choice(db[cat])
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
    base_url = os.environ.get("BASE_URL", "http://localhost:8000")
    try:
        req = urllib.request.Request(
            f"{base_url}{path}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"api_post error ({path}): {e}")
        return None


# ============================================================
# #29: Voice endpoints — whisper.cpp + Silero VAD
# ============================================================

# Paths for whisper.cpp (set via env or defaults)
WHISPER_CLI = os.environ.get("WHISPER_CLI_PATH", "/usr/local/bin/whisper-cli")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL_PATH", str(BASE_DIR / "docker" / "models" / "ggml-base.bin"))
SILERO_VAD_MODEL = os.environ.get("SILERO_VAD_PATH", str(BASE_DIR / "docker" / "models" / "silero_vad.onnx"))

def _silero_vad_check(wav_path: str, threshold: float = 0.5) -> dict:
    """Check if WAV contains speech using Silero VAD (ONNX) or energy fallback.
    Returns {has_speech: bool, speech_prob: float, duration_sec: float}"""
    try:
        import numpy as np
        import wave
        # Read WAV properly using wave module (handles variable headers)
        with wave.open(wav_path, 'rb') as wf:
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)
            sr = wf.getframerate()
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        duration = float(len(samples) / sr)

        # Try ONNX-based Silero VAD
        try:
            import onnxruntime as ort
            if not os.path.exists(SILERO_VAD_MODEL):
                raise FileNotFoundError(f"Silero VAD model not found: {SILERO_VAD_MODEL}")

            sess = ort.InferenceSession(SILERO_VAD_MODEL)
            input_name = sess.get_inputs()[0].name
            # Silero expects chunks of 512 samples at 16kHz
            chunk_size = 512
            speech_probs = []
            for i in range(0, len(samples) - chunk_size, chunk_size):
                chunk = samples[i:i + chunk_size].reshape(1, -1).astype(np.float32)
                result = sess.run(None, {input_name: chunk})
                # Force python float conversion (avoid numpy scalar issues)
                prob_val = result[0].flatten()[0]
                speech_probs.append(float(np.float64(prob_val)))

            max_prob = float(max(speech_probs)) if speech_probs else 0.0
            return {"has_speech": bool(max_prob >= threshold), "speech_prob": max_prob, "duration_sec": duration}
        except Exception as e:
            # Fallback: simple energy-based VAD
            rms = float(np.sqrt(np.mean(samples ** 2)))
            prob = min(rms * 10.0, 1.0)
            return {"has_speech": bool(prob >= threshold), "speech_prob": prob, "duration_sec": duration, "vad_fallback": str(e)}
    except Exception as e:
        return {"has_speech": True, "speech_prob": -1.0, "duration_sec": 0.0, "error": str(e)}


@app.post("/api/voice/stt")
async def speech_to_text(request: dict):
    """Real speech-to-text using whisper.cpp (local, no API needed).
    Input: {audio_base64: str, format: 'wav'|'webm'|'ogg', language: 'ru'|'en'|...}
    Output: {text: str, language: str, confidence: float, vad: dict}
    """
    audio_b64 = request.get("audio_base64", "")
    audio_format = request.get("format", "wav")
    language = request.get("language", "ru")
    
    if not audio_b64:
        raise HTTPException(status_code=400, detail="audio_base64 is required")
    
    # Validate whisper-cli exists
    use_faster_whisper = False
    if not os.path.exists(WHISPER_CLI) or not os.path.exists(WHISPER_MODEL):
        # Fallback to faster_whisper (Python) on Windows
        try:
            from faster_whisper import WhisperModel
            use_faster_whisper = True
        except ImportError:
            raise HTTPException(status_code=500, detail=f"whisper-cli not found at {WHISPER_CLI} and faster_whisper not installed")
    
    try:
        # Decode base64 → temp WAV file
        audio_bytes = base64.b64decode(audio_b64)
        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        # Convert to 16kHz WAV if needed (whisper.cpp needs PCM WAV)
        wav_path = tmp_path
        if audio_format != "wav":
            wav_path = tmp_path + ".wav"
            await _run_subprocess(["ffmpeg", "-y", "-i", tmp_path, "-ar", "16000", "-ac", "1", "-f", "wav", wav_path], timeout=10)
        
        # Step 1: Silero VAD — check if there's actual speech
        vad_result = _silero_vad_check(wav_path)
        if not vad_result["has_speech"]:
            os.unlink(tmp_path)
            if wav_path != tmp_path:
                os.unlink(wav_path)
            return {"text": "", "language": language, "confidence": 0.0, "vad": vad_result, "note": "No speech detected"}
        
        # Step 2: Transcription
        text = ""
        model_name = ""
        
        if use_faster_whisper:
            # faster_whisper (Python) — works on Windows without compiled binary
            from faster_whisper import WhisperModel
            fw_model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, info = fw_model.transcribe(wav_path, language=language if language != "auto" else None)
            text = " ".join(s.text for s in segments).strip()
            model_name = "faster_whisper base (CPU)"
        else:
            # whisper.cpp (Linux/Docker) — faster, compiled binary
            rc, stdout, stderr = await _run_subprocess([WHISPER_CLI, "-m", WHISPER_MODEL, "-l", language, "-f", wav_path,
                 "--no-timestamps", "-t", "4", "--output-txt"], timeout=30
            )
            text = stdout.decode().strip()
            # Also try to read the .txt file whisper may have created
            txt_path = wav_path + ".txt"
            if os.path.exists(txt_path):
                with open(txt_path) as f:
                    file_text = f.read().strip()
                if len(file_text) > len(text):
                    text = file_text
                os.unlink(txt_path)
            model_name = "whisper.cpp base (74M)"
        
        # Remove common artifacts
        for artifact in ["[BLANK_AUDIO]", "[музыка]", "[ Music ]", "[MUSIC]"]:
            text = text.replace(artifact, "")
        text = text.strip()
        
        # Cleanup temp files
        os.unlink(tmp_path)
        if wav_path != tmp_path:
            os.unlink(wav_path)
        
        return {
            "text": text,
            "language": language,
            "confidence": 0.9 if text else 0.0,
            "vad": vad_result,
            "model": model_name,
            "vad_model": "Energy VAD"
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="whisper timeout (30s)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {str(e)}")


@app.post("/api/voice/stt/file")
async def speech_to_text_file(file: UploadFile = None):
    """Upload audio file for STT. Accepts WAV/MP3/OGG/FLAC. Max 25MB."""
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Read with size limit (25MB max)
    content = await file.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 25MB)")
    
    suffix = Path(file.filename).suffix if file.filename else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Convert to 16kHz WAV
        wav_path = tmp_path + ".wav"
        await _run_subprocess(
            ["ffmpeg", "-y", "-i", tmp_path, "-ar", "16000", "-ac", "1", "-f", "wav", wav_path], timeout=10)
        
        # VAD check
        vad_result = _silero_vad_check(wav_path)
        if not vad_result["has_speech"]:
            for p in [tmp_path, wav_path]:
                if os.path.exists(p): os.unlink(p)
            return {"text": "", "vad": vad_result, "note": "No speech detected"}
        
        # Transcription
        use_fw = not (os.path.exists(WHISPER_CLI) and os.path.exists(WHISPER_MODEL))
        text = ""
        model_used = ""
        
        if use_fw:
            from faster_whisper import WhisperModel
            fw_model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, info = fw_model.transcribe(wav_path)
            text = " ".join(s.text for s in segments).strip()
            model_used = "faster_whisper base (CPU)"
        else:
            rc, stdout, stderr = await _run_subprocess(
                [WHISPER_CLI, "-m", WHISPER_MODEL, "-l", "auto", "-f", wav_path,
                 "--no-timestamps", "-t", "4"], timeout=30
            )
            text = stdout.decode().strip()
            model_used = "whisper.cpp base"
        
        # Cleanup
        for p in [tmp_path, wav_path]:
            if os.path.exists(p): os.unlink(p)
        
        return {"text": text, "vad": vad_result, "model": model_used}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voice/status")
async def voice_status():
    """Check STT + VAD availability (whisper.cpp OR faster_whisper)."""
    whisper_ok = os.path.exists(WHISPER_CLI) and os.path.exists(WHISPER_MODEL)
    fw_ok = False
    if not whisper_ok:
        try:
            from faster_whisper import WhisperModel
            fw_ok = True
        except ImportError:
            pass
    silero_ok = os.path.exists(SILERO_VAD_MODEL)
    onnx_ok = False
    if silero_ok:
        try:
            import onnxruntime
            onnx_ok = True
        except ImportError:
            pass
    
    return {
        "stt_available": whisper_ok or fw_ok,
        "stt_engine": "whisper.cpp" if whisper_ok else ("faster_whisper" if fw_ok else "none"),
        "vad_available": silero_ok,
        "onnx_runtime": onnx_ok,
        "whisper_cli": WHISPER_CLI,
        "whisper_model": WHISPER_MODEL,
        "silero_vad": SILERO_VAD_MODEL,
        "whisper_model_size": f"{os.path.getsize(WHISPER_MODEL) // 1024 // 1024}MB" if os.path.exists(WHISPER_MODEL) else "not found",
        "silero_vad_size": f"{os.path.getsize(SILERO_VAD_MODEL) // 1024}KB" if os.path.exists(SILERO_VAD_MODEL) else "not found",
    }

@app.post("/api/voice/tts")
async def text_to_speech(request: dict):
    """Text-to-speech: converts joke text to MP3 audio via gTTS (Google TTS, free)."""
    text = request.get("text", "")
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    if len(text) > 5000:
        raise HTTPException(status_code=400, detail="text слишком длинный (макс 5000 символов)")
    
    try:
        from gtts import gTTS
        import tempfile, os
        
        # Ограничиваем длину (gTTS лимит ~5000 символов)
        text = text[:2000]
        
        tts = gTTS(text=text, lang='ru', slow=False)
        
        # Сохраняем в data/tts/
        tts_dir = BASE_DIR / "data" / "tts"
        tts_dir.mkdir(parents=True, exist_ok=True)
        
        import hashlib
        fname = hashlib.sha256(text.encode()).hexdigest()[:12] + ".mp3"
        fpath = tts_dir / fname
        
        if not fpath.exists():
            tts.save(str(fpath))
        
        return {
            "text": text,
            "audio_file": f"/data/tts/{fname}",
            "duration_estimate": f"{len(text) // 15} сек",
            "generator": "gTTS (Google TTS, free)"
        }
    except ImportError:
        return {"error": "gTTS not installed. Run: pip install gTTS"}
    except Exception as e:
        return {"error": f"TTS failed: {str(e)}"}




@app.get("/data/tts/{filename}")
async def serve_tts_file(filename: str):
    """Serve generated TTS audio files."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(400, "Invalid filename")
    from fastapi.responses import FileResponse
    fpath = BASE_DIR / "data" / "tts" / filename
    if fpath.exists():
        return FileResponse(str(fpath), media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="TTS file not found")

# ============================================================
# Extended Stats
# ============================================================
@app.get("/api/stats")
async def get_stats():
    db = load_jokes()
    total = sum(len(items) for items in db.values())
    all_favs = load_json(FAVORITES_FILE, {})
    total_favs = sum(len(v) for v in all_favs.values()) if isinstance(all_favs, dict) else len(all_favs)
    history = load_json(HISTORY_FILE, [])
    
    # Only count if search engine is already loaded
    sem_stats = search_engine.get_stats() if search_engine else {"indexed_jokes": 0, "vocabulary_size": 0}
    
    # Quick avg from first 1000 jokes (avoid loading all 286K)
    sample = []
    for items in db.values():
        sample.extend(items[:10])
        if len(sample) >= 1000:
            break
    avg_rating = sum(j.get("rating", 4.0) for j in sample) / len(sample) if sample else 4.0
    
    return {
        "total_jokes": total,
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
        "version": "3.9.0"
    }

# ============================================================
# Landing page
# ============================================================
@app.get("/landing", response_class=HTMLResponse)
async def landing():
    landing_path = BASE_DIR / "static" / "landing.html"
    if landing_path.exists():
        return landing_path.read_text(encoding="utf-8")
    raise HTTPException(404, "Landing not found")

@app.get("/desktop", response_class=HTMLResponse)
async def desktop_page():
    """Standalone desktop HTML — connects to API automatically."""
    desktop_path = BASE_DIR / "static" / "standalone.html"
    if desktop_path.exists():
        return desktop_path.read_text(encoding="utf-8")
    raise HTTPException(404, "Desktop page not found")

# ============================================================
# Flutter Web App
# ============================================================
@app.get("/flutter", response_class=HTMLResponse)
async def flutter_app():
    flutter_index = BASE_DIR / "static" / "flutter" / "index.html"
    if flutter_index.exists():
        return flutter_index.read_text(encoding="utf-8")
    raise HTTPException(404, "Flutter app not found")

# Mount static files (icons, CSS, etc.)
from fastapi.staticfiles import StaticFiles
_static_dir = BASE_DIR / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static_files")

# Mount Flutter static assets (canvaskit, assets, icons, etc.)
_flutter_dir = BASE_DIR / "static" / "flutter"
if _flutter_dir.exists():
    app.mount("/static/flutter", StaticFiles(directory=str(_flutter_dir)), name="flutter_static")

# ============================================================
# Moderation API
# ============================================================
_moderator = ContentModerator()

class ModerateRequest(BaseModel):
    text: str

@app.post("/api/moderate")
async def moderate_text(request: ModerateRequest):
    """Проверить текст через ContentModerator (profanity + spam)."""
    result = _moderator.moderate(request.text)
    return {
        "approved": result["approved"],
        "score": result["score"],
        "reasons": result["reasons"],
        "clean_text": result["clean_text"],
    }

@app.post("/api/moderate/profanity")
async def check_profanity(request: ModerateRequest):
    """Проверить только мат (ProfanityFilter)."""
    return _moderator._profanity.check(request.text)

@app.post("/api/moderate/spam")
async def check_spam(request: ModerateRequest):
    """Проверить только спам (SpamDetector)."""
    result = _moderator._spam.is_spam(request.text)
    return {"is_spam": result, "text": request.text}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Запуск Анекдот в тему v3.9.0 на http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
