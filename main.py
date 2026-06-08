"""Anekdot v Temu — AI-powered contextual joke app v3.16.0
- TF-IDF semantic search
- whisper.cpp local STT (74MB, 99 langs)
- Silero VAD voice activity detection (300KB)
- 286K jokes, 132 categories, 10 languages
- SQLite storage
- User CRUD, analytics, social, personalization
- PWA, multi-language, moderation, i18n
"""
import json, os, random, hashlib, time, subprocess, tempfile, base64, asyncio, threading, logging, sys
from pathlib import Path
from contextlib import asynccontextmanager
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Query, UploadFile, Request
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import Optional, List
from moderation import ProfanityFilter, SpamDetector, ContentModerator
from i18n import t, detect_language, get_tts_lang_code, DEFAULT_LANG, normalize_lang

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger("anekdot")


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
        await proc.wait()  # reap zombie
        raise TimeoutError(f"Command timed out: {args[0]}")

# ============================================================
# In-memory rate limiter (60 requests/minute per IP)
# ============================================================
class RateLimiter:
    def __init__(self, max_requests: int = 60, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self._requests: dict = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, ip: str) -> bool:
        async with self._lock:
            now = time.time()
            # Clean old entries for this IP
            self._requests[ip] = [t for t in self._requests[ip] if now - t < self.window]
            # Purge IPs with no recent requests (memory cleanup)
            if len(self._requests) > 10000:
                stale = [k for k, v in self._requests.items() if not v]
                for k in stale:
                    del self._requests[k]
            if len(self._requests[ip]) >= self.max_requests:
                return False
            self._requests[ip].append(now)
            return True

_rate_limiter = RateLimiter(60, 60)

# ============================================================
# AsyncIO locks for race conditions (init in lifespan)
# ============================================================
_rating_lock = None
_favorites_lock = None

# ============================================================
# Top jokes cache (TTL 5 minutes)
# ============================================================
_top_cache = {"jokes": [], "timestamp": 0}
_top_cache_lock = None
_TOP_CACHE_TTL = 300  # 5 minutes

# ============================================================
# Joke-by-ID index (built once)
# ============================================================
_joke_by_id: dict = {}
_joke_by_id_built = False

def _build_joke_by_id():
    global _joke_by_id, _joke_by_id_built
    if _joke_by_id_built:
        return
    all_jokes = get_all_jokes()
    _joke_by_id = {j["id"]: j for j in all_jokes if "id" in j}
    _joke_by_id_built = True

# ============================================================
# Lifespan context manager
# ============================================================
@asynccontextmanager
async def lifespan(app):
    # Init asyncio locks (can't create before event loop)
    global _rating_lock, _favorites_lock, _top_cache_lock
    _rating_lock = asyncio.Lock()
    _favorites_lock = asyncio.Lock()
    _top_cache_lock = asyncio.Lock()
    # Startup
    import asyncio as _asyncio
    async def _flush_loop():
        global _pending_rating_save, _last_save_time
        while True:
            await _asyncio.sleep(60)
            async with _rating_lock:
                if _pending_rating_save and _jokes_cache is not None:
                    try:
                        await _asyncio.to_thread(save_json, JOKES_FILE, _jokes_cache)
                        _pending_rating_save = False
                        _last_save_time = time.time()
                        global _jokes_cache_mtime
                        _jokes_cache_mtime = JOKES_FILE.stat().st_mtime
                        print(t("console.periodic_flush"))
                    except Exception as e:
                        print(t("console.rating_flush_error", error=str(e)))
    global _flush_task
    _flush_task = _asyncio.create_task(_flush_loop())
    yield
    # Shutdown: cancel flush task
    if _flush_task and not _flush_task.done():
        _flush_task.cancel()
    # Shutdown: save ratings
    global _pending_rating_save, _jokes_cache, search_engine
    async with _rating_lock:
        if _pending_rating_save and _jokes_cache is not None:
            await _asyncio.to_thread(save_json, JOKES_FILE, _jokes_cache)
            _jokes_cache_mtime = JOKES_FILE.stat().st_mtime
            print(t("console.ratings_saved"))
    # Save TF-IDF search engine state if loaded
    if search_engine is not None:
        print(t("console.search_released"))
        search_engine = None
    print(t("console.shutdown_complete"))

app = FastAPI(title="Анекдот в тему", version="3.16.0", lifespan=lifespan)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = (time.time() - start) * 1000
    log.info("%s %s → %d (%.0fms)", request.method, request.url.path, response.status_code, elapsed)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
# Data loading with in-memory cache
# ============================================================
_jokes_cache = None
_jokes_cache_mtime = 0

def load_jokes():
    global _jokes_cache, _jokes_cache_mtime
    if not JOKES_FILE.exists():
        return {}
    mtime = JOKES_FILE.stat().st_mtime
    if _jokes_cache is not None and mtime == _jokes_cache_mtime:
        return _jokes_cache
    with open(JOKES_FILE, "r", encoding="utf-8") as f:
        _jokes_cache = json.load(f)
    _jokes_cache_mtime = mtime
    return _jokes_cache

