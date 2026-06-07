"""i18n — Internationalization module for Anekdot v Temu.

Default language: English (en).
Supported: en, ru, es, de, fr, pt, zh, ja, ar, hi.

Usage:
    from i18n import t, detect_language, get_tts_lang_code

    msg = t("error.text_too_long", lang="ru")
    lang = detect_language("Hello world")  # -> "en"
    tts_code = get_tts_lang_code("es")     # -> "es"
"""

SUPPORTED_LANGUAGES = ("en", "ru", "es", "de", "fr", "pt", "zh", "ja", "ar", "hi")
DEFAULT_LANG = "en"

# Language detection heuristics: unique character ranges
def _has_cjk(text, start, end):
    """Check if text contains CJK characters in the given Unicode range."""
    return any(start <= ord(c) <= end for c in text[:100])

def _detect_script(text):
    """Detect script/writing system from text. Returns lang code or None.
    Japanese detection: if hiragana/katakana present, it's ja even with kanji.
    Pure CJK without kana defaults to zh.
    """
    has_kana = False
    has_cjk = False
    for c in text[:200]:
        cp = ord(c)
        # Hiragana + Katakana (Japanese-specific) — check FIRST
        if 0x3040 <= cp <= 0x30FF:
            has_kana = True
        # CJK Unified Ideographs
        elif 0x4E00 <= cp <= 0x9FFF:
            has_cjk = True
        # Arabic
        elif 0x0600 <= cp <= 0x06FF:
            return "ar"
        # Devanagari (Hindi)
        elif 0x0900 <= cp <= 0x097F:
            return "hi"
    # Japanese = CJK + kana; Chinese = CJK without kana
    if has_kana:
        return "ja"
    if has_cjk:
        return "zh"
    return None

# GTTS language code mapping (some differ from ISO 639-1)
_GTTS_LANG_MAP = {
    "en": "en",
    "ru": "ru",
    "es": "es",
    "de": "de",
    "fr": "fr",
    "pt": "pt",
    "zh": "zh-CN",
    "ja": "ja",
    "ar": "ar",
    "hi": "hi",
}

# Whisper language code mapping
_WHISPER_LANG_MAP = {
    "en": "en",
    "ru": "ru",
    "es": "es",
    "de": "de",
    "fr": "fr",
    "pt": "pt",
    "zh": "zh",
    "ja": "ja",
    "ar": "ar",
    "hi": "hi",
}


