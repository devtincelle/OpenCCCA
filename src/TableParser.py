from ValueParser import ValueParser
from Entities import Filiere,Table,Job
from GuessContext import GuessContext
import json
from dataclasses import fields

import pandas as pd
from typing import List, Any
import re

import hashlib
from Utils import to_english



class TableParser():
    
    _parser = ValueParser()
    
    def _hash(self,_thing)->str:
        return str(int(hashlib.sha1(_thing.encode("utf-8")).hexdigest(), 16) % (10 ** 8))

    def is_admin_table(self,table_number:int)->bool:
        return table_number in [1,2,3]
        

    def parse_jobs(self, table:Table)->List[Job]:

        """
        Parse messy multi-row tables from pdfplumber into a clean DataFrame.
        Expected logical columns: Secteur, Fonction, Position, Catégorie, Définition.
        """

        job_table = {}
        current_key = None
        last_job_title = None
        last_category = None
        table_number = table.table_number
        last_sector = None
        row_number = -1
        
        for row in table:
            print(row)
            row_number+=1
            
            tslice = self.parse_slice(row,row_number,table_number)
            
            
            if not tslice:
                continue
            tslice["row_number"] = row_number
            tslice["table_number"] = table_number
            tslice["table_nb_columns"] = len(row)
            
            job_title = tslice.get("job_title")
            position= tslice.get("position")
            sector= tslice.get("sector")
            category= tslice.get("category")
            daily_salary= tslice.get("daily_salary")
            monthly_salary= tslice.get("monthly_salary")

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
            
            if not category:
                category = last_category
        
            if job_title:                  
                if self.is_admin_table(table_number):
                    # new entry 
                    print(job_title)
                    job_key = self._hash(job_title)
                    tslice["job_title"] = job_title 
                    job_table[job_key] = tslice
                    current_key = job_key
                    continue
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
                job_table[current_key]["category"]=category

                    
        jobs = []
                    
        for job_key, job_data in job_table.items():
            # Normalize values using your parser
            for key, value in job_data.items():
                job_data[key] = self._parser.conform(key, value)

            # Add contextual info
            job_data["article"] = table.article
            job_data["page_number"] = table.page_number

            # Only keep keys that exist in Job dataclass
            job_field_names = {f.name for f in fields(Job)}
            valid_data = {k: v for k, v in job_data.items() if k in job_field_names}

            # Instantiate safely
            job = Job(**valid_data)
            jobs.append(job)

                
        return jobs
    
    def _find_filiere(self,job,filieres:List[Filiere])->Filiere:
        # wip
        return filieres[0]
    
    def is_header(self,_name)->bool:
        return _name in [
            'FONCTION (EN ITALIQUE LA VERSION FÉMINISÉE)',
            'Définition',
            'Catégorie',
            "Secteur",
            "Postes (en Italique la version féminisée)",
            "Position",
            "Cadre / Non Cadre",
            "Minima 2021",
            "hebdo 35h",
            "hebdo 39h",
            "mensuel sur base 35h"
        ]
    

    def parse_slice(self,row:list,row_number:int=None,table_number:int=None)->dict:
        data = {}
        column_index=-1
        for value in row:
            if self.is_header(value):
                return None
            column_index+=1
            if not value or value=="":
                continue
            context = GuessContext(
                value=value,
                column_index=column_index,
                table_number=table_number,
                row_number=row_number,
                nb_columns=len(row)
            )
            key = self._parser.guess_key(context)
            if key:
                if data.get(key) and isinstance(data.get(key),str):
                    ...
                    #data[key]+=" "+value
                else:
                    data[key]=value
            else:
                data[str(column_index)] = value
        return data
        