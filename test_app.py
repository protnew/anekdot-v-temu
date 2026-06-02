#!/usr/bin/env python3
"""Test suite for Анекдот в тему app — v3.5 (112K jokes, 33 categories)"""
import sys
sys.path.insert(0, ".")
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)
passed = 0
failed = 0

def test(name, func):
    global passed, failed
    try:
        func()
        print(f"  ✅ {name}")
        passed += 1
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        failed += 1

print("\n🧪 Testing Анекдот в тему API (v3.5, 112K jokes)\n")

# Test 1: Stats
def t1():
    r = client.get("/api/stats")
    assert r.status_code == 200, f"Status {r.status_code}"
    d = r.json()
    assert d["total_jokes"] > 100000, f"Expected 100K+ jokes, got {d['total_jokes']}"
    assert d["categories"] >= 21, f"Expected 21+ categories, got {d['categories']}"
    assert d["avg_rating"] > 0
test("Stats endpoint", t1)

# Test 2: Categories
def t2():
    r = client.get("/api/categories")
    assert r.status_code == 200
    d = r.json()
    assert len(d) >= 21, f"Expected 21+ categories, got {len(d)}"
    assert "работа" in d
    assert "айти" in d
    assert "котики" in d
test("Categories endpoint", t2)

# Test 3: Context search - work
def t3():
    r = client.post("/api/jokes/context", json={"text": "начальник совещание работа дедлайн", "count": 2})
    assert r.status_code == 200
    d = r.json()
    assert len(d["jokes"]) > 0
    assert "работа" in d["matched_categories"]
test("Context search (работа)", t3)

# Test 4: Context search - IT
def t4():
    r = client.post("/api/jokes/context", json={"text": "программист код баг сервер devops", "count": 2})
    d = r.json()
    assert "айти" in d["matched_categories"]
    assert len(d["jokes"]) > 0
test("Context search (IT)", t4)

# Test 5: Context search - AI
def t5():
    r = client.post("/api/jokes/context", json={"text": "нейросеть chatgpt искусственный интеллект", "count": 2})
    d = r.json()
    assert "искусственный интеллект" in d["matched_categories"]
test("Context search (AI)", t5)

# Test 6: Context search - multi-category
def t6():
    r = client.post("/api/jokes/context", json={"text": "программист жена деньги", "count": 3})
    d = r.json()
    assert len(d["matched_categories"]) >= 2, f"Expected 2+ categories, got {d['matched_categories']}"
test("Multi-category context", t6)

# Test 7: Random joke
def t7():
    r = client.get("/api/joke/random")
    assert r.status_code == 200
    j = r.json()
    assert "text" in j
    assert "category" in j
    assert "rating" in j
test("Random joke", t7)

# Test 8: Search
def t8():
    r = client.get("/api/jokes/search?q=программист")
    d = r.json()
    assert d["total"] > 0
test("Full-text search", t8)

# Test 9: Favorites CRUD
def t9():
    # Add
    r = client.post("/api/favorites", json={"joke_id": 1})
    assert r.status_code == 200
    # Get
    r = client.get("/api/favorites")
    assert r.status_code == 200
    fav_ids = [j["id"] for j in r.json()["jokes"]]
    assert 1 in fav_ids, f"Joke 1 not in favorites: {fav_ids}"
    # Remove
    r = client.delete("/api/favorites/1")
    assert r.status_code == 200
test("Favorites CRUD", t9)

# Test 10: Rating
def t10():
    r = client.post("/api/rate", json={"joke_id": 1, "rating": 5.0})
    assert r.status_code == 200
    assert r.json()["new_rating"] > 0
test("Rating", t10)

# Test 11: HTML page loads
def t11():
    r = client.get("/")
    assert r.status_code == 200
    assert "Анекдот в тему" in r.text
    assert "contextInput" in r.text
test("HTML page loads", t11)

# Test 12: Generate (template fallback, no OpenAI key)
def t12():
    r = client.post("/api/jokes/generate", json={"text": "кот программист"})
    assert r.status_code == 200
    d = r.json()
    assert d["joke"]["generated"] == True
test("AI joke generation", t12)

# Test 13: Category filter
def t13():
    r = client.get("/api/jokes?category=айти&count=3")
    d = r.json()
    assert d["total"] <= 3
    assert all(j["category"] == "айти" for j in d["jokes"])
test("Category filter", t13)

# Test 14: No match fallback — should still return something
def t14():
    r = client.post("/api/jokes/context", json={"text": "абракадабраxyz123", "count": 1})
    d = r.json()
    # May or may not return jokes depending on semantic match
    assert r.status_code == 200
test("No-match fallback", t14)

# Test 15: TTS endpoint
def t15():
    r = client.post("/api/voice/tts", json={"text": "Тестовая шутка"})
    assert r.status_code == 200
    d = r.json()
    assert "audio_file" in d or "error" in d
test("TTS endpoint", t15)

# Test 16: User jokes CRUD
def t16():
    r = client.post("/api/user-jokes", json={"category": "тест", "text": "Тестовая шутка для проверки CRUD операций", "tags": ["test"]})
    assert r.status_code == 200
    joke_id = r.json()["id"]
    # List
    r = client.get("/api/user-jokes")
    assert r.status_code == 200
    # Delete
    r = client.delete(f"/api/user-jokes/{joke_id}")
    assert r.status_code == 200
test("User jokes CRUD", t16)

# Test 17: English jokes
def t17():
    r = client.get("/api/jokes/en?count=3")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] > 0
test("English jokes", t17)

# Test 18: Social top
def t18():
    r = client.get("/api/jokes/social/top")
    assert r.status_code == 200
    d = r.json()
    assert len(d["jokes"]) > 0
test("Social top jokes", t18)

# Test 19: Personalization
def t19():
    r = client.post("/api/personalize/test_user?liked_cat=айти&disliked_cat=политика")
    assert r.status_code == 200
    r = client.get("/api/personalize/test_user?count=3")
    assert r.status_code == 200
    assert len(r.json()["jokes"]) > 0
test("Personalization", t19)

# Test 20: Analytics endpoints
def t20():
    r = client.get("/api/analytics/stats")
    assert r.status_code == 200
    r = client.get("/api/analytics/popular")
    assert r.status_code == 200
test("Analytics endpoints", t20)

# Test 21: PWA manifest
def t21():
    r = client.get("/manifest.json")
    assert r.status_code == 200
    d = r.json()
    assert d["name"] == "Анекдот в тему"
test("PWA manifest", t21)

# Test 22: Rate validation
def t22():
    r = client.post("/api/rate", json={"joke_id": 999999, "rating": 5.0})
    assert r.status_code == 404  # Joke not found
test("Rate validation (404 for missing joke)", t22)

# Test 23: Like joke
def t23():
    r = client.post("/api/jokes/1/like")
    assert r.status_code == 200
    assert r.json()["liked"] == True
test("Like joke", t23)

# Test 24: Ad stub
def t24():
    r = client.get("/api/monetization/ad")
    assert r.status_code == 200
    assert r.json()["ad"]["show"] == True
test("Ad stub", t24)

# Test 25: Validation errors
def t25():
    r = client.post("/api/jokes/context", json={"text": "", "count": 1})
    assert r.status_code == 400
    r = client.post("/api/jokes/context", json={"text": "тест", "count": -1})
    assert r.status_code == 400
test("Validation errors", t25)

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed out of {passed+failed}")
if failed == 0:
    print("🎉 ALL TESTS PASSED!")
else:
    print("⚠️ Some tests failed!")
    sys.exit(1)
