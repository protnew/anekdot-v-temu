#!/usr/bin/env python3
"""
Automatic moderation system for "Anekdot v Temu" (Joke on Topic).
Classes: ProfanityFilter, SpamDetector, ContentModerator.
"""
import re
import math
from collections import Counter

# ---------------------------------------------------------------------------
# Russian profanity stems (~200 roots + derivatives)
# Stored as frozenset for fast lookup
# ---------------------------------------------------------------------------
_PROFANITY_STEMS: frozenset = frozenset({
    # dick root and derivatives
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

    # cunt root and derivatives
    "пизда", "пизду", "пизды", "пиздой", "пизде",
    "пиздёж", "пиздёжик",
    "пиздеть", "пиздит", "пиздят", "пиздел",
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

    # whore / damn root and derivatives
    "блядь", "бля", "бляди", "блядство", "блядский",
    "блядина", "блядовать", "блядун",
    "блядский", "блядски",
    "заблудшая",  # not profanity, but sometimes contextual

    # fuck root and derivatives
    "ебать", "ебал", "ебала", "ебало", "ебали",
    "ебан", "ебана", "ебаный", "ебаное", "ебаная", "ебаные",
    "ебанутый", "ебанутая", "ебанутых",
    "ебанько", "ебанина",
    "заебал", "заебала", "заебали", "заебись",
    "заебать", "заебаться",
    "наебать", "наебал", "наебалово",
    "выебываться", "выебон",
    "отебись", "отъебись", "отъебаться",
    "уебать", "уебал",
    "проебать", "проебал", "проеб",
    "ебучий", "ебучая", "ебучее",
    "ебля", "ебли",
    "въебать", "въебал",
    "подъебнуть", "подъебывать",
    "ъебать",

    # prick
    "елда", "елдак", "елдовый",

    # damn (additional)
    "бляха", "бляха-муха",

    # shit root and derivatives
    "говно", "говна", "говне", "говну", "говном",
    "говнистый", "говённый",
    "говняк", "говняной", "говнюк", "говнюкать",

    # foreskin root and derivatives
    "залупа", "залупу", "залупы", "залупой",
    "залупить", "залупился",

    # faggot / fag root and derivatives
    "пидор", "пидора", "пидоры", "пидором",
    "пидорас", "пидорасы", "пидорка",
    "пидорить", "пидорнуть",
    "педик", "педика", "педики",
    "педераст", "педерастия",

    # jerk off root and derivatives
    "дрочить", "дрочу", "дрочит", "дрочат",
    "дрочка", "дрочёный",
    "задрот", "задрота", "задроты",
    "онанизм", "онанист",
    "мудоеб", "мудак", "мудаки", "мудачьё",

    # prick (alt)
    "хер", "хера", "херу", "хером", "херы",
    "похер", "похеру", "похерить", "похеру",
    "охерел", "охеренно",
    "нахер", "нахера",

    # dumbass
    "мудила", "мудилы", "мудилой",

    # ass
    "жопа", "жопу", "жопы", "жопой", "жопе",
    "жопник", "жопошник",

    # shit / shitter
    "срать", "сру", "срет", "срут",
    "насрать", "насрал",
    "засрать", "засрал",
    "обосраться", "обосрался",
    "дристать", "дрищу",
    "гавно",

    # "member" stem removed: "committee member" = false positive, context-dependent

    # whore (Polish loanword)
    "курва",

    # slut
    "шлюха", "шлюхи", "шлюхой", "шлюх",
    "шалава", "шалавой",

    # creature / bitch
    "тварь", "твари", "тварью",

    # bitch
    "сука", "суки", "сукой", "сук",

    # vomit
    "блевать", "блевануть",

    # fuck / bang
    "трахать", "трахаю", "трахает",
    "трахаться", "трахнулся",
    "оттрахать", "оттрахал",

    # fart
    "пердеть", "пердёж", "перднул",

    # cunt (alt)
    "манда", "манду", "мандой",

    # prostitute
    "путана",

    # crap
    "дерьмо", "дерьма", "дерьмом",

    # piss
    "ссать", "ссу", "ссет", "ссут",
    "нассать", "нассал",

    # stink / fart (alt)
    "бздеть", "бздец",


    # ------- Additional derivatives (bringing total to ~200) -------
    "хуйовина", "хуинь", "хуиню", "хуиня",
    "охуели", "охуеть", "ахуел", "ахуела",
    "вхуякнуть", "вхуяривать",
    "хуюкать", "хуякнуть",
    "пиздуй", "пиздуйте",
    "пиздоболия",
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

    # condom
    "гандон", "гандона", "гандоны", "гандоном",
    "гондон", "гондона", "гондоны",
})


