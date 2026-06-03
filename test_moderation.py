#!/usr/bin/env python3
"""Тесты для системы модерации «Анекдот в Тему»."""
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


print("\n🧪 Testing Модерация — Анекдот в Тему\n")

# =====================================================================
# ProfanityFilter
# =====================================================================
pf = ProfanityFilter()

# Test 1: Чистый текст проходит
def t1():
    r = pf.check("Колобок повесился")
    assert r['passed'] is True, f"Expected passed, got {r}"
    assert r['score'] == 0.0
    assert r['flags'] == []
test("ProfanityFilter: чистый текст проходит", t1)


# Test 2: Мат обнаруживается
def t2():
    r = pf.check("Какой же ты хуйло")
    assert r['passed'] is False, f"Expected not passed, got {r}"
    assert len(r['flags']) > 0
    assert r['score'] > 0
test("ProfanityFilter: мат обнаруживается (хуйло)", t2)


# Test 3: filter_text заменяет мат на ***
def t3():
    clean = pf.filter_text("Пошёл нахуй, блядь!")
    assert "нахуй" not in clean, f"Мат не заменён: {clean}"
    assert "блядь" not in clean, f"Мат не заменён: {clean}"
    assert "***" in clean
test("ProfanityFilter: filter_text заменяет на ***", t3)


# Test 4: Проверка слова «пизда»
def t4():
    r = pf.check("Ты совсем пизда")
    assert r['passed'] is False
    assert any("пизда" in f.lower() for f in r['flags']), f"Expected 'пизда' in flags, got {r['flags']}"
test("ProfanityFilter: пизда", t4)


# Test 5: Проверка «ебать»
def t5():
    r = pf.check("Да ебал я эту работу")
    assert r['passed'] is False
    assert r['score'] > 0
test("ProfanityFilter: ебал", t5)


# Test 6: Проверка «говно»
def t6():
    r = pf.check("Какое же это говно")
    assert r['passed'] is False
    assert len(r['flags']) > 0
test("ProfanityFilter: говно", t6)


# Test 7: Проверка «бля»
def t7():
    r = pf.check("Бля, вот это поворот!")
    assert r['passed'] is False
test("ProfanityFilter: бля", t7)


# Test 8: Производное «охуенно»
def t8():
    r = pf.check("Это просто охуенно!")
    assert r['passed'] is False
test("ProfanityFilter: охуенно (производное)", t8)


# Test 9: Производное «заебись»
def t9():
    r = pf.check("Всё просто заебись!")
    assert r['passed'] is False
test("ProfanityFilter: заебись (производное)", t9)


# Test 10: Производное «пиздец»
def t10():
    r = pf.check("Полный пиздец случился")
    assert r['passed'] is False
test("ProfanityFilter: пиздец (производное)", t10)


# Test 11: clean_text сохраняет чистые слова
def t11():
    r = pf.check("Колобок пошёл гулять и не вернулся")
    assert r['clean_text'] == "Колобок пошёл гулять и не вернулся"
test("ProfanityFilter: clean_text = оригинал для чистого", t11)


# Test 12: Несколько матерных слов
def t12():
    r = pf.check("Пиздец какой хуйло бля")
    assert r['passed'] is False
    assert len(r['flags']) >= 2, f"Expected 2+ flags, got {r['flags']}"
test("ProfanityFilter: несколько матов в одном тексте", t12)


# =====================================================================
# SpamDetector
# =====================================================================
sd = SpamDetector()

# Test 13: Короткий текст < 15 символов = спам
def t13():
    assert sd.is_spam("Коротко") is True
test("SpamDetector: короткий текст <15 символов", t13)


# Test 14: Нормальный текст не спам
def t14():
    sd2 = SpamDetector()  # fresh instance
    result = sd2.is_spam("Программист зашёл в бар и заказал пиво, а бармен сказал — вам нельзя")
    assert result is False
test("SpamDetector: нормальный текст не спам", t14)