# ============================================================
# Translation dictionary
# ============================================================
_TRANSLATIONS = {
    # --- Validation errors ---
    "error.text_empty": {
        "en": "text cannot be empty",
        "ru": "text не может быть пустым",
        "es": "el texto no puede estar vacío",
        "de": "Text darf nicht leer sein",
        "fr": "le texte ne peut pas être vide",
        "pt": "o texto não pode estar vazio",
    },
    "error.text_too_long": {
        "en": "text too long (max 5000 characters)",
        "ru": "text слишком длинный (макс 5000 символов)",
        "es": "texto demasiado largo (máx 5000 caracteres)",
        "de": "Text zu lang (max 5000 Zeichen)",
        "fr": "texte trop long (max 5000 caractères)",
        "pt": "texto muito longo (máx 5000 caracteres)",
    },
    "error.text_too_short": {
        "en": "text too short (min 10 characters)",
        "ru": "text слишком короткий (мин 10 символов)",
        "es": "texto demasiado corto (mín 10 caracteres)",
        "de": "Text zu kurz (min 10 Zeichen)",
        "fr": "texte trop court (min 10 caractères)",
        "pt": "texto muito curto (mín 10 caracteres)",
    },
    "error.count_invalid": {
        "en": "count must be > 0",
        "ru": "count должен быть > 0",
        "es": "count debe ser > 0",
        "de": "count muss > 0 sein",
        "fr": "count doit être > 0",
        "pt": "count deve ser > 0",
    },
    "error.category_empty": {
        "en": "category cannot be empty",
        "ru": "category не может быть пустым",
        "es": "la categoría no puede estar vacía",
        "de": "Kategorie darf nicht leer sein",
        "fr": "la catégorie ne peut pas être vide",
        "pt": "a categoria não pode estar vazia",
    },
    "error.rating_range": {
        "en": "rating must be between 1 and 5",
        "ru": "rating должен быть от 1 до 5",
        "es": "rating debe estar entre 1 y 5",
        "de": "Bewertung muss zwischen 1 und 5 liegen",
        "fr": "la note doit être entre 1 et 5",
        "pt": "rating deve estar entre 1 e 5",
    },
    "error.joke_not_found": {
        "en": "Joke not found",
        "ru": "Шутка не найдена",
        "es": "Chiste no encontrado",
        "de": "Witz nicht gefunden",
        "fr": "Blague non trouvée",
        "pt": "Piada não encontrada",
    },
    "error.no_jokes": {
        "en": "No jokes available",
        "ru": "Нет анекдотов",
        "es": "No hay chistes",
        "de": "Keine Witze verfügbar",
        "fr": "Pas de blagues disponibles",
        "pt": "Sem piadas disponíveis",
    },
    "error.no_jokes_found": {
        "en": "No jokes found",
        "ru": "Анекдоты не найдены",
        "es": "No se encontraron chistes",
        "de": "Keine Witze gefunden",
        "fr": "Aucune blague trouvée",
        "pt": "Nenhuma piada encontrada",
    },
    "error.audio_required": {
        "en": "audio_base64 is required",
        "ru": "audio_base64 обязателен",
        "es": "audio_base64 es obligatorio",
        "de": "audio_base64 ist erforderlich",
        "fr": "audio_base64 est requis",
        "pt": "audio_base64 é obrigatório",
    },
    "error.whisper_not_found": {
        "en": "whisper-cli not found and faster_whisper not installed",
        "ru": "whisper-cli не найден и faster_whisper не установлен",
        "es": "whisper-cli no encontrado y faster_whisper no instalado",
        "de": "whisper-cli nicht gefunden und faster_whisper nicht installiert",
        "fr": "whisper-cli introuvable et faster_whisper non installé",
        "pt": "whisper-cli não encontrado e faster_whisper não instalado",
    },
    "error.whisper_timeout": {
        "en": "whisper timeout (30s)",
        "ru": "таймаут whisper (30с)",
        "es": "tiempo de espera de whisper (30s)",
        "de": "Whisper-Zeitüberschreitung (30s)",
        "fr": "délai d'attente whisper (30s)",
        "pt": "tempo limite do whisper (30s)",
    },
    "error.stt_error": {
        "en": "Speech recognition error",
        "ru": "Ошибка распознавания речи",
        "es": "Error de reconocimiento de voz",
        "de": "Spracherkennungsfehler",
        "fr": "Erreur de reconnaissance vocale",
        "pt": "Erro de reconhecimento de voz",
    },
    "error.file_too_large": {
        "en": "File too large (max 25MB)",
        "ru": "Файл слишком большой (макс 25МБ)",
        "es": "Archivo demasiado grande (máx 25MB)",
        "de": "Datei zu groß (max 25MB)",
        "fr": "Fichier trop volumineux (max 25Mo)",
        "pt": "Arquivo muito grande (máx 25MB)",
    },
    "error.no_file": {
        "en": "No file uploaded",
        "ru": "Файл не загружен",
        "es": "Ningún archivo subido",
        "de": "Keine Datei hochgeladen",
        "fr": "Aucun fichier téléchargé",
        "pt": "Nenhum arquivo enviado",
    },
    "error.text_required": {
        "en": "text is required",
        "ru": "text обязателен",
        "es": "texto es obligatorio",
        "de": "Text ist erforderlich",
        "fr": "texte est requis",
        "pt": "texto é obrigatório",
    },
    "error.invalid_filename": {
        "en": "Invalid filename",
        "ru": "Некорректное имя файла",
        "es": "Nombre de archivo no válido",
        "de": "Ungültiger Dateiname",
        "fr": "Nom de fichier invalide",
        "pt": "Nome de arquivo inválido",
    },
    "error.tts_not_installed": {
        "en": "gTTS not installed. Run: pip install gTTS",
        "ru": "gTTS не установлен. Запустите: pip install gTTS",
        "es": "gTTS no instalado. Ejecute: pip install gTTS",
        "de": "gTTS nicht installiert. Ausführen: pip install gTTS",
        "fr": "gTTS non installé. Exécuter : pip install gTTS",
        "pt": "gTTS não instalado. Execute: pip install gTTS",
    },
    "error.tts_failed": {
        "en": "Text-to-speech error",
        "ru": "Ошибка озвучки",
        "es": "Error de sintesis de voz",
        "de": "Sprachausgabefehler",
        "fr": "Erreur de synthese vocale",
        "pt": "Erro de sintese de voz",
    },
    "error.landing_not_found": {
        "en": "Landing page not found",
        "ru": "Страница лендинга не найдена",
        "es": "Página de inicio no encontrada",
        "de": "Landing-Seite nicht gefunden",
        "fr": "Page d'accueil non trouvée",
        "pt": "Página inicial não encontrada",
    },
    "error.desktop_not_found": {
        "en": "Desktop page not found",
        "ru": "Страница десктопа не найдена",
        "es": "Página de escritorio no encontrada",
        "de": "Desktop-Seite nicht gefunden",
        "fr": "Page bureau non trouvée",
        "pt": "Página desktop não encontrada",
    },
    "error.flutter_not_found": {
        "en": "Flutter app not found",
        "ru": "Flutter приложение не найдено",
        "es": "Aplicación Flutter no encontrada",
        "de": "Flutter-App nicht gefunden",
        "fr": "Application Flutter non trouvée",
        "pt": "App Flutter não encontrada",
    },
    "error.tts_file_not_found": {
        "en": "TTS file not found",
        "ru": "TTS файл не найден",
        "es": "Archivo TTS no encontrado",
        "de": "TTS-Datei nicht gefunden",
        "fr": "Fichier TTS non trouvé",
        "pt": "Arquivo TTS não encontrado",
    },
    "error.content_rejected": {
        "en": "Content rejected: {reasons}",
        "ru": "Контент отклонён: {reasons}",
        "es": "Contenido rechazado: {reasons}",
        "de": "Inhalt abgelehnt: {reasons}",
        "fr": "Contenu rejeté : {reasons}",
        "pt": "Conteúdo rejeitado: {reasons}",
    },
    "error.rate_limit": {
        "en": "Rate limit exceeded (60 req/min)",
        "ru": "Превышен лимит запросов (60/мин)",
        "es": "Límite de solicitudes excedido (60 req/min)",
        "de": "Ratenlimit überschritten (60 Anfragen/Min)",
        "fr": "Limite de requêtes dépassée (60 req/min)",
        "pt": "Limite de requisições excedido (60 req/min)",
    },

    # --- Status / info messages ---
    "status.pending_approval": {
        "en": "pending_approval",
        "ru": "на_проверке",
        "es": "pendiente_aprobación",
        "de": "wartet_auf_Genehmigung",
        "fr": "en_attente_de_validation",
        "pt": "aguardando_aprovação",
    },
    "status.deleted": {
        "en": "deleted",
        "ru": "удалено",
        "es": "eliminado",
        "de": "gelöscht",
        "fr": "supprimé",
        "pt": "excluído",
    },
    "status.updated": {
        "en": "updated",
        "ru": "обновлено",
        "es": "actualizado",
        "de": "aktualisiert",
        "fr": "mis_à_jour",
        "pt": "atualizado",
    },
    "status.liked": {
        "en": "liked",
        "ru": "нравится",
        "es": "le_gustó",
        "de": "gelikt",
        "fr": "aimé",
        "pt": "curtido",
    },

    # --- Voice/STT status ---
    "voice.no_speech": {
        "en": "No speech detected",
        "ru": "Речь не обнаружена",
        "es": "No se detectó voz",
        "de": "Keine Sprache erkannt",
        "fr": "Aucune parole détectée",
        "pt": "Nenhuma fala detectada",
    },

    # --- Alice webhook responses ---
    "alice.help": {
        "en": "I find jokes by topic! Say something like 'tell me a joke about work' or 'joke about cats'.",
        "ru": "Я подбираю анекдоты по теме! Скажите, например: «расскажи анекдот про работу» или «шутка про котиков».",
        "es": "¡Encuentro chistes por tema! Di algo como 'cuéntame un chiste sobre el trabajo'.",
        "de": "Ich finde Witze nach Thema! Sag zum Beispiel: 'Erzähl mir einen Witz über Arbeit'.",
        "fr": "Je trouve des blagues par thème ! Dites par exemple : 'raconte une blague sur le travail'.",
        "pt": "Eu encontro piadas por tema! Diga algo como 'conte uma piada sobre trabalho'.",
    },
    "alice.db_empty": {
        "en": "Sorry, the joke database is empty.",
        "ru": "Извините, база анекдотов пока пуста.",
        "es": "Lo siento, la base de datos de chistes está vacía.",
        "de": "Leider ist die Witzdatenbank leer.",
        "fr": "Désolé, la base de données de blagues est vide.",
        "pt": "Desculpe, o banco de dados de piadas está vazio.",
    },
    "alice.category_empty": {
        "en": "Category is empty.",
        "ru": "Категория пуста.",
        "es": "La categoría está vacía.",
        "de": "Kategorie ist leer.",
        "fr": "La catégorie est vide.",
        "pt": "A categoria está vazia.",
    },
    "alice.not_found_fallback": {
        "en": "Couldn't find a matching one, but here's one: ",
        "ru": "Не нашёл подходящий, но вот: ",
        "es": "No encontré uno que coincida, pero aquí hay uno: ",
        "de": "Konnte keinen passenden finden, aber hier ist einer: ",
        "fr": "Je n'en ai pas trouvé un qui correspond, mais en voici un : ",
        "pt": "Não encontrei um que correspondesse, mas aqui está um: ",
    },
    "alice.not_found": {
        "en": "Couldn't find a matching joke.",
        "ru": "Не нашёл подходящий анекдот.",
        "es": "No encontré un chiste que coincida.",
        "de": "Konnte keinen passenden Witz finden.",
        "fr": "Je n'ai pas trouvé de blague correspondante.",
        "pt": "Não encontrei uma piada que correspondesse.",
    },
    "alice.no_jokes_yet": {
        "en": "No jokes yet.",
        "ru": "Шуток пока нет.",
        "es": "Aún no hay chistes.",
        "de": "Noch keine Witze.",
        "fr": "Pas encore de blagues.",
        "pt": "Ainda não há piadas.",
    },

    # --- LLM system prompts ---
    "llm.system_prompt": {
        "en": "You are a professional joke writer. Generate one short funny joke in English on the given topic. The joke should be original, not use profanity. Reply ONLY with the joke text, no explanations.",
        "ru": "Ты — профессиональный автор анекдотов. Генерируй один короткий смешной анекдот на русском языке по заданной теме. Анекдот должен быть оригинальным, не использовать мат. Отвечай ТОЛЬКО текстом анекдота, без пояснений.",
        "es": "Eres un escritor profesional de chistes. Genera un chiste corto y divertido en español sobre el tema dado. El chiste debe ser original y sin groserías. Responde SOLO con el texto del chiste.",
        "de": "Du bist ein professioneller Witzschreiber. Generiere einen kurzen lustigen Witz auf Deutsch zum gegebenen Thema. Nur den Witztext antworten, keine Erklärungen.",
        "fr": "Tu es un écrivain professionnel de blagues. Génère une blague courte et drôle en français sur le sujet donné. Réponds UNIQUEMENT avec le texte de la blague.",
        "pt": "Você é um escritor profissional de piadas. Gere uma piada curta e engraçada em português sobre o tema dado. Responda APENAS com o texto da piada.",
    },
    "llm.user_prompt": {
        "en": "Make up a joke about: {topic}",
        "ru": "Придумай анекдот на тему: {topic}",
        "es": "Inventa un chiste sobre: {topic}",
        "de": "Erdichte einen Witz über: {topic}",
        "fr": "Invente une blague sur : {topic}",
        "pt": "Invente uma piada sobre: {topic}",
    },
    "llm.ai_variation": {
        "en": "[AI variation on theme \"{topic}\"]",
        "ru": "[AI-вариация по теме \"{topic}\"]",
        "es": "[Variación IA sobre el tema \"{topic}\"]",
        "de": "[KI-Variation zum Thema \"{topic}\"]",
        "fr": "[Variation IA sur le thème \"{topic}\"]",
        "pt": "[Variação IA sobre o tema \"{topic}\"]",
    },
    "llm.fallback_topic": {
        "en": "life",
        "ru": "жизнь",
        "es": "vida",
        "de": "Leben",
        "fr": "vie",
        "pt": "vida",
    },

    # --- Monetization ---
    "ad.text": {
        "en": "Want more jokes? Try Premium!",
        "ru": "Хочешь больше анекдотов? Попробуй Premium!",
        "es": "¿Quieres más chistes? ¡Prueba Premium!",
        "de": "Mehr Witze gewollt? Probier Premium!",
        "fr": "Plus de blagues ? Essayez Premium !",
        "pt": "Quer mais piadas? Experimente Premium!",
    },

    # --- Console messages ---
    "console.starting": {
        "en": "Starting Anekdot v Temu v{version} on http://localhost:{port}",
        "ru": "Запуск Анекдот в тему v{version} на http://localhost:{port}",
        "es": "Iniciando Anekdot v Temu v{version} en http://localhost:{port}",
        "de": "Starte Anekdot v Temu v{version} auf http://localhost:{port}",
        "fr": "Demarrage Anekdot v Temu v{version} sur http://localhost:{port}",
        "pt": "Iniciando Anekdot v Temu v{version} em http://localhost:{port}",
    },
    "console.periodic_flush": {
        "en": "Periodic rating flush OK",
        "ru": "Периодический flush рейтингов OK",
        "es": "Flush periodico de ratings OK",
        "de": "Periodisches Rating-Flush OK",
        "fr": "Flush periodique des notes OK",
        "pt": "Flush periodico de avaliacoes OK",
    },
    "console.rating_flush_error": {
        "en": "Rating flush error: {error}",
        "ru": "Ошибка flush рейтингов: {error}",
        "es": "Error en flush de ratings: {error}",
        "de": "Rating-Flush-Fehler: {error}",
        "fr": "Erreur flush des notes: {error}",
        "pt": "Erro no flush de avaliacoes: {error}",
    },
    "console.ratings_saved": {
        "en": "Ratings saved to disk on shutdown",
        "ru": "Рейтинги сохранены на диск при выключении",
        "es": "Ratings guardados en disco al apagar",
        "de": "Ratings beim Herunterfahren gespeichert",
        "fr": "Notes sauvegardees a l'arret",
        "pt": "Avaliacoes salvas no disco ao desligar",
    },
    "console.search_released": {
        "en": "Search engine released on shutdown",
        "ru": "Поисковый движок освобождён при выключении",
        "es": "Motor de busqueda liberado al apagar",
        "de": "Suchmaschine beim Herunterfahren freigegeben",
        "fr": "Moteur de recherche libere a l'arret",
        "pt": "Motor de busca liberado ao desligar",
    },
    "console.shutdown_complete": {
        "en": "Graceful shutdown complete",
        "ru": "Корректное завершение",
        "es": "Apagado correcto completado",
        "de": "Ordnungsgemaesses Herunterfahren abgeschlossen",
        "fr": "Arret propre termine",
        "pt": "Desligamento correto concluido",
    },
    "console.building_index": {
        "en": "Building semantic index (first request)...",
        "ru": "Построение семантического индекса (первый запрос)...",
        "es": "Construyendo indice semantico (primera solicitud)...",
        "de": "Erstelle semantischen Index (erste Anfrage)...",
        "fr": "Construction de l'index semantique (premiere requete)...",
        "pt": "Construindo indice semantico (primeira requisicao)...",
    },
    "console.indexed": {
        "en": "Indexed {count} jokes, vocab size: {vocab}",
        "ru": "Проиндексировано {count} шуток, размер словаря: {vocab}",
        "es": "Indexados {count} chistes, tamano de vocabulario: {vocab}",
        "de": "{count} Witze indexiert, Vokabulargroesse: {vocab}",
        "fr": "{count} blagues indexees, taille du vocabulaire: {vocab}",
        "pt": "{count} piadas indexadas, tamanho do vocabulario: {vocab}",
    },
    "console.llm_error": {
        "en": "LLM generation error: {error}",
        "ru": "Ошибка генерации LLM: {error}",
        "es": "Error de generacion LLM: {error}",
        "de": "LLM-Generierungsfehler: {error}",
        "fr": "Erreur de generation LLM: {error}",
        "pt": "Erro de geracao LLM: {error}",
    },
    "console.analytics_error": {
        "en": "Analytics error: {error}",
        "ru": "Ошибка аналитики: {error}",
        "es": "Error de analitica: {error}",
        "de": "Analysefehler: {error}",
        "fr": "Erreur analytique: {error}",
        "pt": "Erro de analise: {error}",
    },
    "console.api_post_error": {
        "en": "api_post error ({path}): {error}",
        "ru": "Ошибка api_post ({path}): {error}",
        "es": "Error api_post ({path}): {error}",
        "de": "api_post Fehler ({path}): {error}",
        "fr": "Erreur api_post ({path}): {error}",
        "pt": "Erro api_post ({path}): {error}",
    },
    "console.command_timeout": {
        "en": "Command timed out: {cmd}",
        "ru": "Таймаут команды: {cmd}",
        "es": "Comando expirado: {cmd}",
        "de": "Befehl abgelaufen: {cmd}",
        "fr": "Commande expiree: {cmd}",
        "pt": "Comando expirado: {cmd}",
    },
}


