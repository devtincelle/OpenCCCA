
import json
import unicodedata
import re


def to_english(text: str) -> str:
        # 1. Normalize the text to decompose accents (é -> e + ́)
        text = unicodedata.normalize('NFD', text)
        # 2. Remove accent characters
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        # 3. Remove all non-alphanumeric characters (keep letters, numbers, spaces)
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # 4. Optionally collapse multiple spaces and trim
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    
def clean_text(text: str) -> str:
    """Remove unwanted characters but keep letters (with accents), numbers in words, spaces, apostrophes, commas, euro symbol."""
    if not text:
        return ""

    # Normalize to NFC to keep accents combined
    text = unicodedata.normalize('NFC', text)

    # Remove control characters (\n, \r, \t, \x0b, \x0c)
    text = re.sub(r"[\n\r\t\x0b\x0c]+", " ", text)

    # Remove unwanted characters but keep letters, numbers (even in words), spaces, apostrophes, comma, euro
    text = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ0-9' ,€]+", "", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()