
import json
import unicodedata
import re
from datetime import datetime
def serialize(text:str)->str:
    return to_english(clean_text(text)).lower().replace(" ","")

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

def parse_french_date(date_str):
        # Remove 'er', 'e', etc. from day
        day_str = re.match(r"(\d+)", date_str).group(1)
        
        # Replace French month names with numbers
        months = {
            "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
            "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
            "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12
        }
        
        # Extract month and year
        match = re.search(r"\d+\w* (\w+) (\d{4})", date_str)
        if not match:
            return None
        month_str, year_str = match.groups()
        month = months.get(month_str.lower())
        year = int(year_str)
        day = int(day_str)
        
        return datetime(year, month, day).date()