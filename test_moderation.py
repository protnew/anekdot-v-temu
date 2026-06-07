#!/usr/bin/env python3
"""Tests for the moderation system of 'Anecdote on Topic'."""
import sys
sys.path.insert(0, ".")

from moderation import ProfanityFilter, SpamDetector, ContentModerator

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


print("\n🧪 Testing Moderation — Anecdote on Topic\n")

# =====================================================================
# ProfanityFilter
# =====================================================================
pf = ProfanityFilter()

# Test 1: Clean text passes
def t1():
    r = pf.check("Колобок повесился")
    assert r['passed'] is True, f"Expected passed, got {r}"
    assert r['score'] == 0.0
    assert r['flags'] == []
test("ProfanityFilter: clean text passes", t1)


# Test 2: Profanity is detected
def t2():
    r = pf.check("Какой же ты хуйло")
    assert r['passed'] is False, f"Expected not passed, got {r}"
    assert len(r['flags']) > 0
    assert r['score'] > 0
test("ProfanityFilter: profanity detected (хуйло)", t2)


# Test 3: filter_text replaces profanity with ***
def t3():
    clean = pf.filter_text("Пошёл нахуй, блядь!")
    assert "нахуй" not in clean, f"Profanity not replaced: {clean}"
    assert "блядь" not in clean, f"Profanity not replaced: {clean}"
    assert "***" in clean
test("ProfanityFilter: filter_text replaces with ***", t3)


# Test 4: Check the word «пизда»
def t4():
    r = pf.check("Ты совсем пизда")
    assert r['passed'] is False
    assert any("пизда" in f.lower() for f in r['flags']), f"Expected 'пизда' in flags, got {r['flags']}"
test("ProfanityFilter: пизда", t4)


# Test 5: Check «ебать»
def t5():
    r = pf.check("Да ебал я эту работу")
    assert r['passed'] is False
    assert r['score'] > 0
test("ProfanityFilter: ебал", t5)


# Test 6: Check «говно»
def t6():
    r = pf.check("Какое же это говно")
    assert r['passed'] is False
    assert len(r['flags']) > 0
test("ProfanityFilter: говно", t6)


# Test 7: Check «бля»
def t7():
    r = pf.check("Бля, вот это поворот!")
    assert r['passed'] is False
test("ProfanityFilter: бля", t7)


# Test 8: Derivative «охуенно»
def t8():
    r = pf.check("Это просто охуенно!")
    assert r['passed'] is False
test("ProfanityFilter: охуенно (derivative)", t8)


# Test 9: Derivative «заебись»
def t9():
    r = pf.check("Всё просто заебись!")
    assert r['passed'] is False
test("ProfanityFilter: заебись (derivative)", t9)


# Test 10: Derivative «пиздец»
def t10():
    r = pf.check("Полный пиздец случился")
    assert r['passed'] is False
test("ProfanityFilter: пиздец (derivative)", t10)


# Test 11: clean_text preserves clean words
def t11():
    r = pf.check("Колобок пошёл гулять и не вернулся")
    assert r['clean_text'] == "Колобок пошёл гулять и не вернулся"
test("ProfanityFilter: clean_text = original for clean input", t11)


# Test 12: Multiple profane words
def t12():
    r = pf.check("Пиздец какой хуйло бля")
    assert r['passed'] is False
    assert len(r['flags']) >= 2, f"Expected 2+ flags, got {r['flags']}"
test("ProfanityFilter: multiple profanities in one text", t12)


# =====================================================================
# SpamDetector
# =====================================================================
sd = SpamDetector()

# Test 13: Short text < 15 chars = spam
def t13():
    assert sd.is_spam("Коротко") is True
test("SpamDetector: short text <15 chars", t13)


# Test 14: Normal text is not spam
def t14():
    sd2 = SpamDetector()  # fresh instance
    result = sd2.is_spam("Программист зашёл в бар и заказал пиво, а бармен сказал — вам нельзя")
    assert result is False
test("SpamDetector: normal text is not spam", t14)


# Test 15: Text with URL = spam
def t15():
    sd3 = SpamDetector()
    result = sd3.is_spam("Заходи на сайт https://scam-site.ru и получи приз бесплатно")
    assert result is True
