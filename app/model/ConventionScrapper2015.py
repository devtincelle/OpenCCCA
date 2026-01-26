


import pdfplumber
import json
import uuid
import os
import unicodedata
import re
from datetime import datetime
from model.JobParser import TableParser
from model.ConventionScrapperAbstract import ConventionScrapperAbstract
class ConventionScrapper2015(ConventionScrapperAbstract):
    
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
    
    def parse_current_filieres(self,_raw_string)->list:
        if "Filière " not in _raw_string:
            return []
        filieres = _raw_string.split("Filière")
        data = []

        for f in filieres[1:]:
            # split filiere number and name
            parts = f.split(":", 1)
            filiere_number = int(parts[0].strip())
            filiere_name = self.clean_text(parts[1].split("\n")[0].strip())
            filiere_key = self.clean_text(filiere_name).replace(" ","_")
            corrections = {
                "exploitation, maintenance et transfert de données":
                "exploitation, maintenance et transfert des données"
            }
            if filiere_name in corrections:
                filiere_name = corrections[filiere_name]
            filiere = {
                "name":f"{filiere_number} {filiere_name}",
                "number":filiere_number,
                "key":f"{filiere_number}-{filiere_key[0]}"
            }
            data.append(filiere) 
        return data

    def find_filiere(self,_entries:dict,_filiere_list:list)->str:
        for key,value in _entries.items():
            if key not in ["fonction","definition"]:
                continue
            for f in _filiere_list:
                for word in f["name"].split(" "):
                    if word in value:
                        return f["name"]
        return None
    
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

    def parse(self, file: str = None) -> dict:
        if not file:
            print("Error pdf is None")
            return {}
        if not os.path.exists(file):
            print("Error pdf does not exist:", file)
            return {}
        
        filieres = []
        categories = []
        filieres_fonction_table= {}
        data_table = {}
        document_version_string = None
        
        
        with pdfplumber.open(file) as pdf:
            last_headers = None
            current_filiere = None
            page_number = 0
            
            for page in pdf.pages:
                
                if page_number==0:
                    document_version_string = self.parse_document_version(page.extract_text())
                    print(document_version_string)
                
                page_number+=1
                pages_filieres = self.parse_current_filieres(page.extract_text())
                for f in pages_filieres:
                    if f not in filieres:
                        filieres.append(f)
                
                if len(pages_filieres)>0:
                    current_filiere = pages_filieres[0]['name']

                for f in pages_filieres:
                    if f not in filieres:
                        filieres.append(f)
                        
                tables = page.extract_table()
                if tables is None:
                    continue

                table = self.parse_table(tables, last_headers)
                
                # Clean headers
                if len(table["headers"]) > 0:
                    last_headers = [self.clean_text(h) for h in table["headers"]]
                    headers_key = "_".join(last_headers)

                if headers_key not in data_table.keys():
                    data_table[headers_key] = []

                # Clean each entry
                for entry in table["entries"]:
                    
                    cleaned_entry = {k: self.clean_text(v) if isinstance(v, str) else v for k, v in entry.items()}
                    if len(pages_filieres)>1:
                        found = self.find_filiere(cleaned_entry,pages_filieres)
                        if found:
                            current_filiere = found
                    if "fonction" in cleaned_entry.keys() :
                        if cleaned_entry["fonction"] not in filieres_fonction_table.keys():
                            filieres_fonction_table[cleaned_entry["fonction"]] = current_filiere
                        else:
                            current_filiere = filieres_fonction_table[cleaned_entry["fonction"]] 
                    cleaned_entry["filiere"] = current_filiere
                    cleaned_entry["page_number"] = str(page_number)
                    cleaned_entry["document_version"] = document_version_string or "inconnue"
                    if "category" in cleaned_entry.keys() :
                        cat = cleaned_entry["category"] 
                        defi = cleaned_entry.get("definition")
                        catched_cat = None
                        if "Hors" in cat or self.is_category(cat):
                            catched_cat = cat
                        elif defi and self.is_category(defi):
                            catched_cat = defi
                            cleaned_entry["category"]  = defi
                        if catched_cat and catched_cat not in categories:
                            categories.append(catched_cat)
                            
                    data_table[headers_key].append(cleaned_entry)
                    

        f_table = self.parse_function_table(data_table)
        clean_table = self.conform_function_table(f_table)
        
        final_data = {}
        final_data["jobs"] = clean_table
        final_data["filieres"] = [ f["name"] for f in filieres ]
        final_data["categories"] = categories
    
        return final_data

    def is_category(self,text):
        category_regex = re.compile(r"^(I{1,3}|IV|V|VI{0,3}|IX|X)(?: [A-Z])?$")
        return bool(category_regex.match(text))

    def check_key(self,_key:str)->bool:
            if _key == "":
                return False
            if _key in ConventionScrapper2015._bad_keys:
                return False
            for bkw in ConventionScrapper2015._bad_key_words:
                if bkw in _key:
                    return False
            return True

    def conform_function_table(self,_table:dict)->dict:
        clean_talbe = {}
        for key,value in _table.items():
            if self.check_key(key) == False:
                continue
            value["id"] = str(uuid.uuid4())[-8:]
            clean_talbe[key] = value
        return clean_talbe

    def is_header(self,_list:list):
        none_values_count = 0
        known_header_keywords = ["Fonction","FONCTION","Catégorie","CATÉGORIE","Définition","Evénements","Durée"]
        has_kw = False
        clean_keys = [value for value in _list if value is not None and value != ""]
        for key in clean_keys:
            for kw in known_header_keywords:
                if kw not in key and kw.upper() not in key:
                    continue
                return True
        return False



    def filter_key(self,_key):
        if 'AU 1ER MARS' in _key:
            return 'salaire_brut'
        if 'FONCTION' in _key or "Fonction" in _key:
            return "fonction"    
        if 'Catégorie' in _key or  "CATÉGORIE" in _key:
            return "category"   
        if 'Définition' in _key :
            return "definition"
        return _key

    def filter_headers(self,_list)->list:
        filtered = []
        for el in _list:
            if el is None:
                continue
            if el in filtered:
                continue
            if el == "":
                continue
            fem_split = el.split("(")
            if  len(fem_split)>1 :
                filtered.append( self.filter_key(fem_split[0]))
                filtered.append("version_feminisee")
                continue
            key = self.filter_key(el)
            filtered.append(key)
        return filtered

    def parse_entry(self,_headers,_row): 
        entry = {}
        row = _row
        if len(_headers)!=len(_row):
            row = [value for value in row if value is not None]
        values = []
        for value in row:
            if value is None:
                values.append("")
                continue
            values.append(value)
        index = 0
        last_key = None
        for key in _headers:
            if index > len(values)-1:
                break
            if last_key == "version féminisée" and key =="Catégorie" and value is not None and len(value)>4:
                key = 'Définition de fonction'
            if last_key == "FONCTION" and key =="Catégorie" and value is not None and "€" in value :
                key = 'salaire brut'
            entry[key] = values[index]
            index+=1
            last_key = key
        if len(entry.keys())==0:
            return None
        return entry

    def validate_entry(self,_entry):
        count = 0
        for key,value in _entry.items():
            if value=="":
                count+=1
        return count < 3


    def parse_table(self,_table,_last_header=None)->dict:
        headers = _last_header or []
        entries = []
        if not _table:
            return{}
        for row in _table:
            if self.is_header(row):
                headers = self.filter_headers(row)
                continue
            entry = self.parse_entry(headers,row)
            if entry is None:
                continue        
            if self.validate_entry(entry)==False:
                continue
            
            entries.append(entry)    
        return {
            "headers":headers,
            "entries":entries
        }

    # Open the PDF file
    

    def remove_special_chars(self,text: str) -> str:
        if type(text) != str:
            return text
        # Keep letters (including accents), spaces, and apostrophes
        # [\p{L}] is not natively supported in Python, so use \w with re.UNICODE
        # But \w includes digits and underscore, so we explicitly use a negated pattern to remove unwanted chars
        cleaned = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ0-9\-_'\/ ]+", "", text)
        return cleaned


    
    def strip_name(self,_name:str)->str:
        replace_table= {
            "é":"e",
            "è":"e",
            "à":"a",
            "'":"_",
            "\'":"_",
            "ô":"o",
            "ç":"c",
            "\n":"_",
            "/":"_",
            " ":"_",
        }
        clean = ""
        for char in _name:
            if not replace_table.get(char):
                clean+=char
                continue
            clean+=replace_table.get(char)
        return clean
    
    
    def filter_value(self,value:str)->bool:
        if value == "":
            return False
        if not value :
            return False        
        if value == "feminisée" :
            return False
        return True
    
    def filter_fonction_key(self,_name:str)->bool:
        if "OUS_FORME_DE_JOURS_DE_REPOS_SUR" in _name:
            return False
        if "LA_REDUCTION_DU_TEMPS_DE_TRAVAIL" in _name:
            return False        
        if "alaries_non_cadres_et_cadres_inte" in _name:
            return False        
        if "(*)_On_ne_peut_employer_de_salarie_" in _name:
            return False        
        if "On_ne_peut_employer_de" in _name:
            return False        
        if "féminisée"==_name:
            return False
        return True

    def conform_data(self,_data:dict):
        definition = _data.get("defintion")
        categorie = _data.get("category")
        if definition and categorie:
            if len(categorie) < 5:
                self._last_category = categorie
            return _data
        if categorie and not definition:
            if len(categorie) > 5:
                _data["definition"] = categorie
                _data["category"] = self._last_category or ""
        return _data

    def parse_function_table(self,_data_table):
        table = {}
        index = 0
        for key,datas in _data_table.items():
            for data in datas:
                if "fonction" not in data.keys():
                    continue                
                function_nice_name = data["fonction"].replace("\n"," ")
                function_base_name = self.strip_name(data["fonction"])
                if self.filter_fonction_key(function_base_name)==False:
                    continue                
                # concatenate category and job as unqiue key to avoid missing jobs with the same names but different categories 
                function_key = "-".join([self.strip_name(data.get("filiere","")),self.strip_name(data["fonction"])])
                if self.filter_fonction_key(function_key)==False:
                    continue  
                data["nom"] = function_nice_name
                data["parsing_id"] = str(index)
                if function_key not in table.keys():
                    table[function_key] = {}
                for key,value in data.items():
                    if self.filter_value(value)==False:
                        continue
                    if "€" in value and len(value)>4:
                        key = "salaire_brut_mensuel"
                        value = self.parse_salary(value)
                    if key == "salaire_brut":
                        key = "salaire_brut_journalier"
                        value = self.parse_salary(value)
                    clean_key = self.strip_name(key)
                    table[function_key][clean_key] = self.remove_special_chars(value)
                self.conform_data(table[function_key])
                index+=1
                
        optimised_table = self.merge_starred_entries(table)
                
        return optimised_table

    def parse_salary(self,_string):
        clean = _string.replace(",",".").replace("€","").replace(" ","")
        return float(clean)


    def merge_starred_entries(self,data: dict) -> dict:
        """
        Merge entries in a dictionary whose keys differ only by a trailing '*'.
        Keeps all unique fields and merges overlapping ones intelligently.
        """
        merged_data = {}
        processed = set()

        for key in list(data.keys()):
            base_key = key.rstrip("*")
            if base_key in processed:
                continue

            # find the potential pair (with or without *)
            alt_key = base_key + "*" if not key.endswith("*") else base_key
            entry1 = data[key]
            entry2 = data.get(alt_key)

            if alt_key in data and alt_key != key:
                # merge both entries
                merged_entry = {**entry2, **entry1}  # right side overwrites on duplicates
                
                merged_data[base_key] = merged_entry
                processed.add(base_key)
            else:
                merged_data[key] = entry1
                processed.add(base_key)
                
        clean_table = {}
        for key,value in merged_data.items():
            clean_key = key.replace("*","")
            clean_table[clean_key] = value

        return clean_table