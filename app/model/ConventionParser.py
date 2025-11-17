
import re
from model.TableParser import TableParser
from model.ValueParser import ValueParser
from model.Entities import Article,Filiere,Table,Job,Category,Convention,Sector
from utils.Utils import to_english,clean_text,parse_french_date
from typing import List,Dict
from dataclasses import asdict
import pdfplumber
import os
import uuid

class ConventionParser():
    
    _article_table:dict = {}
    _articles:List[Article] = []
    _jobs:List[Job] = []
    _filieres:List[Filiere] = []
    _categories: List[Category] = []
    _sectors: List[Sector] = []
    _last_article_key = None
    _document_lines = []
    _line = -1
    _table_parser=TableParser()
    _value_parser=ValueParser()
    _document_version:str =None
    _document_version_data:dict=None
    _document_name:str=None
    _parsing_id:int = None
    
    def __init__(self):
        self._parsing_id = str(uuid.uuid4())[-8:]
        

    def parse(self, _pdf: str = None) -> Convention:
        if not _pdf:
            print("Error pdf is None")
            return {}
        if not os.path.exists(_pdf):
            print("Error pdf does not exist:", _pdf)
            return {}
        self._document_name = os.path.basename(_pdf)
        
        with pdfplumber.open(_pdf) as pdf:

            page_number = 0
            
            
            for page in pdf.pages:
                if page_number == 0:
                    self.parse_document_version(page.extract_text())
                page_number+=1
                self.parse_page(page,page_number)
                
        self.parse_filieres()
        self.parse_sub_articles()
        self.parse_tables()
        self.parse_jobs()
        self._build_article_list()
        
        convention = Convention(
            id=self._parsing_id,
            articles=self._articles,
            jobs=self._jobs,
            categories=self._categories,
            sectors=self._sectors,
            filieres=self._filieres,   
            name=self._document_name,
            version_name=self._document_version,
            version_data= self._document_version_data
        )
        
        return convention
    
    def _build_article_list(self):
        self._articles = []
        for key,article in self._article_table.items():
            if not article:
                continue
            print(article)
            self._articles.append(article)
    
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
            data["extended_by_order"] = parse_french_date(extended_match.group(1).strip())

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
            data["version_consolidated"] = str(parse_french_date(version_match.group(1).strip()))

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
        self._document_version_data = data
        
        version = f"IDCC-{data['IDCC']}_B-{data['brochure_number']}_{data['version_consolidated']}"
        self._document_version = version
        
        return version

    def set_doc_version(self,_data:str):
        self._document_version = _data

    def extract_articles(self,texte: str,_start_line=None):
        """
        Extrait les articles de type :
        'Article 8 – Institutions représentatives du personnel'
        en ignorant ceux dont le titre finit par une suite de points.
        
        Retourne une liste de tuples : [(numero, titre), ...]
        """
        pattern = re.compile(
            r'^(?:Article|Art\.?)\s*(\d+)\s*[-–—]\s*(.+?)$',
            re.IGNORECASE | re.UNICODE | re.MULTILINE
        )

        articles = []
        for numero, titre in pattern.findall(texte):
            titre = titre.strip()
            # Ignore titles that end with filler dots or dot patterns
            if re.search(r'\.{3,}\s*$', titre):
                continue
            article = Article(_start_line)
            article.title = titre.replace(".","")
            article.number = numero
            articles.append(article)
        
        return articles
    
    def extract_sub_articles(self,texte: str,line_number):
        """
        Extrait les sous-articles de type :
        '8.1. Délégués du personnel'
        '9.2.3 Observatoire paritaire ...'
        
        Retourne une liste de tuples : [(numero, titre), ...]
        """
        pattern = re.compile(r'^\s*(\d+(?:\.\d+)+)\.\s*(.+)$', re.MULTILINE)
        sous_articles = []
        for numero, titre in pattern.findall(texte):
            titre = titre.strip()
            # Ignore titles that end with filler dots or dot patterns
            if re.search(r'\.{3,}\s*$', titre):
                continue
            article = Article(line_number)
            article.title = titre.replace(".","")
            article.number = numero
            sous_articles.append(article)
        
        return sous_articles
    
    
    def parse_page(self,page,_page_number):
        raw_text = page.extract_text()
        raw_tables = page.extract_tables()
        lines = raw_text.split('\n')
        current_key = self._last_article_key
        
        for line in lines:
            self._line+=1
            self._document_lines.append(line)
            articles = self.extract_articles(line,self._line)
            if len(articles)>0:
                # new article detected 
                current_key = articles[0].get_key()
                self._article_table[current_key] = articles[0]
                self._article_table[current_key].pages.append( _page_number)
                self._last_article_key = current_key
                continue
            # add line to current article
            if self._article_table.get(current_key):
                self._article_table[current_key].body.append(line)
                
        # find a way to get the table number rigth again 
        
        table_number = -1
        if self._article_table.get(current_key):
            for t in raw_tables:
                table_number+=1
                table = Table(
                    article=current_key,
                    page_number=_page_number,
                    rows=t
                ).clean()
                self._article_table[current_key].tables.append(table)
                    
    def parse_sub_articles(self):
        new_articles = []
        for key,article in self._article_table.items():
            line_number = article.start_line
            current_subarticle = None
            raw_body = article.body
            article.body = []
            for line in raw_body:
                line_number+=1
                sub_articles = self.extract_sub_articles(line,line_number)
                if len(sub_articles)>0:
                    if current_subarticle:
                        article.add_sub_article(current_subarticle)
                        new_articles.append(current_subarticle)
                    current_subarticle = sub_articles[0]
                    current_subarticle.pages = article.pages
                    continue
                if current_subarticle:
                    current_subarticle.body.append(line)
                else:
                    article.body.append(line)
        for sa in new_articles:
            self._article_table[sa.get_key()] = sa
                    
    def parse_filieres(self)->List[Filiere]:
        last_filiere:Filiere = None
        last_job_title:str = None
        for article in self._article_table.values():
            line_number = article.start_line-1
            for line in article.body:
                line_number+=1
                filiere = self.parse_filiere_from_line(line)
                if filiere:
                    filiere.article = article.get_key()
                    filiere.start_line = line_number
                    filiere.source = self._document_version
                    last_filiere = filiere
                    article.filieres.append(filiere)
                    continue
                if last_filiere:
                    if not last_filiere.text :
                        last_filiere.text = ""
                    last_filiere.text+=to_english(clean_text(line.lower()).replace(" ",""))
                    
        merged:Dict[str,Filiere] = {}
        for article in self._article_table.values():
            for f in article.filieres:
                # find an existing representative that is equal to this job
                rep = next((k for k in merged if k == f), None)
                if rep is None:              # first time we see this title
                    merged[f.id] = f
                else:                        # merge into the representative
                    merged[rep.id] = rep.merge_with(f)

        unique_list = list(merged.values())
        self._filieres = unique_list
        return unique_list
                
    
            
        
    def parse_tables(self):
        table_counter = -1
        for key,article in self._article_table.items():
            if len(article.tables)==0:
                continue
            for table in article.tables:
                table_counter +=1
                table.table_number = table_counter
                table.article = article.get_key()
                jobs = self._table_parser.parse_jobs(table)
                # connect job to filiere according to job title string 
                for job in jobs:
                    job.source = self._document_version
                    for f in self._filieres:
                        if f.has_job(job.job_title["male"]) or f.has_job(job.job_title["female"]):
                            job.filiere = f.name
                            break
                article.jobs.extend(jobs)    
                
    def parse_jobs(self) -> List[Job]:
        """
        Return a single list of unique Jobs (uniqueness decided by __eq__).
        Duplicate titles are merged into one Job record via Job.merge_with().
        """
        merged: Dict[str, Job] = {}          # key == representative Job, value == fully-merged Job

        for article in self._article_table.values():
            for job in article.jobs:
                # find an existing representative that is equal to this job
                rep = next((k for k in merged if k == job), None)
                if rep is None:              # first time we see this title
                    merged[job.id] = job
                else:                        # merge into the representative
                    merged[rep.id] = rep.merge_with(job)

        unique_list = list(merged.values())
        self._jobs = unique_list
        return unique_list
            
    def parse_filiere_from_line(self,_line:str)->Filiere:

        if "Filière " not in _line:
            return 
        filieres = _line.split("Filière")
        for f in filieres[1:]:
            # split filiere number and name
            parts = f.split(":", 1)
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
        

    

                    
    def get_dict(self)->dict:
        table = {
            "articles":[],
            "filieres":[],
            "categories":[],
            "sectors":[],
            "jobs":[]
        }
        for key,article in self._article_table.items():
            data =  article.get_dict()
            table["articles"].append( data)        
        for j in self._jobs:
            table["jobs"].append(asdict(j))
                
        for f in self._filieres:
            table["filieres"].append(asdict(f))
                        
        for c in self._categories:
            table["categories"].append(asdict(c))
            
        return table
                
                