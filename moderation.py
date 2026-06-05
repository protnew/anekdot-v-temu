#!/usr/bin/env python3
"""
Автоматическая система модерации для «Анекдот в Тему».
Классы: ProfanityFilter, SpamDetector, ContentModerator.
"""
import re
import math
from collections import Counter

# ---------------------------------------------------------------------------
# Стемы русского мата (~200 основ + производные)
# Храним как frozenset для быстрого lookup
# ---------------------------------------------------------------------------
_PROFANITY_STEMS: frozenset = frozenset({
    # хуй (х*y)
    "хуй", "хуя", "хуе", "хуи", "хуё",
    "хуев", "хуён", "хуяр", "хулю", "хую",
    "хуяк", "хуяра", "хуярить", "хуякать",
    "хуёв", "хуёвый", "хуёво",
    "хуйня", "хуйнёй", "хуйню",
    "похуй", "похую", "похуюсь",
    "нихуй", "нихуя", "нихуё",
    "охуел", "охуела", "охуевать", "охуенно", "охуен", "охуительно",
    "захуел", "захуела", "захуевать",
    "отхуячить", "отхуйярить",
    "прихуярить", "прихуячить",
    "нахуй", "нахуя", "нахуярить",
    "дохуя", "дохуища",
    "хуиплёт", "хуеглот",
    "хуюшки", "хуй",

    # пизда (п*зд)
    "пизда", "пизду", "пизды", "пиздой", "пизде",
    "пиздёж", "пиздёжик",
    "пиздеть", "пиздит", "пиздят", "пиздел", "пиздит",
    "пиздец", "пиздато", "пиздатый",
    "пиздануть", "пизданул",
    "запизделся", "запиздеться",
    "пропиздел", "пропиздеть",
    "спиздить", "спиздил",
    "пиздюк", "пиздюки",
    "пиздабол", "пиздаболия",
    "пиздушить", "пиздошить",
    "опездол", "опизденеть",
    "препиздонь", "подпизднуть",

    # блядь / бля (б*я)
    "блядь", "бля", "бляди", "блядство", "блядский",
    "блядина", "блядовать", "блядун",
    "блядский", "блядски",
    "заблудшая",  # не мат, но иногда контекстно

    # ебать (*бать)
    "ебать", "ебал", "ебала", "ебало", "ебали",
    "ебан", "ебана", "ебаный", "ебаное", "ебаная", "ебаные",
    "ебанутый", "ебанутая", "ебанутых",
    "ебанько", "ебанина",
    "заебал", "заебала", "заебали", "заебись",
    "заебать", "заебаться",
    "наебать", "наебал", "наебалово",
    "выебываться", "выебываться", "выебон",
    "отебись", "отъебись", "отъебаться",
    "уебать", "уебал",
    "проебать", "проебал", "проеб",
    "ебучий", "ебучая", "ебучее",
    "ебля", "ебли",
    "въебать", "въебал",
    "подъебнуть", "подъебывать",
    "ъебать",

    # елда / елдак
    "елда", "елдак", "елдовый",

    # бля (доп)
    "бляха", "бляха-муха",

    # говно (г*вн)
    "говно", "говна", "говне", "говну", "говном",
    "говнистый", "говённый",
    "говняк", "говняной", "говнюк", "говнюкать",

    # залупа (з*луп)
    "залупа", "залупу", "залупы", "залупой",
    "залупить", "залупился",

    # пидор / пидарас (п*дор)
    "пидор", "пидора", "пидоры", "пидором",
    "пидорас", "пидорасы", "пидорка",
    "пидорить", "пидорнуть",
    "педик", "педика", "педики",
    "педераст", "педерастия",

    # дрочить / дрочка (д*ч)
    "дрочить", "дрочу", "дрочит", "дрочат",
    "дрочка", "дрочёный",
    "задрот", "задрота", "задроты",
    "онанизм", "онанист",
    "мудоеб", "мудак", "мудаки", "мудачьё",

    # хер
    "хер", "хера", "херу", "хером", "херы",
    "похер", "похеру", "похерить", "похеру",
    "охерел", "охеренно",
    "нахер", "нахера",

    # мудила
    "мудила", "мудилы", "мудилой",

    # жопа
    "жопа", "жопу", "жопы", "жопой", "жопе",
    "жопник", "жопошник",

    # срать / засранец
    "срать", "сру", "срет", "срут",
    "насрать", "насрал",
    "засрать", "засрал",
    "обосраться", "обосрался",
    "дристать", "дрищу",
    "гавно",

    # член / хуем — убрано: «член комиссии» = FP, контекстно-зависимое

    # курва
    "курва",

    # шлюха
    "шлюха", "шлюхи", "шлюхой", "шлюх",
    "шалава", "шалавой",

    # тварь
    "тварь", "твари", "тварью",

    # сучка / сука
    "сука", "суки", "сукой", "сук",

    # блевать
    "блевать", "блевануть",

    # трахать
    "трахать", "трахаю", "трахает",
    "трахаться", "трахнулся",
    "оттрахать", "оттрахал",

    # пердеть
    "пердеть", "пердёж", "перднул",

    # манда
    "манда", "манду", "мандой",

    # путана
    "путана",

    # дерьмо
    "дерьмо", "дерьма", "дерьмом",

    # ссать
    "ссать", "ссу", "ссет", "ссут",
    "нассать", "нассал",

    # бздеть
    "бздеть", "бздец",

    # перины / прочие
    "хуйня", "пиздюк",

    # ------- Доп. дериваты (добиваем до ~200) -------
    "хуйовина", "хуинь", "хуиню", "хуиня",
    "охуели", "охуеть", "ахуел", "ахуела",
    "вхуякнуть", "вхуяривать",
    "хуюкать", "хуякнуть",
    "пиздуй", "пиздуйте", "пиздуйте",
    "пиздаболия", "пиздоболия",
    "пиздорванец", "пиздобратия",
    "ебанари", "ебань",
    "уёбок", "уёбки", "уебок", "уебки",
    "уебищный", "уебище",
    "ёбарь", "ебарь",
    "ебатория",
    "разъебай", "разъебать",
    "ёбнул", "ебнул", "ёбнуть",
    "выёбываться",
    "ёбик", "ебик",
    "говнодав", "говнограф",
    "залупаться",
    "пидрила", "пидрилка",
    "задрачивать", "задрочить",
    "мудозвон", "мудозвонка",
    "сучара", "сучий",
    "шмарá", "шмара",
    "пиздюган", "пиздюк",
    "ебучка",
    "говномер",
    "ебли́вый",
    "мудосос",
    "хуеСос", "хуесос",
    "пидорг",
    "ебло",
    "ёб",
    "блядунья", "блядство",
    "хуйло", "хуило",
    "пиздато",
    "заебись",
    "охуенно",
    "похую",
    "нихуя",
    "дохуя",
    "пиздец",
    "ахуенно",
    "хуёвый", "хуевый",
    "пиздабол",
    "ебаный", "ёбаный",
    "уебан", "уёбан",

    # гандон / гондон
    "гандон", "гандона", "гандоны", "гандоном",
    "гондон", "гондона", "гондоны",
})


