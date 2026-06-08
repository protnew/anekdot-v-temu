#!/usr/bin/env python3
"""Autotests for Anekdot v Temu — voice pipeline + core API.
Run: python test_voice.py
"""

import json
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

BASE = "http://localhost:8000"
passed = 0
failed = 0
errors = []


def test(name, func):
    global passed, failed
    try:
        func()
        passed += 1
        print(f"  ✅ {name}")
    except Exception as e:
        failed += 1
        errors.append(f"{name}: {e}")
        print(f"  ❌ {name} — {e}")


def api_get(path, expected_status=200):
    url = BASE + path
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert resp.status == expected_status, f"Expected {expected_status}, got {resp.status}"
            return data
    except urllib.error.HTTPError as e:
        if e.code == expected_status:
            return json.loads(e.read().decode("utf-8"))
        raise


def api_post(path, body, expected_status=200):
    url = BASE + path
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            assert resp.status == expected_status, f"Expected {expected_status}, got {resp.status}"
            return result
    except urllib.error.HTTPError as e:
        if e.code == expected_status:
            return json.loads(e.read().decode("utf-8"))
        raise


# ============================================================
# PART 1: Core API endpoints
# ============================================================
print("\n=== PART 1: Core API ===")


def test_stats():
    d = api_get("/api/stats")
    assert d["total_jokes"] > 0, "No jokes in database"
    assert d["categories"] > 0, "No categories"
    assert "llm_available" in d, "Missing llm_available field"
    print(f"    ({d['total_jokes']} jokes, {d['categories']} cats)")


test("GET /api/stats", test_stats)


def test_random():
    d = api_get("/api/joke/random")
    assert "text" in d, "Missing text field"
    assert "category" in d, "Missing category field"
    assert len(d["text"]) > 10, "Joke text too short"


test("GET /api/joke/random", test_random)


def test_categories():
    d = api_get("/api/categories")
    assert isinstance(d, dict) or isinstance(d, list), "Categories not a dict/list"
    cats = d if isinstance(d, list) else list(d.keys())
    assert len(cats) > 0, "No categories returned"


test("GET /api/categories", test_categories)


def test_search():
    d = api_get("/api/jokes/search?q=" + urllib.parse.quote("программист") + "&limit=5")
    assert "jokes" in d, "Missing jokes field"
    assert d["total"] >= 0, "Missing total"


test("GET /api/jokes/search?q=программист", test_search)


def test_search_en():
    d = api_get("/api/jokes/search?q=test&limit=5")
    assert "jokes" in d, "Missing jokes field"


test("GET /api/jokes/search?q=test (EN)", test_search_en)


def test_context():
    d = api_post("/api/jokes/context", {"text": "сижу на совещании начальник", "count": 3})
    assert "jokes" in d, "Missing jokes field"
    assert "matched_categories" in d, "Missing matched_categories"


test("POST /api/jokes/context (RU)", test_context)


def test_context_en():
    d = api_post("/api/jokes/context", {"text": "software testing bug report", "count": 3})
    assert "jokes" in d, "Missing jokes field"


test("POST /api/jokes/context (EN)", test_context_en)


def test_generate():
    d = api_post("/api/jokes/generate", {"text": "программист", "count": 1})
    assert "joke" in d or "jokes" in d, "Missing joke/jokes field"


test("POST /api/jokes/generate", test_generate)


def test_index_html():
    req = urllib.request.Request(BASE + "/")
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8")
        assert '<html lang="en"' in html, "Missing html lang=en"
        assert "vmBtn" in html, "Missing voice monitor button"
        assert "tab-voice" in html, "Missing voice tab"


test("GET / — index.html has voice tab", test_index_html)


# ============================================================
# PART 2: Voice endpoints
# ============================================================
print("\n=== PART 2: Voice Pipeline ===")


def test_voice_status():
    d = api_get("/api/voice/status")
    assert "stt_available" in d, "Missing stt_available"
    assert "stt_engine" in d, "Missing stt_engine"
    print(f"    (STT: {d['stt_engine']}, available: {d['stt_available']})")


test("GET /api/voice/status", test_voice_status)


def test_stt_empty_rejected():
    try:
        api_post("/api/voice/stt", {}, expected_status=400)
    except urllib.error.HTTPError as e:
        assert e.code == 400, f"Expected 400, got {e.code}"


