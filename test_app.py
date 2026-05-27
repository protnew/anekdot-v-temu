#!/usr/bin/env python3
"""Test suite for Анекдот в тему app"""
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

print("\n🧪 Testing Анекдот в тему API\n")

# Test 1: Stats
def t1():
    r = client.get("/api/stats")
    assert r.status_code == 200, f"Status {r.status_code}"
    d = r.json()
    assert d["total_jokes"] == 60, f"Expected 60 jokes, got {d['total_jokes']}"
    assert d["categories"] == 16, f"Expected 16 categories, got {d['categories']}"
    assert d["avg_rating"] > 0
test("Stats endpoint", t1)

# Test 2: Categories
def t2():
    r = client.get("/api/categories")
    assert r.status_code == 200
    d = r.json()
    assert len(d) == 16
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

# Test 9: Favorites
def t9():
    r = client.post("/api/favorites", json={"joke_id": 8})
    assert r.status_code == 200
    r = client.get("/api/favorites")
    assert len(r.json()["jokes"]) >= 1
    # Cleanup
    client.delete("/api/favorites/8")
test("Favorites CRUD", t9)

# Test 10: Rating
def t10():
    r = client.post("/api/rate", json={"joke_id": 11, "rating": 5.0})
    assert r.status_code == 200
    assert r.json()["new_rating"] > 0
test("Rating", t10)

# Test 11: HTML page
def t11():
    r = client.get("/")
    assert r.status_code == 200
    assert "Анекдот в тему" in r.text
    assert "contextInput" in r.text
test("HTML page loads", t11)

# Test 12: Generate
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

# Test 14: No match fallback
def t14():
    r = client.post("/api/jokes/context", json={"text": "абракадабраxyz123", "count": 1})
    d = r.json()
    assert len(d["jokes"]) > 0  # Should return random joke
test("No-match fallback", t14)

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed out of {passed+failed}")
if failed == 0:
    print("🎉 ALL TESTS PASSED!")
else:
    print("⚠️ Some tests failed!")
    sys.exit(1)