class ProfanityFilter:
    """Profanity filter for Russian texts."""

    def __init__(self):
        self._stems = _PROFANITY_STEMS
        # Pre-compile regex for speed
        self._word_re = re.compile(r'[а-яёА-ЯЁa-zA-Z]+', re.UNICODE)

    # ----- internal: word normalization -----
    @staticmethod
    def _normalize(word: str) -> str:
        """Convert to lowercase and replace iotated letters."""
        return word.lower().replace('ё', 'е').replace('й', 'и').replace('ъ', '').replace('ь', '')

    # ----- public methods -----
    def _find_bad_words(self, text: str) -> list:
        """Returns a list of found profane words."""
        found = []
        for match in self._word_re.finditer(text):
            word = match.group()
            norm = self._normalize(word)
            # Direct match
            if norm in self._stems:
                found.append(word)
                continue
            # Check if norm is a prefix or infix of any stem
            # (catches derivatives via fuzzy matching)
            for stem in self._stems:
                if len(norm) >= 3 and (norm.startswith(stem[:3]) or stem.startswith(norm[:3])):
                    # More precise check: if character overlap >= 60%
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
        Check text for profanity.

        Returns:
            {
                'passed': bool,       # True if passed
                'score': float,       # 0-1 (0 = clean, 1 = maximum profanity)
                'flags': [str],       # List of found words
                'clean_text': str,    # Text with *** replacements
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
        """Replaces profane words with ***."""
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
    """Spam and duplicate detector."""

    def __init__(self):
        self._history: list = []
        self._url_re = re.compile(
            r'https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.(ru|com|net|org|io|рф)[/\S]*',
            re.IGNORECASE
        )

    @staticmethod
    def _tokenize(text: str) -> Counter:
        """Simple tokenization: words in lowercase."""
        words = re.findall(r'[а-яёa-z0-9]+', text.lower())
        return Counter(words)

    @staticmethod
    def _cosine_similarity(v1: Counter, v2: Counter) -> float:
        """Cosine similarity of two Counter vectors."""
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
        Determines whether the text is spam.

        Criteria:
          - cosine similarity > 0.9 with previous texts (duplicates)
          - length < 15 characters
          - >80% CAPS
          - >5 repetitions of a single word
          - contains URL
        """
        # 1. Length
        if len(text.strip()) < 15:
            return True

        # 2. CAPS > 80%
        alpha_chars = [c for c in text if c.isalpha()]
        if alpha_chars:
            caps_count = sum(1 for c in alpha_chars if c.isupper())
            if caps_count / len(alpha_chars) > 0.8:
                return True

        # 3. Word repetitions > 5 times
        words = re.findall(r'[а-яёa-z]+', text.lower())
        if words:
            word_counts = Counter(words)
            if word_counts.most_common(1)[0][1] > 5:
                return True

        # 4. URL
        if self._url_re.search(text):
            return True

        # 5. Duplicates (cosine > 0.9)
        current_vec = self._tokenize(text)
        for prev_text in self._history[-50:]:  # Check the last 50
            prev_vec = self._tokenize(prev_text)
            if self._cosine_similarity(current_vec, prev_vec) > 0.9:
                return True

        # Save to history (max 200 entries)
        self._history.append(text)
        if len(self._history) > 200:
            self._history = self._history[-200:]
        return False


class ContentModerator:
    """
    Main content moderator.

    Severity score thresholds:
      < 0.3  → approved
      0.3-0.7 → needs_review
      > 0.7  → rejected
    """

    def __init__(self):
        self.profanity = ProfanityFilter()
        self.spam = SpamDetector()

    def moderate(self, text: str) -> dict:
        """
        Moderate text.

        Returns:
            {
                'approved': bool,
                'score': float,          # 0-1, overall violation score
                'reasons': [str],        # reasons
                'clean_text': str,       # text with profanity replaced
            }
        """
        reasons = []
        total_score = 0.0

        # 1. Profanity check
        p_result = self.profanity.check(text)
        if not p_result['passed']:
            reasons.append(f"profanity: {', '.join(p_result['flags'][:5])}")
            # Base penalty 0.35 + proportional (up to 0.35) → max 0.7
            total_score += 0.35 + p_result['score'] * 0.35

        # 2. Spam check
        if self.spam.is_spam(text):
            reasons.append("spam_detected")
            total_score += 0.4  # Spam weight — 0.4

        # If empty text
        if len(text.strip()) == 0:
            reasons.append("empty_text")
            total_score = 1.0

        total_score = min(total_score, 1.0)

        # Determine approved/needs_review/rejected
        if total_score > 0.7:
            approved = False
        elif total_score >= 0.3:
            approved = False  # needs_review → not auto-approved
        else:
            approved = True

        return {
            'approved': approved,
            'score': round(total_score, 3),
            'reasons': reasons,
            'clean_text': p_result['clean_text'],
        }
