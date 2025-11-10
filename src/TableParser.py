from ValueParser import ValueParser
from Entities import Filiere
import json

import pandas as pd
from typing import List, Any
import re

import hashlib
from Utils import to_english

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


    def parse_raw_tables(self, _article_key,_raw_tables: List[list],article_filieres:List[Filiere]) -> List[Table]:

        clean_tables = []
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
            
        return self.parse_complex_tables(_article_key,clean_tables,article_filieres)   
        


        
    def _hash(self,_thing)->str:
        return str(int(hashlib.sha1(_thing.encode("utf-8")).hexdigest(), 16) % (10 ** 8))


        
    def parse_complex_tables(self,_article_key,tables:list,filieres:List[Filiere]) -> pd.DataFrame:
        """
        Parse messy multi-row tables from pdfplumber into a clean DataFrame.
        Expected logical columns: Secteur, Fonction, Position, Catégorie, Définition.
        """



        job_table = {}
        current_key = None
        last_job_title = None
        last_category = None
        last_definition = None
        table_number = -1
        
        for table in tables:
            table_number+=1
            # Clean up
            cleaned = [[(cell or '').replace('\n', ' ').strip() for cell in row] for row in table]
            cleaned = [r for r in cleaned if any(c.strip() for c in r)]
            
            row_number = -1
            last_sector = None
            for row in cleaned: 
                row_number+=1
                
                tslice = self.parse_slice(row)
                tslice["row_number"] = row_number
                tslice["table_number"] = table_number
                
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
            job["article"] = _article_key
            if len(filieres) > 0:
                job["filiere"] = self._find_filiere(job,filieres).name 
                

        print(json.dumps(job_table,indent=4))
        return job_table
    
    def _find_filiere(self,job,filieres:List[Filiere])->Filiere:
        # wip
        return filieres[0]
    

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
        