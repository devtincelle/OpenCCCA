
import re
from dataclasses import dataclass,field,asdict
from typing import Any, Iterator,List
from Utils import to_english,clean_text

class Article():
    def __init__(self,_start_line=None):
        self.name = None
        self.title = None
        self.start_line = _start_line
        self.number = None
        self.body:List[str] = []
        self.jobs:List[Job]= []
        self.sub_articles = []
        self.tables: List[Table] = []
        self.filieres:List[Filiere] = []
        self.coord = None
        self.pages = []

    def __str__(self)->str:
        return f"<ARTICLE : {self.number } {self.title} --- {self.body[:20]}....{len(self.body)} >"
    
    def __repr__(self)->str:
        return str(self)
    
    def add_sub_article(self,_sa):
        self.coord = self.coord or f"{self.number}"
        _sa.coord = f"{self.coord}-{_sa.number}"
        self.sub_articles.append(_sa.get_key())
    
    def get_key(self)->str:
        self.coord = self.coord or f"{self.number}"
        sanitized_title = to_english(self.title.lower()).split(" ")[0][:10]
        return f"{self.coord}_{sanitized_title}"
    
    
    def get_coord(self)->str:
        return f"{self.number}"
    
    def get_dict(self)->dict:
        
        return {
            "start_line":self.start_line,
            "title":self.name,
            "title":self.title,
            "coord":self.coord,
            "pages":self.pages,
            "number":self.number,
            "body":self.body,
            "sub_articles":self.sub_articles,
            "filieres":[ f"{f.name}({f.start_line})" for f in self.filieres],
            "tables":[ asdict(t) for t in self.tables],
            "jobs":[ asdict(j) for j in self.jobs]
            #"jobs":self.jobs
        }
    
    def print(self):
        ...


@dataclass
class Filiere():
    start_line:int=None
    name:str=None
    number:str=None
    start_line:int=None
    key:str=None
    article:str=None
    
@dataclass
class Category():
    start_line:int=None
    name:str=None
    number:str=None
    key:str=None
    article:str=None
    
@dataclass
class Sector():
    start_line:int=None
    name:str=None
    number:str=None
    key:str=None 
    article:str=None
       
@dataclass
class Job():
    key:str=None
    start_line:int=None
    job_title:dict=None
    article:dict=None
    page_number:dict=None
    table_number:dict=None
    category:str=None
    position:str=None
    filiere:str=None
    definition:str=None
    monthly_salary:float=None
    daily_salary:float=None
    weekly_salary:float=None
    is_cadre:bool=None
    
@dataclass
class Page():
    number:str=None
    key:str=None
    document:str=None
    filieres:list=field(default_factory=list)
    
    
       
@dataclass
class Table():
    article:str=None
    page_number:int=None
    table_number:int=None
    key:str=None
    document:str=None
    rows: list[list[Any]] = field(default_factory=list)
    
    def __iter__(self) -> Iterator[list[Any]]:
        """Allow iteration directly over table rows."""
        return iter(self.rows)
            
    def clean(self):
        def _deep_flatten(row):
            """Recursively flatten nested lists."""
            if not isinstance(row, list):
                return [row]
            result = []
            for r in row:
                result.extend(_deep_flatten(r))
            return result

        clean_rows = []
        for row in self.rows:
            if not row:
                continue
            
            # Deep flatten
            row = _deep_flatten(row)

            # Normalize and strip
            row = [(str(cell).replace("\n", " ").strip() if cell else "") for cell in row]

            # Keep only rows with at least one non-empty cell
            if any(cell.strip() for cell in row):
                clean_rows.append(row)

        # Return a new cleaned instance instead of mutating
        return Table(
            page_number=self.page_number,
            key=self.key,
            document=self.document,
            rows=clean_rows
        )
    