class ProfanityFilter:
    """Фильтр нецензурной лексики для русских текстов."""

    def __init__(self):
        self._stems = _PROFANITY_STEMS
        # Прекомпилируем регулярку для скорости
        self._word_re = re.compile(r'[а-яёА-ЯЁa-zA-Z]+', re.UNICODE)

    # ----- внутренний: нормализация слова -----
    @staticmethod
    def _normalize(word: str) -> str:
        """Приводим к нижнему регистру и заменяем йоты."""
        return word.lower().replace('ё', 'е').replace('й', 'и').replace('ъ', '').replace('ь', '')

    # ----- публичные методы -----
    def _find_bad_words(self, text: str) -> list:
        """Возвращает список найденных нецензурных слов."""
        found = []
        for match in self._word_re.finditer(text):
            word = match.group()
            norm = self._normalize(word)
            # Прямое совпадение
            if norm in self._stems:
                found.append(word)
                continue
            # Проверяем: является ли norm началом или серединой любого стема
            # (ловит производные типа «пизданул», «охуевший» и т.д.)
            for stem in self._stems:
                if len(norm) >= 3 and (norm.startswith(stem[:3]) or stem.startswith(norm[:3])):
                    # Более точная проверка: если пересечение по символам >= 60%
                    common = 0
                    min_len = min(len(norm), len(stem))
                    for i in range(min_len):
                        if norm[i] == stem[i]:
                            common += 1
                    if common / max(len(norm), len(stem)) >= 0.70:
                        found.append(word)
                        break
        return found

    def check(self, text: str) -> dict:
        """
        Проверить текст на мат.

        Returns:
            {
                'passed': bool,       # True если passed
                'score': float,       # 0-1 (0 = чисто, 1 = максимум мата)
                'flags': [str],       # Список найденных слов
                'clean_text': str,    # Текст с заменой ***
            }
        """
        bad_words = self._find_bad_words(text)
        clean = self.filter_text(text)
        total_words = len(self._word_re.findall(text))
        if total_words == 0:
            score = 0.0
        else:
            score = min(len(bad_words) / max(total_words, 1), 1.0)
        return {
            'passed': len(bad_words) == 0,
            'score': round(score, 3),
            'flags': bad_words,
            'clean_text': clean,
        }

    def filter_text(self, text: str) -> str:
        """Заменяет нецензурные слова на ***."""
        def _replacer(match):
            word = match.group()
            norm = self._normalize(word)
            if norm in self._stems:
                return '***'
            # fuzzy check
            for stem in self._stems:
                if len(norm) >= 3 and (norm.startswith(stem[:3]) or stem.startswith(norm[:3])):
                    common = 0
                    min_len = min(len(norm), len(stem))
                    for i in range(min_len):
                        if norm[i] == stem[i]:
                            common += 1
                    if common / max(len(norm), len(stem)) >= 0.70:
                        return '***'
            return word

        return self._word_re.sub(_replacer, text)


