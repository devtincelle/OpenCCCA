


import pdfplumber
import json
import uuid
import os
import unicodedata
import re
from datetime import datetime
from Entities import Page
from TableParser import TableParser
from ArticleParser import ArticleParser
import re
from typing import List

class ConventionScrapper2021():
    
    _bad_keys = [
        "6- Salari\u00e9s non cadres et cadres int\u00e9gr\u00e9s",
        "4- LA REDUCTION DU TEMPS DE TRAVAIL",
        "SOUS FORME DE JOURS DE REPOS SUR L\u2019ANNEE"
    ]    
    _bad_key_words = [
        "On ne peut employer"
    ]
    
    _last_category = None

    def __init__(self):
        ...

    def clean_text(self,text: str) -> str:
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
    

    def parse_french_date(self,date_str):
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
    
    def parse_convention_first_page(self,text:str)->dict:
        data = {}

        # Extract title (everything before the first date)
        title_match = re.match(r"^(.*?)(?:du|de) (\d{1,2} \w+ \d{4})", text)
        if title_match:
            data["title"] = title_match.group(1).strip()
            data["date_of_signature"] = title_match.group(2).strip()

        # Extract date of extension
        extended_match = re.search(r"Etendue par arrêté le (\d{1,2} \w+ \d{4})", text)
        if extended_match:
            data["extended_by_order"] = self.parse_french_date(extended_match.group(1).strip())

        # Extract IDCC
        idcc_match = re.search(r"IDCC\s*:\s*(\d+)", text)
        if idcc_match:
            data["IDCC"] = int(idcc_match.group(1))

        # Extract brochure number
        brochure_match = re.search(r"Brochure n°\s*(\d+)", text)
        if brochure_match:
            data["brochure_number"] = int(brochure_match.group(1))

        # Extract consolidated version date (fix for ordinals like '1er')
        version_match = re.search(r"Version consolidée au (\d+\w* \w+ \d{4})", text)
        if version_match:
            data["version_consolidated"] = self.parse_french_date(version_match.group(1).strip())

        # Extract note
        note_match = re.search(r"En italique\s*:\s*(.*)", text)
        if note_match:
            data["note"] = note_match.group(1).strip()

        return data
    
    def parse_document_version(self,_text:str)->str:
        '''
            Convention collective
            de la production de films d’animation
            du 6 juillet 2004
            Etendue par arrêté le 18 juillet 2005
            IDCC : 2412
            Brochure n° 3314
            Version consolidée au 1er mars 2015
            En italique : nouvelle codification du Code du Travail
            1
            
           {'extended_by_order': datetime.date(2005, 7, 18), 'IDCC': 2412, 'brochure_number': 3314, 'version_consolidated': datetime.date(2015, 3, 1), 'note': 'nouvelle codification du Code du Travail'}
        '''
        
        data = self.parse_convention_first_page(_text)
        print(data)
        
        version = f"IDCC-{data['IDCC']}_B-{data['brochure_number']}_{data['version_consolidated']}"
        return version


    def parse(self, _pdf: str = None, _output_json_path: str = None) -> dict:
        if not _pdf:
            print("Error pdf is None")
            return {}
        if not os.path.exists(_pdf):
            print("Error pdf does not exist:", _pdf)
            return {}
        
        article_parser = ArticleParser()
        
        with pdfplumber.open(_pdf) as pdf:

            page_number = 0
            
            
            for page in pdf.pages:
                if page_number == 0:
                    version = self.parse_document_version(page.extract_text())
                    article_parser.set_doc_version(version)
                page_number+=1
                article_parser.parse_page(page,page_number)
                
                
                
        article_parser.parse_filieres()
        article_parser.parse_sub_articles()
        article_parser.parse_tables()
        article_parser.parse_jobs()
            
        final_data =  article_parser.get_dict()
            
        # Save JSON with UTF-8 encoding
        if _output_json_path:
            with open(_output_json_path, "w", encoding="utf-8") as file:
                json.dump(final_data, file, ensure_ascii=False, indent=2)

        return final_data
  