def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    """Translate a key to the given language.

    Args:
        key: Translation key (e.g. "error.text_empty")
        lang: Language code (en, ru, es, de, fr, pt, zh, ja, ar, hi)
        **kwargs: Format variables for string interpolation

    Returns:
        Translated string. Falls back to English, then to the key itself.
    """
    entry = _TRANSLATIONS.get(key)
    if not entry:
        return key

    # Try requested language, then English fallback, then first available
    text = entry.get(lang) or entry.get(DEFAULT_LANG)
    if not text:
        text = next(iter(entry.values()))

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass

    return text


def detect_language(text: str) -> str:
    """Detect language from text content using character analysis.

    Returns ISO 639-1 code. Defaults to "en" if uncertain.
    """
    if not text:
        return DEFAULT_LANG

    # Check script via Unicode ranges (much more reliable than char samples)
    script_lang = _detect_script(text)
    if script_lang:
        return script_lang

    # Check Cyrillic (Russian)
    cyrillic_range = range(0x0400, 0x04FF)
    cyrillic_count = sum(1 for c in text[:200] if ord(c) in cyrillic_range)
    if cyrillic_count > len(text[:200]) * 0.3:
        return "ru"

    # Latin diacritics hints (order matters: most specific first)
    text_lower = text.lower()
    # Portuguese: ã, õ (unique to PT)
    if any(c in text_lower for c in ("ã", "õ")):
        return "pt"
    # German: ä, ö, ü, ß
    if any(c in text_lower for c in ("ä", "ö", "ü", "ß")):
        return "de"
    # Spanish: ñ, ¿, ¡
    if any(c in text_lower for c in ("ñ", "¿", "¡")):
        return "es"
    # French: é, è, ê, ë, ù, ç, à
    if any(c in text_lower for c in ("é", "è", "ê", "ë", "ù", "ç", "à")):
        return "fr"

    # Default to English for Latin text
    return DEFAULT_LANG


def get_tts_lang_code(lang: str) -> str:
    """Get gTTS-compatible language code."""
    return _GTTS_LANG_MAP.get(lang, "en")


def get_whisper_lang_code(lang: str) -> str:
    """Get whisper-compatible language code."""
    return _WHISPER_LANG_MAP.get(lang, "en")


def normalize_lang(lang: str | None) -> str:
    """Normalize language string. Returns DEFAULT_LANG if invalid."""
    if not lang:
        return DEFAULT_LANG
    lang = lang.strip().lower()[:2]
    if lang in SUPPORTED_LANGUAGES:
        return lang
    return DEFAULT_LANG
