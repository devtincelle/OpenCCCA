from model.Entities import Filiere

import hashlib
from utils.Utils import clean_text


class FiliereParser():
    
    def __init__(self,source_type:str="pdf"):
        self.source_type = source_type
    
    def _hash(self,_thing)->str:
        return str(int(hashlib.sha1(_thing.encode("utf-8")).hexdigest(), 16) % (10 ** 8))
            
    def parse_from_line(self,_line:str)->Filiere:

        if "Filière " not in _line:
            return 
        filieres = _line.split("Filière")
        print(filieres)
        for f in filieres[1:]:
            if ":" in f:
                return self._parse_with_semicolumn(f)
            return self._parse_with_spaces(f)

        
    def _parse_with_semicolumn(self,_line:str)->Filiere:
        # split filiere number and name
        parts = _line.split(":", 1)
        filiere_number = int(parts[0].strip())
        filiere_name = clean_text(parts[1].split("\n")[0].strip())
        filiere_key = clean_text(filiere_name).replace(" ","_")
        corrections = {
            "exploitation, maintenance et transfert de données":
            "exploitation, maintenance et transfert des données"
        }
        if filiere_name in corrections:
            filiere_name = corrections[filiere_name]
        filiere = Filiere(
            name=f"{filiere_number} {filiere_name}",
            number=filiere_number,
            slug=f"{filiere_number}-{filiere_key[0]}"
        )
        return filiere    
    
    def _parse_with_spaces(self,_line:str)->Filiere:
        # split filiere number and name
        parts = _line.split(" ", 1)
        filiere_number, filiere_name = self._split_number_and_name(_line)
        filiere_key = clean_text(filiere_name).replace(" ","_").lower()
        corrections = {
            "exploitation, maintenance et transfert de données":
            "exploitation, maintenance et transfert des données"
        }
        if filiere_name in corrections:
            filiere_name = corrections[filiere_name]
        filiere = Filiere(
            name=f"{filiere_number} {filiere_name}".lower(),
            number=filiere_number,
            slug=f"{filiere_number}-{filiere_key[0]}".lower()
        )
        return filiere
    
    def _split_number_and_name(self,text: str):
        parts = text.strip().split(" ", 1)
        return int(parts[0]), parts[1]