class SpamDetector:
    """Детектор спама и дублей."""

    def __init__(self):
        self._history: list = []
        self._url_re = re.compile(
            r'https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.(ru|com|net|org|io|рф)[/\S]*',
            re.IGNORECASE
        )

    @staticmethod
    def _tokenize(text: str) -> Counter:
        """Простая токенизация: слова в нижнем регистре."""
        words = re.findall(r'[а-яёa-z0-9]+', text.lower())
        return Counter(words)

    @staticmethod
    def _cosine_similarity(v1: Counter, v2: Counter) -> float:
        """Косинусное сходство двух Counter-векторов."""
        common = set(v1) & set(v2)
        if not common:
            return 0.0
        dot = sum(v1[w] * v2[w] for w in common)
        mag1 = math.sqrt(sum(v ** 2 for v in v1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in v2.values()))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)

    def is_spam(self, text: str) -> bool:
        """
        Определяет, является ли текст спамом.

        Критерии:
          - cosine similarity > 0.9 с предыдущими текстами (дубликаты)
          - длина < 15 символов
          - >80% CAPS
          - >5 повторений одного слова
          - содержит URL
        """
        # 1. Длина
        if len(text.strip()) < 15:
            return True

        # 2. CAPS > 80%
        alpha_chars = [c for c in text if c.isalpha()]
        if alpha_chars:
            caps_count = sum(1 for c in alpha_chars if c.isupper())
            if caps_count / len(alpha_chars) > 0.8:
                return True

        # 3. Повторы слов > 5 раз
        words = re.findall(r'[а-яёa-z]+', text.lower())
        if words:
            word_counts = Counter(words)
            if word_counts.most_common(1)[0][1] > 5:
                return True

        # 4. URL
        if self._url_re.search(text):
            return True

        # 5. Дубликаты (cosine > 0.9)
        current_vec = self._tokenize(text)
        for prev_text in self._history[-50:]:  # Проверяем последние 50
            prev_vec = self._tokenize(prev_text)
            if self._cosine_similarity(current_vec, prev_vec) > 0.9:
                return True

        # Сохраняем в историю (максимум 200 записей)
        self._history.append(text)
        if len(self._history) > 200:
            self._history = self._history[-200:]
        return False


class ContentModerator:
    """
    Главный модератор контента.

    Пороги severity score:
      < 0.3  → approved
      0.3-0.7 → needs_review
      > 0.7  → rejected
    """

    def __init__(self):
        self.profanity = ProfanityFilter()
        self.spam = SpamDetector()

    def moderate(self, text: str) -> dict:
        """
        Модерация текста.

        Returns:
            {
                'approved': bool,
                'score': float,          # 0-1, общий скор нарушения
                'reasons': [str],        # причины
                'clean_text': str,       # текст с заменой мата
            }
        """
        reasons = []
        total_score = 0.0

        # 1. Profanity check
        p_result = self.profanity.check(text)
        if not p_result['passed']:
            reasons.append(f"profanity: {', '.join(p_result['flags'][:5])}")
            # Базовый штраф 0.35 + пропорциональный (до 0.35) → максимум 0.7
            total_score += 0.35 + p_result['score'] * 0.35

        # 2. Spam check
        if self.spam.is_spam(text):
            reasons.append("spam_detected")
            total_score += 0.4  # Вес спама — 0.4

        # Если пустой текст
        if len(text.strip()) == 0:
            reasons.append("empty_text")
            total_score = 1.0

        total_score = min(total_score, 1.0)

        # Определяем approved/needs_review/rejected
        if total_score > 0.7:
            approved = False
        elif total_score >= 0.3:
            approved = False  # needs_review → не approved автоматически
        else:
            approved = True

        return {
            'approved': approved,
            'score': round(total_score, 3),
            'reasons': reasons,
            'clean_text': p_result['clean_text'],
        }
