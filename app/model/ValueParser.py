import re
from model.GuessContext import GuessContext
from utils.Utils import to_english
from typing import Optional


class ValueParser():

    source_type: str = "pdf"

    # Titles that look like job titles but are actually category descriptions
    _non_job_titles: set = {
        "Décès beaux-parents",
        "Mariage du salarié",
        "Mariage d'un enfant",
    }

    # Prefix that identifies category-description rows (handled by _is_paragraph anyway,
    # but kept as a fast-path check)
    _EMPLOIS_PREFIX = "Emplois qui requièrent"

    def __init__(self, source_type: str = "pdf"):
        self.source_type = source_type
        self._conform_table: dict = {
            "job_title":        self._split_genders,
            "job_title_male":   self._lower_capitalise,
            "job_title_female": self._lower_capitalise,
            "sector":           self._lower_capitalise,
            "category":         self._conform_category,
            "position":         self._lower_capitalise,
            "monthly_salary":   self._extract_number,
            "weekly_salary":    self._extract_number,
            "daily_salary":     self._extract_number,
            "is_cadre":         self._cadre_to_bool,
        }
        self._content_guess_table: dict = {
            "job_title":      [self._is_job_title],
            "category":       [self._is_roman_AB],
            "is_cadre":       [self._is_NC_or_C],
            "definition":     [self._is_definition],
            "position":       [self._is_chef_or_confirme],
            "sector":         [self._is_sector],
            "monthly_salary": [self._is_salary, self._greater_than_900],
            "weekly_salary":  [self._is_salary, self._greater_than_400, self._lower_than_1000],
            "daily_salary":   [self._is_salary, self._lower_than_300],
        }

    # ─────────────────────────────────────────
    # Number extraction
    # ─────────────────────────────────────────

    def _extract_number(self, text) -> float | None:
        if not isinstance(text, str):
            return text
        # collapse spaces used as thousand separators
        cleaned = re.sub(r'(?<=\d) (?=\d)', '', text)
        match = re.search(r'-?\d+(?:\.\d+)?', cleaned)
        return float(match.group()) if match else None

    # ─────────────────────────────────────────
    # Content classifiers
    # ─────────────────────────────────────────

    def _contains_link_words(self, text: str) -> bool:
        link_words = [" de ", " une ", " ou ", " qui ", " le ", " un ", " avec "]
        return any(w in text for w in link_words)

    def _is_paragraph(self, context: GuessContext) -> bool:
        s = context.value.strip()
        if s.startswith(self._EMPLOIS_PREFIX):
            return False
        if len(s) >= 40:
            return self._contains_link_words(s) or bool(re.search(r'[.!?()]', s))
        if len(s) >= 15:
            return self._contains_link_words(s)
        return False

    def _is_definition(self, context: GuessContext) -> bool:
        if self._from_admin_table(context):
            return False
        return self._is_paragraph(context)

    def _is_job_title(self, context: GuessContext) -> bool:
        s = context.value.strip()

        if len(s) < 2:
            return False
        if s in self._non_job_titles:
            return False
        if s.startswith(self._EMPLOIS_PREFIX):
            return False
        if self._is_roman_AB(context):
            return False
        if self._is_paragraph(context):
            return False
        if self._is_NC_or_C(context):
            return False

        if self._from_admin_table(context) or self.source_type == "html":
            # HTML / admin tables: title-cased (first letter up, second down)
            return self._is_title_case_start(s) and not self._is_roman_AB(context)

        # PDF tables: all-uppercase, min length 5
        pattern = r'^[A-ZÀ-Ÿ0-9\' /\\\n]+$'
        return bool(
            re.match(pattern, s)
            and len(s) > 5
            and not self._is_chef_or_confirme(context)
            and not self._is_sector(context)
        )

    def _is_title_case_start(self, s: str) -> bool:
        """First char uppercase, second char lowercase — e.g. 'Monteur'."""
        return len(s) >= 2 and self.is_upper(s[0]) and not self.is_upper(s[1])

    def _is_roman_AB(self, context: GuessContext) -> bool:
        return context.value.strip() in {
            "I", "II", "III", "IV", "V",
            "IIIA", "III A", "IIIB", "III B",
            "Hors catégorie",
        }

    def _is_NC_or_C(self, context: GuessContext) -> bool:
        return context.value.strip().upper() in {"NC", "C"}

    def _is_chef_or_confirme(self, context: GuessContext) -> bool:
        return to_english(context.value.lower().strip()) in {"chef", "confirme"}

    def _is_sector(self, context: GuessContext) -> bool:
        """
        A sector is a short title-cased phrase (all words capitalised).
        Guard against short job titles by requiring at least 2 words OR
        checking it's not already flagged as a job title.
        """
        s = context.value.strip()
        if len(s) < 3 or len(s) > 40:
            return False
        words = s.split()
        if not all(self._is_capitalized(w) for w in words):
            return False
        # single-word capitalized strings are ambiguous — require 2+ words for sector
        return len(words) >= 2

    def _is_capitalized(self, word: str) -> bool:
        return len(word) >= 2 and self.is_upper(word[0]) and not self.is_upper(word[1])

    def _is_salary(self, context: GuessContext) -> bool:
        v = context.value
        if isinstance(v, (int, float)):
            return True
        pattern = re.compile(r'^\s*\d{1,3}(?:[\s.,]\d{3})*(?:[.,]\d{2})?\s*€?\s*$')
        return bool(pattern.match(str(v)))

    def _greater_than_900(self, context: GuessContext) -> bool:
        n = self._extract_number(str(context.value))
        return n is not None and n > 900

    def _greater_than_400(self, context: GuessContext) -> bool:
        n = self._extract_number(str(context.value))
        return n is not None and n > 400

    def _lower_than_300(self, context: GuessContext) -> bool:
        n = self._extract_number(str(context.value))
        return n is not None and n < 300

    def _lower_than_1000(self, context: GuessContext) -> bool:
        n = self._extract_number(str(context.value))
        return n is not None and n < 1000

    def _from_admin_table(self, context: GuessContext) -> bool:
        return bool(context.table_number and context.table_number in {1, 2, 3} and context.nb_columns < 20)

    def _is_phrase(self, context: GuessContext) -> bool:
        return not self.is_upper(context.value) and len(context.value) > 30

    # ─────────────────────────────────────────
    # Key guesser
    # ─────────────────────────────────────────

    def guess_key(self, context: GuessContext) -> str | None:
        if context is None:
            return None
        for key, checks in self._content_guess_table.items():
            if all(check(context) for check in checks):
                return key
        return None

    # ─────────────────────────────────────────
    # Conformers
    # ─────────────────────────────────────────

    def conform(self, key: str, value):
        if not value:
            return value
        fn = self._conform_table.get(key)
        return fn(value) if fn else value

    def strip(self, value: str) -> str:
        return value.replace("\n", " ").strip()

    def _lower_capitalise(self, value: str) -> str:
        return self.strip(value).lower().capitalize()

    def _cadre_to_bool(self, value):
        if value == "NC":
            return False
        if value == "C":
            return True
        return value

    def _conform_category(self, value: str) -> str:
        if value == "Hors catégorie":
            return value
        return self.strip(value).upper().replace(" ", "")

    FEMININE_SUFFIXES = [
        "euse", "rice", "ière", "ienne", "ante", "ette", "elle", "onne"
    ]

    def _split_genders(self, value) -> dict:
        if not isinstance(value, str):
            return {"male": None, "female": None}

        cleaned = self.strip(value)

        # 1. explicit separator — easy case
        for sep in (" / ", "/"):
            if sep in cleaned:
                parts = [p.strip() for p in cleaned.split(sep, 1)]
                return {
                    "male":   self._lower_capitalise(parts[0]),
                    "female": self._lower_capitalise(parts[1]) if len(parts) > 1 else None,
                }

        # 2. no separator — try to find where female form starts
        words = cleaned.lower().split()
        split_index = self._find_female_split(words)

        if split_index:
            male   = " ".join(words[:split_index])
            female = " ".join(words[split_index:])
            return {
                "male":   self._lower_capitalise(male),
                "female": self._lower_capitalise(female),
            }

        # 3. no female form detected
        return {
            "male":   self._lower_capitalise(cleaned),
            "female": None,
        }

    def _find_female_split(self, words: list) -> Optional[int]:
        """
        Find the index where the female repetition starts.
        Strategy: look for a word that ends with a feminine suffix
        AND the next word looks like the start of a repeated title.
        """
        FEMININE_SUFFIXES = ("euse", "rice", "ière", "ienne", "ante", "ette", "elle", "onne")
        
        for i, word in enumerate(words):
            if any(word.endswith(s) for s in FEMININE_SUFFIXES):
                # check the next word starts a new title (capitalized or matches first word)
                next_index = i + 1
                if next_index < len(words):
                    # female part starts after this word
                    return next_index
        return None

    # ─────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────

    def is_upper(self, text: str) -> bool:
        letters = [c for c in text if c.isalpha()]
        return len(letters) > 0 and all(c == c.upper() for c in letters)

    def line_to_job_title(self, value: str):
        context = GuessContext(value=value)
        if self._is_job_title(context):
            return self._lower_capitalise(value)
        return None