test("SpamDetector: URL in text = spam", t15)


# Test 16: >80% CAPS = spam
def t16():
    sd4 = SpamDetector()
    result = sd4.is_spam("КУПИ СЕЙЧАС АКЦИЯ СКИДКА БЕСПЛАТНО СРОЧНО!!!!!!!")
    assert result is True
test("SpamDetector: >80% CAPS = spam", t16)


# Test 17: >5 repetitions of the same word = spam
def t17():
    sd5 = SpamDetector()
    result = sd5.is_spam("купи купи купи купи купи купи купи прямо сейчас")
    assert result is True
test("SpamDetector: >5 word repetitions = spam", t17)


# Test 18: Duplicates (cosine > 0.9)
def t18():
    sd6 = SpamDetector()
    text1 = "Программист зашёл в бар и заказал пиво"
    sd6.is_spam(text1)  # add to history
    # Nearly identical text — duplicate
    text2 = "Программист зашёл в бар и заказал пиво"
    result = sd6.is_spam(text2)
    assert result is True
test("SpamDetector: duplicates (cosine>0.9)", t18)


# Test 19: Different texts — not duplicates
def t19():
    sd7 = SpamDetector()
    sd7.is_spam("Программист зашёл в бар и заказал пиво")
    result = sd7.is_spam("Колобок пошёл по лесу и встретил зайца, который пел песни")
    assert result is False
test("SpamDetector: different texts — not duplicates", t19)


# =====================================================================
# ContentModerator
# =====================================================================
cm = ContentModerator()

# Test 20: Clean joke is approved
def t20():
    r = cm.moderate("Колобок повесился. Вот и сказочке конец.")
    assert r['approved'] is True, f"Expected approved, got {r}"
    assert r['score'] < 0.3
    assert r['reasons'] == []
test("ContentModerator: clean joke is approved", t20)


# Test 21: Text with profanity is rejected or needs_review
def t21():
    cm2 = ContentModerator()
    r = cm2.moderate("Ты что, совсем пизданулся, блядь?!")
    assert r['approved'] is False, f"Expected not approved, got {r}"
    assert len(r['reasons']) > 0
test("ContentModerator: profanity → not approved", t21)


# Test 22: Short text + profanity = high score
def t22():
    cm3 = ContentModerator()
    r = cm3.moderate("Хуй")
    assert r['approved'] is False
    assert r['score'] > 0.5
test("ContentModerator: short profanity → high score", t22)


# Test 23: Text with URL → not approved
def t23():
    cm4 = ContentModerator()
    r = cm4.moderate("Заходи на https://free-stuff.com и забирай подарок прямо сейчас срочно!")
    assert r['approved'] is False
    assert "spam_detected" in r['reasons']
test("ContentModerator: URL → not approved", t23)


# Test 24: Empty text → rejected
def t24():
    cm5 = ContentModerator()
    r = cm5.moderate("")
    assert r['approved'] is False
    assert "empty_text" in r['reasons']
test("ContentModerator: empty text → rejected", t24)


# Test 25: Score is in the range [0, 1]
def t25():
    cm6 = ContentModerator()
    texts = [
        "Колобок пошёл гулять и не вернулся",
        "Какой же ты хуйло",
        "Бля, вот это поворот!",
        "Программист зашёл в бар",
    ]
    for t in texts:
        r = cm6.moderate(t)
        assert 0.0 <= r['score'] <= 1.0, f"Score out of range: {r['score']}"
test("ContentModerator: score ∈ [0, 1]", t25)


# Test 26: clean_text is always returned
def t26():
    cm7 = ContentModerator()
    r = cm7.moderate("Ты ебаный пиздюк, иди нахуй отсюда")
    assert r['clean_text'] is not None
    assert "***" in r['clean_text']
    assert "ебан" not in r['clean_text'].lower()
test("ContentModerator: clean_text is profanity-free", t26)


# =====================================================================
print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed out of {passed+failed}")
if failed == 0:
    print("🎉 ALL TESTS PASSED!")
else:
    print("⚠️ Some tests failed!")
    sys.exit(1)