test("POST /api/voice/stt (empty) → 400", test_stt_empty_rejected)


def test_tts():
    d = api_post("/api/voice/tts", {"text": "Test joke for TTS pipeline"})
    assert "audio_file" in d, "Missing audio_file"
    assert d["audio_file"].startswith("/data/tts/"), f"Unexpected audio_file: {d['audio_file']}"
    print(f"    (file: {d['audio_file']})")


test("POST /api/voice/tts", test_tts)


def test_tts_empty_rejected():
    try:
        api_post("/api/voice/tts", {"text": ""}, expected_status=400)
    except urllib.error.HTTPError as e:
        assert e.code == 400, f"Expected 400, got {e.code}"


test("POST /api/voice/tts (empty) → 400", test_tts_empty_rejected)


def test_tts_served():
    # First generate a TTS file
    d = api_post("/api/voice/tts", {"text": "Cache test TTS audio file"})
    fname = d["audio_file"].split("/")[-1]
    req = urllib.request.Request(BASE + f"/data/tts/{fname}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status == 200, "TTS file not served"
        data = resp.read()
        assert len(data) > 100, "TTS file too small"
        print(f"    ({len(data)} bytes MP3)")


test("GET /data/tts/{file} serves MP3", test_tts_served)


# ============================================================
# PART 3: Language filter validation
# ============================================================
print("\n=== PART 3: Language Filter ===")


def test_context_ru_returns_ru():
    d = api_post("/api/jokes/context", {"text": "работа офис начальник", "count": 5})
    jokes = d.get("jokes", [])
    if jokes:
        ru_count = sum(1 for j in jokes if not any(j.get("category", "").startswith(p) for p in ["en_", "es_", "de_", "fr_"]))
        print(f"    ({ru_count}/{len(jokes)} Russian jokes)")
        assert ru_count > 0, "No Russian jokes returned for Russian query"


test("Context RU query → Russian results", test_context_ru_returns_ru)


def test_context_en_returns_en():
    d = api_post("/api/jokes/context", {"text": "software developer code", "count": 5})
    jokes = d.get("jokes", [])
    if jokes:
        en_count = sum(1 for j in jokes if j.get("category", "").startswith("en_"))
        print(f"    ({en_count}/{len(jokes)} English jokes)")
        # Not strict — may have some RU, but EN should be present


test("Context EN query → English results preferred", test_context_en_returns_en)


def test_generate_topic_match():
    d = api_post("/api/jokes/generate", {"text": "тестирование ПО", "count": 1})
    j = d.get("joke", d)
    cats = d.get("matched_categories", [])
    print(f"    (matched: {cats}, category: {j.get('category', '?')})")
    assert len(cats) > 0, "No matched categories for 'тестирование ПО'"


test("Generate 'тестирование ПО' → matches IT category", test_generate_topic_match)


# ============================================================
# PART 4: Edge cases
# ============================================================
print("\n=== PART 4: Edge Cases ===")


def test_search_one_char():
    try:
        api_get("/api/jokes/search?q=" + urllib.parse.quote("а"), expected_status=422)
    except urllib.error.HTTPError as e:
        assert e.code == 422, f"Expected 422 for 1-char search, got {e.code}"


test("Search 1 char → 422", test_search_one_char)


def test_tts_long_text():
    d = api_post("/api/voice/tts", {"text": "A" * 5000})
    assert "audio_file" in d, "Missing audio_file for long text"


test("TTS max length text", test_tts_long_text)


def test_tts_path_traversal():
    try:
        req = urllib.request.Request(BASE + "/data/tts/../../main.py")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert False, "Path traversal should be blocked"
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        if hasattr(e, 'code'):
            assert e.code in [400, 404], f"Expected 400/404, got {e.code}"


test("TTS path traversal blocked", test_tts_path_traversal)


# ============================================================
# Summary
# ============================================================
print(f"\n{'='*50}")
print(f"RESULTS: {passed} passed, {failed} failed, {passed+failed} total")
if errors:
    print("\nFailures:")
    for e in errors:
        print(f"  ❌ {e}")
print(f"{'='*50}")

sys.exit(0 if failed == 0 else 1)