def _invalidate_jokes_cache():
    global _jokes_cache, _joke_by_id, _joke_by_id_built
    _jokes_cache = None
    _joke_by_id = {}
    _joke_by_id_built = False

# Periodic save for ratings (non-blocking)
_pending_rating_save = False
_last_save_time = 0

def _schedule_rating_save():
    """Mark ratings for save on next load or shutdown."""
    global _pending_rating_save, _last_save_time
    _pending_rating_save = True

def load_json(path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    """Atomic write: write to temp file, then rename (no corruption on crash)."""
    import tempfile
    dir_path = os.path.dirname(str(path))
    fd, tmp = tempfile.mkstemp(dir=dir_path, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, str(path))
    except Exception:
        os.unlink(tmp) if os.path.exists(tmp) else None
        raise

def get_all_jokes():
    db = load_jokes()
    jokes = []
    for category, items in db.items():
        for joke in items:
            jokes.append({**joke, "category": category})
    return jokes

# ============================================================
# English jokes (multi-language support)
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
        self._build_index()

    def _build_index(self):
        self.jokes = get_all_jokes()
        # Include EN_JOKES in search index
        self.jokes.extend([{**j, "category": f"en_{j.get('category', 'misc')}"} for j in EN_JOKES])
        if not self.jokes:
            return
        # Combine text + tags + category for matching
        documents = []
        for j in self.jokes:
            tags_text = " ".join(j.get("tags", []))
            doc = f"{j['text']} {j['category']} {tags_text}"
            documents.append(doc)
        self.tfidf_matrix = self.vectorizer.fit_transform(documents)

    def search(self, query: str, top_k: int = 10, min_score: float = 0.05) -> List[dict]:
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


# Lazy search engine: build TF-IDF on first request
# Server starts instantly instead of 60-90s wait
search_engine = None
_search_engine_lock = threading.Lock()

def _get_search_engine():
    global search_engine
    if search_engine is None:
        with _search_engine_lock:
            # Double-check after acquiring lock
            if search_engine is None:
                print(t("console.building_index"))
                search_engine = SemanticSearchEngine()
                print(t("console.indexed", count=len(search_engine.jokes), vocab=search_engine.get_stats()['vocabulary_size']))
    return search_engine

# ============================================================
# Keyword map (fallback + category boosting)
# ============================================================
KEYWORD_MAP = {
    "работа": ["работа", "работать", "зарплата", "начальник", "коллега", "офис", "карьера", "должность", "премия", "совещание", "босс", "подчинённый", "резюме", "собеседование", "увольнение", "отпуск", "дедлайн", "проект", "переработ", "meeting", "boss", "office", "deadline", "project", "salary", "work", "job", "boss", "deadline", "manager", "corporate"],
    "айти": ["программист", "код", "айти", "it", "python", "javascript", "git", "сервер", "баг", "devops", "qa", "тестировщик", "тестирование", "по", "software", "testing", "разработчик", "backend", "frontend", "sql", "linux", "девопс", "джуниор", "сеньор", "прод", "рефакторинг", "документация", "npm", "docker", "kubernetes", "микросервис", "legacy", "тип", "компиля", "фреймворк", "бета", "релиз", "деплой", "сборка"],
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
    # Multilingual keywords: Spanish
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
# LLM integration (OpenAI)
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

def generate_joke_with_llm(context: str, lang: str = "en") -> Optional[str]:
    """Generate a joke using OpenAI GPT model in the specified language."""
    client = get_openai_client()
    if not client:
        return None
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": t("llm.system_prompt", lang)},
                {"role": "user", "content": t("llm.user_prompt", lang, topic=context)}
            ],
            max_tokens=300,
            temperature=0.9,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(t("console.llm_error", error=str(e)))
        return None

# ============================================================
# Pydantic models
# ============================================================

class JokeRequest(BaseModel):
    text: str
    count: int = 3
    category: Optional[str] = None

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(t("error.text_empty"))
        if len(v) > 5000:
            raise ValueError(t("error.text_too_long"))
        return v.strip()

    @field_validator('count')
    @classmethod
    def validate_count(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(t("error.count_invalid"))
        if v > 50:
            v = 50
        return v

class FavoriteRequest(BaseModel):
    joke_id: int
    user_id: str = "default"

class RatingRequest(BaseModel):
    joke_id: int
    rating: float
    
    def validate_rating(self):
        import math
        if math.isnan(self.rating) or math.isinf(self.rating):
            raise HTTPException(status_code=400, detail=t("error.rating_range"))
        if self.rating < 1 or self.rating > 5:
            raise HTTPException(status_code=400, detail=t("error.rating_range"))
        return min(max(self.rating, 1.0), 5.0)

# ============================================================
# API routes
# ============================================================
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """#14: Simple rate limiter — 60 req/min per IP."""
    if request.url.path.startswith("/api/"):
        client_ip = request.client.host if request.client else "unknown"
        if not await _rate_limiter.is_allowed(client_ip):
            return HTMLResponse(content=json.dumps({"detail": t("error.rate_limit")}), status_code=429, media_type="application/json")
    response = await call_next(request)
    return response

@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = BASE_DIR / "static" / "index.html"
    if not html_path.exists():
        raise HTTPException(404, "index.html not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

@app.get("/logs", response_class=HTMLResponse)
async def logs_page():
    html_path = BASE_DIR / "static" / "logs.html"
    if not html_path.exists():
        raise HTTPException(404, "logs.html not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

@app.get("/emulator", response_class=HTMLResponse)
async def emulator_page():
    html_path = BASE_DIR / "static" / "emulator.html"
    if not html_path.exists():
        raise HTTPException(404, "emulator.html not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

@app.get("/api/categories")
async def get_categories():
    db = load_jokes()
    return {cat: len(jokes) for cat, jokes in db.items()}

@app.get("/api/jokes")
async def get_jokes(
    category: Optional[str] = Query(None),
    count: int = Query(5, ge=1, le=20),
    offset: int = Query(0, ge=0),
    randomize: bool = Query(True)
):
    all_jokes = get_all_jokes()
    if category:
        jokes = [j for j in all_jokes if j["category"] == category]
    else:
        jokes = all_jokes
    
    total = len(jokes)
    if randomize:
        jokes = random.sample(jokes, min(count, len(jokes)))
    else:
        jokes = jokes[offset:offset + count]
    
    return {"jokes": jokes, "total": total}

@app.get("/api/jokes/search")
async def search_jokes(q: str = Query(..., min_length=2), limit: int = Query(10, ge=1, le=50)):
    """Full-text search using TF-IDF semantic search."""
    engine = await asyncio.to_thread(_get_search_engine)
    results = await asyncio.to_thread(engine.search, q, limit * 3)
    # Language-aware scoring
    detected_lang = detect_language(q)
    lang_prefix_map = {"ru": "", "en": "en_", "es": "es_", "de": "de_", "fr": "fr_", "pt": "pt_", "zh": "zh_"}
    prefer_prefix = lang_prefix_map.get(detected_lang, "en_")
    for joke in results:
        cat = joke.get("category", "")
        if prefer_prefix == "":
            is_lang_match = not any(cat.startswith(p) for p in ["en_", "es_", "de_", "fr_", "pt_", "zh_"])
        else:
            is_lang_match = cat.startswith(prefer_prefix)
        if not is_lang_match:
            joke["semantic_score"] = joke.get("semantic_score", 0) * 0.3
    results.sort(key=lambda x: x.get("semantic_score", 0), reverse=True)
    return {"jokes": results[:limit], "total": len(results[:limit])}

@app.post("/api/jokes/context")
async def contextual_joke(request: JokeRequest):
    """Get contextually relevant jokes using semantic search + keyword boosting."""
    # Detect query language to prioritize matching jokes
    detected_lang = detect_language(request.text)
    # Map detected language to category prefix
    lang_prefix_map = {"ru": "", "en": "en_", "es": "es_", "de": "de_", "fr": "fr_", "pt": "pt_", "zh": "zh_"}
    prefer_prefix = lang_prefix_map.get(detected_lang, "en_")
    
    # Step 1: Semantic search
    engine = await asyncio.to_thread(_get_search_engine)
    semantic_results = await asyncio.to_thread(engine.search, request.text, 50)
    
    # Step 2: Keyword matching for category boosting
    matching_cats = find_matching_categories(request.text)
    
    # Step 3: Language-aware scoring — prefer jokes matching query language
    for joke in semantic_results:
        cat = joke.get("category", "")
        if prefer_prefix == "":
            # Russian: prefer non-prefixed categories
            is_lang_match = not any(cat.startswith(p) for p in ["en_", "es_", "de_", "fr_", "pt_", "zh_"])
        else:
            is_lang_match = cat.startswith(prefer_prefix)
        if not is_lang_match:
            joke["semantic_score"] = joke.get("semantic_score", 0) * 0.3  # Penalize wrong-language jokes
    
    # Step 4: Category boosting
    if matching_cats:
        for joke in semantic_results:
            if joke["category"] == matching_cats[0]:
                joke["semantic_score"] = joke.get("semantic_score", 0) * 1.5
            elif joke["category"] in matching_cats:
                joke["semantic_score"] = joke.get("semantic_score", 0) * 1.3
    
    # Step 5: Filter out zero-score results (no semantic match)
    semantic_results = [j for j in semantic_results if j.get("semantic_score", 0) > 0.01]
    
    # Step 6: If semantic search found nothing, fall back to keyword-only
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
    await asyncio.to_thread(save_json, HISTORY_FILE, history[-100:])
    
    return {
        "jokes": selected,
        "matched_categories": matching_cats,
        "context": request.text,
        "search_method": "semantic"
    }

@app.post("/api/jokes/generate")
async def generate_joke(request: JokeRequest):
    """Generate a new joke using LLM (OpenAI) or template fallback."""
    matching_cats = find_matching_categories(request.text)
    
    # Try LLM first
    detected_lang = detect_language(request.text)
    llm_joke = await asyncio.to_thread(generate_joke_with_llm, request.text, detected_lang)
    
    if llm_joke:
        return {
            "joke": {
                "id": int(time.time() * 1000000) % 1000000 + random.randint(1, 99999),
                "text": llm_joke,
                "rating": 4.5,
                "tags": matching_cats[:3] + ["ai-generated", "llm"],
                "category": matching_cats[0] if matching_cats else "misc",
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
        # No keyword match — try semantic search to find relevant jokes
        engine = await asyncio.to_thread(_get_search_engine)
        semantic_hits = await asyncio.to_thread(engine.search, request.text, 20)
        if semantic_hits:
            templates = semantic_hits
        else:
            # Last resort: pick from category that looks related to query language
            templates = all_jokes
    
    template = random.choice(templates if templates else (all_jokes if all_jokes else [{"text": t("alice.no_jokes_yet"), "rating": 0, "tags": []}]))
    
    return {
        "joke": {
            "id": int(time.time() * 1000000) % 1000000 + random.randint(1, 99999),
            "text": t("llm.ai_variation", detected_lang, topic=matching_cats[0] if matching_cats else request.text[:50]) + "\n" + template["text"],
            "rating": round(template.get("rating", 4.0) + random.uniform(-0.5, 0.5), 1),
            "tags": template.get("tags", []) + ["ai-generated", "template"],
            "category": template.get("category", "misc"),
            "generated": True,
            "generator": "template"
        },
        "matched_categories": matching_cats
    }

@app.post("/api/favorites")
async def add_favorite(request: FavoriteRequest):
    async with _favorites_lock:
        all_favs = load_json(FAVORITES_FILE, {})
        user_favs = all_favs.get(request.user_id, [])
        if request.joke_id not in user_favs:
            user_favs.append(request.joke_id)
        all_favs[request.user_id] = user_favs
        await asyncio.to_thread(save_json, FAVORITES_FILE, all_favs)
    return {"favorites": user_favs}

@app.delete("/api/favorites/{joke_id}")
async def remove_favorite(joke_id: int, user_id: str = "default"):
    async with _favorites_lock:
        all_favs = load_json(FAVORITES_FILE, {})
        user_favs = all_favs.get(user_id, [])
        if joke_id in user_favs:
            user_favs.remove(joke_id)
        all_favs[user_id] = user_favs
        await asyncio.to_thread(save_json, FAVORITES_FILE, all_favs)
    return {"favorites": user_favs}

@app.get("/api/favorites")
async def get_favorites(user_id: str = "default"):
    all_favs = load_json(FAVORITES_FILE, {})
    favorites = all_favs.get(user_id, [])
    if not favorites:
        return {"jokes": []}
    _build_joke_by_id()
    fav_jokes = [_joke_by_id[jid].copy() for jid in favorites if jid in _joke_by_id]
    return {"jokes": fav_jokes}

@app.post("/api/rate")
async def rate_joke(request: RatingRequest):
    clamped = request.validate_rating()
    async with _rating_lock:
        db = load_jokes()  # Uses cache, fast after first call
        for category, jokes in db.items():
            for joke in jokes:
                if joke["id"] == request.joke_id:
                    old = joke.get("rating", 4.0)
                    # Weighted average with confidence
                    votes = joke.get("votes", 1) + 1
                    new = round((old * (votes - 1) + clamped) / votes, 1)
                    joke["rating"] = min(max(new, 1.0), 5.0)
                    joke["votes"] = votes
                    # Schedule save (non-blocking)
                    _schedule_rating_save()
                    return {"new_rating": joke["rating"], "votes": votes}
    raise HTTPException(status_code=404, detail=t("error.joke_not_found"))

@app.get("/api/joke/random")
async def random_joke(category: Optional[str] = Query(None), lang: Optional[str] = Query(None)):
    # Fast random: category -> joke
    # No need to flatten 286K jokes
    if lang:
        lang = normalize_lang(lang)
    db = load_jokes()
    cats = list(db.keys())
    if not cats:
        raise HTTPException(404, t("error.no_jokes"))
    
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
        # Default: exclude foreign-prefixed categories
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
        raise HTTPException(404, t("error.no_jokes_found"))
    
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
            raise HTTPException(status_code=400, detail=t("error.category_empty"))
        if not self.text or len(self.text.strip()) < 10:
            raise HTTPException(status_code=400, detail=t("error.text_too_short"))
        if len(self.text) > 5000:
            raise HTTPException(status_code=400, detail=t("error.text_too_long"))
        return True

@app.post("/api/user-jokes")
async def create_user_joke(req: UserJokeRequest):
    """Add a user-submitted joke."""
    req.validate()
    # Moderation check
    mod = _moderator.moderate(req.text)
    if not mod["approved"]:
        raise HTTPException(status_code=422, detail=t("error.content_rejected", reasons='; '.join(mod['reasons'])))
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
    return {"id": joke_id, "status": t("status.pending_approval")}

@app.get("/api/user-jokes")
async def list_user_jokes(approved: int = Query(0)):
    """List user-submitted jokes."""
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM user_jokes WHERE approved = ? ORDER BY created_at DESC LIMIT 50", (approved,)).fetchall()
    finally:
        conn.close()
    result = []
    for r in rows:
        d = dict(r)
        # Parse tags from JSON string
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
        # Check joke exists (404 if not)
        row = conn.execute("SELECT id FROM user_jokes WHERE id = ?", (joke_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=t("error.joke_not_found"))
        conn.execute("DELETE FROM user_jokes WHERE id = ?", (joke_id,))
        conn.commit()
    finally:
        conn.close()
    return {"status": t("status.deleted")}

# ============================================================
# #26: Personalization
# ============================================================
@app.post("/api/personalize/{user_hash}")
async def update_preferences(user_hash: str, liked_cat: str = "", disliked_cat: str = ""):
    """Update user preferences."""
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO user_prefs (user_hash, liked_categories, disliked_categories, request_count) 
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_hash) DO UPDATE SET 
                liked_categories = ?, disliked_categories = ?, 
                request_count = request_count + 1, last_seen = CURRENT_TIMESTAMP
        """, (user_hash, liked_cat, disliked_cat, liked_cat, disliked_cat))
        conn.commit()
    finally:
        conn.close()
    return {"status": t("status.updated")}

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
            # Insert from JSON db (O(1) via _joke_by_id)
            _build_joke_by_id()
            joke = _joke_by_id.get(joke_id)
            if joke:
                try:
                    conn.execute("INSERT INTO jokes (id, category, text, rating, tags, likes) VALUES (?,?,?,?,?,1)",
                                (joke["id"], joke["category"], joke["text"], joke.get("rating", 4.0), json.dumps(joke.get("tags",[]))))
                except Exception as _ie:
                    # Concurrent INSERT or DB error: update instead
                    conn.execute("UPDATE jokes SET likes = likes + 1 WHERE id = ?", (joke_id,))
            else:
                raise HTTPException(404, t("error.joke_not_found"))
        conn.commit()
    finally:
        conn.close()
    
    # Track analytics
    await asyncio.to_thread(track_event, "like", joke_id=joke_id)
    return {"status": t("status.liked")}

@app.get("/api/jokes/social/top")
async def top_jokes(period: str = Query("day"), count: int = Query(10, ge=1, le=50)):
    """Get top jokes by likes/rating. Results cached for 5 minutes (#23)."""
    global _top_cache
    cache_key = f"{period}_{count}"
    async with _top_cache_lock:
        now = time.time()
        if now - _top_cache.get("timestamp", 0) > _TOP_CACHE_TTL or _top_cache.get("key") != cache_key or not _top_cache.get("jokes"):
            all_jokes = get_all_jokes()
            sorted_jokes = sorted(all_jokes, key=lambda j: j.get("rating", 0), reverse=True)
            _top_cache = {"jokes": sorted_jokes[:100], "timestamp": now, "key": cache_key}
    return {"jokes": _top_cache["jokes"][:count], "period": period}

# ============================================================
# #31: Monetization endpoints (stubs)
# ============================================================
@app.get("/api/monetization/ad")
async def get_ad():
    """Get an ad to display (stub)."""
    return {
        "ad": {
            "type": "banner",
            "text": t("ad.text"),
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
        "price": "199 RUB/month"
    }

# ============================================================
# #33: Analytics
# ============================================================
def track_event(event_type: str, category: str = None, joke_id: int = None, query: str = None, user_hash: str = None):
    """Track an analytics event."""
    try:
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO analytics (event_type, category, joke_id, query, user_hash) VALUES (?,?,?,?,?)",
                (event_type, category, joke_id, query, user_hash)
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        print(t("console.analytics_error", error=str(e)))

@app.get("/api/analytics/popular")
async def popular_topics(days: int = Query(7, ge=1, le=30)):
    """Get most popular topics/queries."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT category, COUNT(*) as cnt 
            FROM analytics 
            WHERE event_type = 'search' 
            AND created_at >= datetime('now', ? || ' days')
            GROUP BY category 
            ORDER BY cnt DESC 
            LIMIT 20
        """, (f"-{days}",)).fetchall()
    finally:
        conn.close()
    return {"popular": [dict(r) for r in rows], "period_days": days}

@app.get("/api/analytics/stats")
async def analytics_stats():
    """Get overall analytics."""
    conn = get_db()
    try:
        total_events = conn.execute("SELECT COUNT(*) FROM analytics").fetchone()[0]
        total_users = conn.execute("SELECT COUNT(DISTINCT user_hash) FROM analytics WHERE user_hash IS NOT NULL").fetchone()[0]
        top_cats = conn.execute("""
            SELECT category, COUNT(*) as cnt FROM analytics 
            WHERE category IS NOT NULL GROUP BY category ORDER BY cnt DESC LIMIT 10
        """).fetchall()
    finally:
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
    db = load_jokes()
    en = []
    for cat, items in db.items():
        if cat.startswith("en_"):
            for j in items:
                en.append({**j, "category": cat})
    if not en:
        en = list(EN_JOKES)  # fallback to hardcoded
    selected = random.sample(en, min(count, len(en)))
    return {"jokes": selected, "total": len(en)}

# ============================================================
# #34: PWA Support
# ============================================================
@app.get("/sw.js")
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
    return Response(content=sw, media_type="application/javascript")

@app.get("/manifest.json")
async def web_manifest():
    return {
        "name": "Анекдот в тему",
        "short_name": "Анекдот",
        "description": "AI-powered contextual jokes",
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
        text = t("alice.help", "ru")
    elif "случайный" in command or "любой" in command:
        db = load_jokes()
        if not db:
            text = t("alice.db_empty", "ru")
        else:
            cat = random.choice(list(db.keys()))
            joke = random.choice(db[cat]) if db[cat] else {"text": t("alice.category_empty", "ru")}
            text = joke["text"]
    else:
        data = await api_post("/api/jokes/context", {"text": original_utterance, "count": 1})
        if data and data.get("jokes"):
            text = data["jokes"][0]["text"]
        else:
            db = load_jokes()
            if db:
                cat = random.choice(list(db.keys()))
                joke = random.choice(db[cat]) if db[cat] else {"text": ""}
                text = t("alice.not_found_fallback", "ru") + joke['text']
            else:
                text = t("alice.not_found", "ru")
    
    # Alice has 1024 char limit for text/tts
    text_safe = text[:1024]
    tts_safe = text_safe.replace("\n", ". ")
    
    return {
        "response": {
            "text": text_safe,
            "tts": tts_safe,
            "end_session": False
        },
        "version": "1.0"
    }

async def api_post(path, data):
    """Internal API call for Alice webhook (async to avoid event loop blocking)."""
    import urllib.request
    base_url = os.environ.get("BASE_URL", "http://localhost:8000")
    def _do():
        req = urllib.request.Request(
            f"{base_url}{path}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    try:
        return await asyncio.to_thread(_do)
    except Exception as e:
        print(t("console.api_post_error", path=path, error=str(e)))
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
            # Silero expects 512-sample chunks at 16kHz
            chunk_size = 512
            speech_probs = []
            for i in range(0, len(samples) - chunk_size, chunk_size):
                chunk = samples[i:i + chunk_size].reshape(1, -1).astype(np.float32)
                result = sess.run(None, {input_name: chunk})
                # Force Python float conversion
                prob_val = result[0].flatten()[0]
                speech_probs.append(float(np.float64(prob_val)))

            max_prob = float(max(speech_probs)) if speech_probs else 0.0
            return {"has_speech": bool(max_prob >= threshold), "speech_prob": max_prob, "duration_sec": duration}
        except Exception as e:
            # Fallback: energy-based VAD
            rms = float(np.sqrt(np.mean(samples ** 2)))
            prob = min(rms * 10.0, 1.0)
            return {"has_speech": bool(prob >= threshold), "speech_prob": prob, "duration_sec": duration, "vad_fallback": "energy_mode"}
    except Exception as e:
        return {"has_speech": True, "speech_prob": -1.0, "duration_sec": 0.0, "error": "vad_check_failed"}


@app.post("/api/voice/stt")
async def speech_to_text(request: dict):
    """Real speech-to-text using whisper.cpp (local, no API needed).
    Input: {audio_base64: str, format: 'wav'|'webm'|'ogg', language: 'ru'|'en'|...}
    Output: {text: str, language: str, confidence: float, vad: dict}
    """
    audio_b64 = request.get("audio_base64", "")
    audio_format = request.get("format", "wav")
    language = normalize_lang(request.get("language", DEFAULT_LANG))
    
    if not audio_b64:
        raise HTTPException(status_code=400, detail=t("error.audio_required"))
    
    # Validate whisper-cli exists
    use_faster_whisper = False
    if not os.path.exists(WHISPER_CLI) or not os.path.exists(WHISPER_MODEL):
        # Fallback to faster_whisper on Windows
        try:
            from faster_whisper import WhisperModel
            use_faster_whisper = True
        except ImportError:
            raise HTTPException(status_code=500, detail=t("error.whisper_not_found"))
    
    tmp_path = None
    wav_path = None
    try:
        # Decode base64 to temp file
        audio_bytes = base64.b64decode(audio_b64)
        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        # Convert to 16kHz WAV if needed
        wav_path = tmp_path
        if audio_format != "wav":
            wav_path = tmp_path + ".wav"
            await _run_subprocess(["ffmpeg", "-y", "-i", tmp_path, "-ar", "16000", "-ac", "1", "-f", "wav", wav_path], timeout=10)
        
        # Step 1: Silero VAD check
        vad_result = await asyncio.to_thread(_silero_vad_check, wav_path)
        if not vad_result["has_speech"]:
            os.unlink(tmp_path)
            if wav_path != tmp_path:
                os.unlink(wav_path)
            return {"text": "", "language": language, "confidence": 0.0, "vad": vad_result, "note": t("voice.no_speech")}
        
        # Step 2: Transcription
        text = ""
        model_name = ""
        
        if use_faster_whisper:
            # faster_whisper (works on Windows)
            from faster_whisper import WhisperModel
            if not hasattr(speech_to_text, "_fw_model"): speech_to_text._fw_model = WhisperModel("base", device="cpu", compute_type="int8")
            fw_model = speech_to_text._fw_model
            lang_arg = language if language != "auto" else None
            def _fw_transcribe():
                segs, _ = fw_model.transcribe(wav_path, language=lang_arg)
                return " ".join(s.text for s in segs).strip()
            text = await asyncio.to_thread(_fw_transcribe)
            model_name = "faster_whisper base (CPU)"
        else:
            # whisper.cpp (Linux/Docker)
            rc, stdout, stderr = await _run_subprocess([WHISPER_CLI, "-m", WHISPER_MODEL, "-l", language, "-f", wav_path,
                 "--no-timestamps", "-t", "4", "--output-txt"], timeout=30
            )
            text = stdout.decode().strip()
            # Also try .txt file whisper may have created
            txt_path = wav_path + ".txt"
            if os.path.exists(txt_path):
                with open(txt_path, encoding='utf-8') as f:
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
    except (subprocess.TimeoutExpired, TimeoutError):
        for p in [_p for _p in [tmp_path, wav_path] if _p]:
            if 'tmp_path' in dir() and os.path.exists(p): os.unlink(p)
        raise HTTPException(status_code=504, detail=t("error.whisper_timeout"))
    except Exception as e:
        for p in [_p for _p in [tmp_path, wav_path] if _p]:
            if 'tmp_path' in dir() and os.path.exists(p): os.unlink(p)
        raise HTTPException(status_code=500, detail=t("error.stt_error"))


@app.post("/api/voice/stt/file")
async def speech_to_text_file(file: UploadFile = None, language: str = "auto"):
    """Upload audio file for STT. Accepts WAV/MP3/OGG/FLAC. Max 25MB."""
    if not file:
        raise HTTPException(status_code=400, detail=t("error.no_file"))
    
    # Read with 25MB size limit
    content = await file.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail=t("error.file_too_large"))
    
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
        vad_result = await asyncio.to_thread(_silero_vad_check, wav_path)
        if not vad_result["has_speech"]:
            for p in [_p for _p in [tmp_path, wav_path] if _p]:
                if os.path.exists(p): os.unlink(p)
            return {"text": "", "vad": vad_result, "note": t("voice.no_speech")}
        
        # Transcription
        use_fw = not (os.path.exists(WHISPER_CLI) and os.path.exists(WHISPER_MODEL))
        text = ""
        model_used = ""
        
        if use_fw:
            from faster_whisper import WhisperModel
            if not hasattr(speech_to_text_file, "_fw_model"): speech_to_text_file._fw_model = WhisperModel("base", device="cpu", compute_type="int8")
            fw_model = speech_to_text_file._fw_model
            lang_arg = language if language != "auto" else None
            def _transcribe():
                segs, _ = fw_model.transcribe(wav_path, language=lang_arg)
                return " ".join(s.text for s in segs).strip()
            text = await asyncio.to_thread(_transcribe)
            model_used = "faster_whisper base (CPU)"
        else:
            lang_arg = language if language != "auto" else "auto"
            rc, stdout, stderr = await _run_subprocess(
                [WHISPER_CLI, "-m", WHISPER_MODEL, "-l", lang_arg, "-f", wav_path,
                 "--no-timestamps", "-t", "4"], timeout=30
            )
            text = stdout.decode().strip()
            model_used = "whisper.cpp base"
        
        # Cleanup
        for p in [_p for _p in [tmp_path, wav_path] if _p]:
            if os.path.exists(p): os.unlink(p)
        
        return {"text": text, "vad": vad_result, "model": model_used}
    except Exception as e:
        # Cleanup temp files on error
        for p in [tmp_path, tmp_path + ".wav"]:
            if os.path.exists(p): os.unlink(p)
        raise HTTPException(status_code=500, detail=t("error.stt_error"))


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
        "whisper_cli": os.path.basename(WHISPER_CLI),
        "whisper_model": os.path.basename(WHISPER_MODEL),
        "silero_vad": os.path.basename(SILERO_VAD_MODEL),
        "whisper_model_size": f"{os.path.getsize(WHISPER_MODEL) // 1024 // 1024}MB" if os.path.exists(WHISPER_MODEL) else "not found",
        "silero_vad_size": f"{os.path.getsize(SILERO_VAD_MODEL) // 1024}KB" if os.path.exists(SILERO_VAD_MODEL) else "not found",
    }

@app.post("/api/voice/tts")
async def text_to_speech(request: dict):
    """Text-to-speech: converts joke text to MP3 audio via gTTS (Google TTS, free)."""
    text = request.get("text", "")
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail=t("error.text_required"))
    if len(text) > 5000:
        raise HTTPException(status_code=400, detail=t("error.text_too_long"))
    
    try:
        from gtts import gTTS
        import tempfile, os
        
        # gTTS limit ~5000 characters
        text = text[:2000]
        
        tts_dir = BASE_DIR / "data" / "tts"
        tts_dir.mkdir(parents=True, exist_ok=True)
        
        import hashlib
        fname = hashlib.sha256(text.encode()).hexdigest()[:12] + ".mp3"
        fpath = tts_dir / fname
        
        if not fpath.exists():
            def _gen_tts():
                tts = gTTS(text=text, lang=get_tts_lang_code(detect_language(text)), slow=False)
                tts.save(str(fpath))
            await asyncio.to_thread(_gen_tts)
        
        return {
            "text": text,
            "audio_file": f"/data/tts/{fname}",
            "duration_estimate": f"{len(text) // 15} sec",
            "generator": "gTTS (Google TTS, free)"
        }
    except ImportError:
        raise HTTPException(status_code=503, detail=t("error.tts_not_installed"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=t("error.tts_failed"))




@app.get("/data/tts/{filename}")
async def serve_tts_file(filename: str):
    """Serve generated TTS audio files."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(400, t("error.invalid_filename"))
    from fastapi.responses import FileResponse
    fpath = BASE_DIR / "data" / "tts" / filename
    if fpath.exists():
        return FileResponse(str(fpath), media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail=t("error.tts_file_not_found"))

# ============================================================
# Extended stats
# ============================================================
@app.get("/api/stats")
async def get_stats():
    db = load_jokes()
    total = sum(len(items) for items in db.values())
    all_favs = load_json(FAVORITES_FILE, {})
    total_favs = sum(len(v) for v in all_favs.values()) if isinstance(all_favs, dict) else len(all_favs)
    history = load_json(HISTORY_FILE, [])
    
    # Only count if search engine is loaded
    sem_stats = search_engine.get_stats() if search_engine else {"indexed_jokes": 0, "vocabulary_size": 0}
    
    # Quick avg from first 1000 jokes
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
        "version": "3.14.2"
    }

# ============================================================
# Landing page
# ============================================================
@app.get("/landing", response_class=HTMLResponse)
async def landing():
    landing_path = BASE_DIR / "static" / "landing.html"
    if landing_path.exists():
        return landing_path.read_text(encoding="utf-8")
    raise HTTPException(404, t("error.landing_not_found"))

@app.get("/desktop", response_class=HTMLResponse)
async def desktop_page():
    """Standalone desktop HTML — connects to API automatically."""
    desktop_path = BASE_DIR / "static" / "standalone.html"
    if desktop_path.exists():
        return desktop_path.read_text(encoding="utf-8")
    raise HTTPException(404, t("error.desktop_not_found"))

# ============================================================
# Flutter Web app
# ============================================================
@app.get("/flutter", response_class=HTMLResponse)
async def flutter_app():
    flutter_index = BASE_DIR / "static" / "flutter" / "index.html"
    if flutter_index.exists():
        return flutter_index.read_text(encoding="utf-8")
    raise HTTPException(404, t("error.flutter_not_found"))

# Mount static files
from fastapi.staticfiles import StaticFiles
_static_dir = BASE_DIR / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static_files")

# Mount Flutter static assets
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
    """Moderate text (profanity + spam)."""
    result = _moderator.moderate(request.text)
    return {
        "approved": result["approved"],
        "score": result["score"],
        "reasons": result["reasons"],
        "clean_text": result["clean_text"],
    }

@app.post("/api/moderate/profanity")
async def check_profanity(request: ModerateRequest):
    """Check profanity only."""
    return _moderator.profanity.check(request.text)

@app.post("/api/moderate/spam")
async def check_spam(request: ModerateRequest):
    """Check spam only."""
    result = _moderator.spam.is_spam(request.text)
    return {"is_spam": result, "text": request.text}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(t("console.starting", version="3.14.2", port=port))
    uvicorn.run(app, host="0.0.0.0", port=port)
