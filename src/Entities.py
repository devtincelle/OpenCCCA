
import re
from dataclasses import dataclass,field,fields,asdict
from typing import Any, Iterator,List,Optional
from Utils import to_english,clean_text,serialize



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
        self.source:str=None
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
    
        ...



@dataclass
class Filiere:
    start_line: Optional[int] = None
    name: Optional[str] = None
    number: Optional[str] = None
    text: Optional[str] = None
    slug: Optional[str] = None
    article: Optional[str] = None
    source:str=None
    
    @property
    def id(self):
        return serialize(self.name)

    # ----------  equality  ----------
    def __eq__(self, other) -> bool:
        if not isinstance(other, Filiere):
            return NotImplemented
        # both sides must have a non-empty name to be considered equal
        return bool(self.name and other.name and serialize(self.slug) == serialize(other.slug))

    # ----------  merge  ----------
    def merge_with(self, other: "Filiere") -> "Filiere":
        """Return a new Filiere whose fields are the first non-None value
        between *self* and *other*.  Lists (jobs) are concatenated and deduplicated."""
        if not isinstance(other, Filiere):
            raise TypeError("Can only merge with another Filiere instance")

        def _pick(a, b):
            return a if a is not None else b
        
        return Filiere(
            start_line=_pick(self.start_line,other.start_line),
            name=_pick(self.name,other.name),
            slug=_pick(self.slug,other.slug),
            text="".join([self.text,other.text]),
            article=_pick(self.article,other.article)
        )

      

    # ----------  helper  ----------
    def has_job(self, _job_title: str) -> bool:
        if not self.text:
            return False
        job = to_english(_job_title.lower().replace(" ", ""))
        return job in self.text.lower().replace(" ", "")
    
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
class Job:
    key: Optional[str] = None
    start_line: Optional[int] = None
    job_title: Optional[dict] = None
    article: Optional[dict] = None
    page_number: Optional[dict] = None
    table_number: Optional[dict] = None
    category: Optional[str] = None
    position: Optional[str] = None
    sector: Optional[str] = None
    filiere: Optional[str] = None
    definition: Optional[str] = None
    monthly_salary: Optional[float] = None
    daily_salary: Optional[float] = None
    weekly_salary: Optional[float] = None
    is_cadre: Optional[bool] = None
    source:str=None
    @property
    def id(self):
        return self.get_slug()
        
    def get_slug(self)->str:
        name = self.job_title.get("male") or self.job_title.get("female")
        if name:
            return serialize(name)
    # ----------  equality  ----------
    def __eq__(self, other)->bool:
        if not isinstance(other, Job):
            return NotImplemented
        # no title dict on either side → can’t match
        if not self.job_title or not other.job_title:
            return False
        # one common name (male or female) is enough
        
        compare = (self.id == other.id)
        return compare
        return (self.job_title.get("male") == other.job_title.get("male")
                and self.job_title.get("male") is not None) or \
               (self.job_title.get("female") == other.job_title.get("female")
                and self.job_title.get("female") is not None)

    # ----------  merge  ----------
    def merge_with(self, other: "Job") -> "Job":
        """
        Return a new Job whose fields are the first non-None value
        between *self* and *other*.  If both are None the field stays None.
        """
        if not isinstance(other, Job):
            raise TypeError("Can only merge with another Job instance")

        def _pick(a, b):
            return a if a is not None else b

        kwargs = {f.name: _pick(getattr(self, f.name), getattr(other, f.name))
                  for f in fields(self)}
        return Job(**kwargs)
    
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
    
