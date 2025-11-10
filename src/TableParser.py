from ValueParser import ValueParser
import json

import pandas as pd
from typing import List, Any
import re

import hashlib


class Table:
    """A simple container for table data."""
    def __init__(self, title:str):
        self.title = title
        self.header = []
        self.entries = []

    def to_dataframe(self):
        return pd.DataFrame(self.rows, columns=self.header)

    def __repr__(self):
        return f"Table(header={self.header}, rows={len(self.rows)} rows)"

class TableParser():
    
    _parser = ValueParser()
    _tables = {}
    _current_headers = None
    _current_table = None
    _current_job_title = None
    _current_defintion = ""
    _headers_conversion_table = {
        "Événements":"events",
        "Durée du congé":"conge_duration",
        "Minima 1er janvier 2021":"brut_daily_salary",
        "Minima 1er janvier 2021":"Sbrut_daily_salary",
        "Minima 2021":"brut_daily_salary",
        "hebdo 35 h":"brut_weekly_salary_35h",
        "hebdo 39h":"brut_weekly_salary_39h",
        "mensuel sur base 35h":"brut_monthly_salary_35h",
        "Cadre / Non Cadre":"is_cadre",
        "Position":"position",
        "Catégorie":"category",
        "CATÉGORIE":"category",
        "Catégories":"category",
        "Fonction repère":"job_title",
        "FONCTION (EN ITALIQUE LA VERSION\nFÉMINISÉE)":"job_title",
        "Fonction (suivi de la version féminisée)":"job_title",
        "Postes (en Italique la version féminisée)":"job_title",
        "Responsabilité":"_",
        "Secteur":"sector",
        "Autonomie":"_",
        "Encadrement":"_",
        "Définition":"definition",
        "Déscription":"definition",
        "Fort":"_",
        "Moyen":"_",
        "Faible":"_",
    }
    _filiere_headers = {
        # FONCTION (EN ITALIQUE LA VERSION FÉMINISÉE) CATÉGORIE CADRE / NON CADRE Minima 1er janvier 2021
        "administrative et commerciale":["job_tile_male","job_title_female","is_cadre","monthly_salary"],
        # Secteur Postes (en Italique la version féminisée) Position Catégorie Cadre/Non Cadre Minima 2021
        "Tronc Commun":["sector","job_title","position","category","is_cadre","monthly_salary","definition"],
        "Volume":["sector","job_title","position","category","is_cadre","monthly_salary","definition"],
        "Animation 3D":["sector","job_title","position","category","is_cadre","monthly_salary","definition"],
        "Animation 2D":["sector","job_title","position","category","is_cadre","monthly_salary","definition"],
        "Motion Capture":["sector","job_title","position","category","is_cadre","monthly_salary","definition"],
        "Artistes de complément":["sector","job_title","position","category","is_cadre","monthly_salary","definition"],
    }

    def adpat_to_value(self,entry:dict,value)->str:
        for header,list in self._header_guess_table.items():
            if value not in list:
                continue
            entry[header] = value
        return None
            
    def is_upper(self,text):
        """
        Check if the input string is fully uppercase (letters, including accented, and spaces).

        Args:
            text (str): Input string.

        Returns:
            bool: True if all letters are uppercase, False otherwise.
        """
        # Remove non-letter characters for the check
        letters_only = ''.join(c for c in text if c.isalpha())
        return letters_only.isupper() and len(letters_only) > 0
        
    def guess_value_key(self,value)->str:
        for header,list in self._header_guess_table.items():
            if value not in list:
                continue
            return header
        if self.is_upper(value) and len(value)>5:
            return "job_title"        
        if len(value)>6:
            return "definition"
        return None
    
    
    def parse_table_title(self,_raw_page_text):
        known_titles = [
            "31.2. Construction de la grille de classification (voir tableau page suivante28)",
            "31.4. Les fonctions",
            "32.1. Barèmes salariaux des salariés sous contrat à durée indéterminée ou sous contrat à durée déterminée"
        ]
        
    
        
        

    def parse_raw_tables(self, _parent_article,_raw_tables: List[Any]) -> List[Table]:

        clean_tables = []
        article_title = _parent_article.title
        for table in _raw_tables:
            print("--------TABLE---------")

            # Skip empty tables
            if not table:
                continue
            
            # Flatten one level if needed
            if isinstance(table[0], list) and all(isinstance(r, list) for r in table[0]):
                table = table[0]

            # Skip empty again after flattening
            if len(table) == 0:
                continue
            
            
            clean_tables.append(table)
            
        return self.parse_complex_tables(article_title,clean_tables)   
        


        
    def _hash(self,_thing)->str:
        return str(int(hashlib.sha1(_thing.encode("utf-8")).hexdigest(), 16) % (10 ** 8))


        
    def parse_complex_tables(self,title,tables: List) -> pd.DataFrame:
        """
        Parse messy multi-row tables from pdfplumber into a clean DataFrame.
        Expected logical columns: Secteur, Fonction, Position, Catégorie, Définition.
        """



        job_table = {}
        current_key = None
        last_job_title = None
        last_category = None
        last_definition = None
        
        
        for table in tables:
            # Clean up
            cleaned = [[(cell or '').replace('\n', ' ').strip() for cell in row] for row in table]
            cleaned = [r for r in cleaned if any(c.strip() for c in r)]
            
            last_sector = None
            for row in cleaned: 
                tslice = self.parse_slice(row)
                job_title = tslice.get("job_title")
                position= tslice.get("position")
                sector= tslice.get("sector")
                category= tslice.get("category")
                daily_salary= tslice.get("daily_salary")
                monthly_salary= tslice.get("monthly_salary")
                is_cadre= tslice.get("is_cadre")

                # apply last values if None 
                tslice["sector"]= sector or last_sector
                tslice["category"] = category or last_category
                
                # remember if not None
                if sector and sector!="Secteur":
                    last_sector = sector
                if category:
                    last_category = category
                last_job_title = job_title or last_job_title
                
                if position and not job_title:
                    job_title = last_job_title

                definition = tslice.get("definition") 
 
                if job_title:
                    if definition:
                        # new entry 
                        job_key = self._hash(definition)
                        tslice["job_title"] = job_title or ""
                        job_table[job_key] = tslice
                        current_key = job_key
                        continue
                    if daily_salary or monthly_salary:
                        # new entry 
                        to_hash = daily_salary or monthly_salary
                        job_key = self._hash(to_hash)
                        tslice["job_title"] = job_title or ""
                        job_table[job_key] = tslice
                        current_key = job_key
                        continue
                if current_key and definition and not job_title:
                    if job_table[current_key].get("definition"):
                        job_table[current_key]["definition"]+=" "+definition
                if current_key and job_title:
                    job_table[current_key]["job_title"]+=" "+job_title

                    
                    
        for key,job in job_table.items():
            for key,value in job.items():
                job[key] = self._parser.conform(key,value)
                

        print(json.dumps(job_table,indent=4))
        return job_table
    
    
            
            
            
    def parse_slice(self,row:list)->dict:
        data = {}
        value_index=0
        for value in row:
            value_index+=1
            if not value or value=="":
                continue
            key = self._parser.guess_key(value,value_index)
            if key:
                data[key]=value
            else:
                data[str(value_index)] = value
        return data
        
    def merge_split_rows(self,raw_rows: List[List[str]]) -> List[List[str]]:
        """
        Merge pdfplumber-split rows into full logical entries.
        Heuristic: when a row has a non-empty category or description cell,
        it's considered the start of a new entry.
        """

        # Clean up
        cleaned = [[(cell or '').replace('\n', ' ').strip() for cell in row] for row in raw_rows]
        cleaned = [r for r in cleaned if any(c.strip() for c in r)]

        merged = []
        current = ["", "", "", "", "", "", "", "", ""]  # 9-column template

        for row in cleaned:
            # Ensure same number of cols
            while len(row) < len(current):
                row.append("")

            # Heuristic: detect start of new logical entry
            # if the row has a category (col 5 or 6) or a long description (col 6–8)
            has_category = any(re.match(r'^[IVX]+$', c.strip()) for c in row) or any("cat" in c.lower() for c in row if c)
            has_description = any(len(c) > 40 for c in row[5:])
            is_new_entry = has_category or has_description

            if is_new_entry:
                # save previous entry if it has content
                if any(current):
                    merged.append(current)
                current = row.copy()
            else:
                # append words to previous row (mostly column 2/3 area)
                for i in range(len(current)):
                    if row[i].strip():
                        current[i] = (current[i] + " " + row[i]).strip()

        # Add last one
        if any(current):
            merged.append(current)

        return merged
    
    def parse_row(self,row:list,current_filiere:dict=None):
        
        
        # new headers ? 
        if current_filiere and self._filiere_headers.get(current_filiere.get("bare")):
            headers = self._filiere_headers.get(current_filiere.get("bare"))
            self._current_headers = headers
        else:
            headers = self._parse_headers(row)
            if headers:
                self._current_headers = headers
                return
        if self._current_headers:
            table_key = "-".join(self._current_headers)
            if not self._tables.get(table_key):
                self._tables[table_key] = []
            self._current_table = self._tables[table_key]

        if not self._current_headers:
            return
        index=0
        entry = {}
        # create new entry
        for value in row:
            print(value)
            guessed_key = self._parser.guess_key(value)
            print(guessed_key)
            if guessed_key:
                entry[guessed_key] = self._parser.conform(guessed_key,value)
                index+=1
                continue
            key = str(index)
            entry[key] = self._parser.conform(key,value)
            index+=1
        
        if self._has_job_title(entry):
            self._current_job_title=entry.get("job_title")
            self._current_defintion = ""
        else:
            if not self._current_job_title:
                return
            entry["job_title"] = self._current_job_title
        
        if self._has_definition(entry):
            self._current_defintion+=entry.get("definition")
            entry["definition"] = self._current_defintion
            
        self._current_table.append(entry)
        ...
        
    def _has_job_title(self,entry):
        if not entry.get("job_title"):
            return False
        return True    
    
    def _has_definition(self,entry):
        if not entry.get("definition"):
            return False
        return True
        
    def get_tables(self)->dict:
        return self._tables
        
        
    def _parse_headers(self,_row:list)->bool:
        headers = []
        for value in _row :
            converted = self._headers_conversion_table.get(value)
            if not converted:
                continue
            if converted=="_":
                converted = value.lower()
            headers.append(converted)
        if len(headers)>1:
            return headers
        return None