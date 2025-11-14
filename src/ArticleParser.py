
import re
from TableParser import TableParser
from ValueParser import ValueParser
from Entities import Article,Filiere,Table,Job,Category
from Utils import to_english,clean_text
from typing import List,Dict
from dataclasses import asdict


class ArticleParser():
    
    _doc_version = {}
    _articles = {}
    _jobs:List[Job] = []
    _filieres:List[Filiere] = []
    _categories: List[Category] = []
    _last_article_key = None
    _document_lines = []
    _line = -1
    _table_parser=TableParser()
    _value_parser=ValueParser()

    def set_doc_version(self,_data:str):
        self._doc_version = _data

    def extraire_articles(self,texte: str,_start_line=None):
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
    
    def extraire_sous_articles(self,texte: str,line_number):
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
            articles = self.extraire_articles(line,self._line)
            if len(articles)>0:
                # new article detected 
                current_key = articles[0].get_key()
                self._articles[current_key] = articles[0]
                self._articles[current_key].pages.append( _page_number)
                self._last_article_key = current_key
                continue
            # add line to current article
            if self._articles.get(current_key):
                self._articles[current_key].body.append(line)
                
        # find a way to get the table number rigth again 
        
        table_number = -1
        if self._articles.get(current_key):
            for t in raw_tables:
                table_number+=1
                table = Table(
                    article=current_key,
                    page_number=_page_number,
                    rows=t
                ).clean()
                self._articles[current_key].tables.append(table)
                    
    def parse_sub_articles(self):
        new_articles = []
        for key,article in self._articles.items():
            line_number = article.start_line
            current_subarticle = None
            raw_body = article.body
            article.body = []
            for line in raw_body:
                line_number+=1
                sub_articles = self.extraire_sous_articles(line,line_number)
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
            self._articles[sa.get_key()] = sa
                    
    def parse_filieres(self)->List[Filiere]:
        last_filiere:Filiere = None
        last_job_title:str = None
        for article in self._articles.values():
            line_number = article.start_line-1
            for line in article.body:
                line_number+=1
                filiere = self.parse_filiere_from_line(line)
                if filiere:
                    filiere.article = article.get_key()
                    filiere.start_line = line_number
                    filiere.source = self._doc_version
                    last_filiere = filiere
                    article.filieres.append(filiere)
                    continue
                if last_filiere:
                    if not last_filiere.text :
                        last_filiere.text = ""
                    last_filiere.text+=to_english(clean_text(line.lower()).replace(" ",""))
                    
        merged:Dict[str,Filiere] = {}
        for article in self._articles.values():
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
        for key,article in self._articles.items():
            if len(article.tables)==0:
                continue
            for table in article.tables:
                table_counter +=1
                table.table_number = table_counter
                table.article = article.get_key()
                jobs = self._table_parser.parse_jobs(table)
                # connect job to filiere according to job title string 
                for job in jobs:
                    job.source = self._doc_version
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

        for article in self._articles.values():
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
        for key,article in self._articles.items():
            data =  article.get_dict()
            #table["articles"].append( data)        
        for j in self._jobs:
            table["jobs"].append(asdict(j))
                
        for f in self._filieres:
            table["filieres"].append(asdict(f))
                        
        for c in self._categories:
            table["categories"].append(asdict(c))
            
        return table
                
                