# Test 15: Текст с URL = спам
def t15():
    sd3 = SpamDetector()
    result = sd3.is_spam("Заходи на сайт https://scam-site.ru и получи приз бесплатно")
    assert result is True
test("SpamDetector: URL в тексте = спам", t15)


# Test 16: >80% CAPS = спам
def t16():
    sd4 = SpamDetector()
    result = sd4.is_spam("КУПИ СЕЙЧАС АКЦИЯ СКИДКА БЕСПЛАТНО СРОЧНО!!!!!!!")
    assert result is True
test("SpamDetector: >80% CAPS = спам", t16)


# Test 17: >5 повторов одного слова = спам
def t17():
    sd5 = SpamDetector()
    result = sd5.is_spam("купи купи купи купи купи купи купи прямо сейчас")
    assert result is True
test("SpamDetector: >5 повторов слова = спам", t17)


# Test 18: Дубликаты (cosine > 0.9)
def t18():
    sd6 = SpamDetector()
    text1 = "Программист зашёл в бар и заказал пиво"
    sd6.is_spam(text1)  # добавляем в историю
    # Почти тот же текст — дубль
    text2 = "Программист зашёл в бар и заказал пиво"
    result = sd6.is_spam(text2)
    assert result is True
test("SpamDetector: дубликаты (cosine>0.9)", t18)


# Test 19: Разные тексты — не дубликаты
def t19():
    sd7 = SpamDetector()
    sd7.is_spam("Программист зашёл в бар и заказал пиво")
    result = sd7.is_spam("Колобок пошёл по лесу и встретил зайца, который пел песни")
    assert result is False
test("SpamDetector: разные тексты — не дубликаты", t19)


# =====================================================================
# ContentModerator
# =====================================================================
cm = ContentModerator()

# Test 20: Чистый анекдот одобрен
def t20():
    r = cm.moderate("Колобок повесился. Вот и сказочке конец.")
    assert r['approved'] is True, f"Expected approved, got {r}"
    assert r['score'] < 0.3
    assert r['reasons'] == []
test("ContentModerator: чистый анекдот одобрен", t20)


# Test 21: Текст с матом отклонён или needs_review
def t21():
    cm2 = ContentModerator()
    r = cm2.moderate("Ты что, совсем пизданулся, блядь?!")
    assert r['approved'] is False, f"Expected not approved, got {r}"
    assert len(r['reasons']) > 0
test("ContentModerator: мат → не одобрен", t21)


# Test 22: Короткий текст + мат = высокий скор
def t22():
    cm3 = ContentModerator()
    r = cm3.moderate("Хуй")
    assert r['approved'] is False
    assert r['score'] > 0.5
test("ContentModerator: короткий мат → высокий скор", t22)


# Test 23: Текст с URL → не одобрен
def t23():
    cm4 = ContentModerator()
    r = cm4.moderate("Заходи на https://free-stuff.com и забирай подарок прямо сейчас срочно!")
    assert r['approved'] is False
    assert "spam_detected" in r['reasons']
test("ContentModerator: URL → не одобрен", t23)


# Test 24: Пустой текст → rejected
def t24():
    cm5 = ContentModerator()
    r = cm5.moderate("")
    assert r['approved'] is False
    assert "empty_text" in r['reasons']
test("ContentModerator: пустой текст → rejected", t24)


# Test 25: Score в диапазоне [0, 1]
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


# Test 26: clean_text всегда возвращается
def t26():
    cm7 = ContentModerator()
    r = cm7.moderate("Ты ебаный пиздюк, иди нахуй отсюда")
    assert r['clean_text'] is not None
    assert "***" in r['clean_text']
    assert "ебан" not in r['clean_text'].lower()
test("ContentModerator: clean_text очищен от мата", t26)


# =====================================================================
print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed out of {passed+failed}")
if failed == 0:
    print("🎉 ALL TESTS PASSED!")
else:
    print("⚠️ Some tests failed!")
    sys.exit(1)
