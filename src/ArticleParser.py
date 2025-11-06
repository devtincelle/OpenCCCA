
import re

class Article():
    def __init__(self,_start_line=None):
        self.title = None
        self.start_line = _start_line
        self.number = None
        self.body = []
        self.tables = []
        self.sub_articles = []
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
        sanitized_title = self.title.lower().split(" ")[0][:10]
        return f"{self.coord}_{sanitized_title}"
    
    def get_coord(self)->str:
        return f"{self.number}"
    
    def get_dict(self)->dict:
        
        return {
            "start_line":self.start_line,
            "title":self.title,
            "coord":self.coord,
            "pages":self.pages,
            "number":self.number,
            "body":self.body,
            "sub_articles":self.sub_articles,
            "tables":self.tables
        }
    
    def print(self):
        ...

class ArticleParser():
    
    _articles = {}
    _last_article_key = None
    _document_lines = []
    _line = -1


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
        
        if self._articles.get(current_key):
            print(self._articles.get(current_key))
            print(raw_tables)
            self._articles[current_key].tables.append(raw_tables)
                    
    def parse_sub_articles(self):
        new_articles = []
        for key,article in self._articles.items():
            line_number = article.start_line
            current_subarticle = None
            for line in article.body:
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
        for sa in new_articles:
            self._articles[sa.get_key()] = sa
                    
    def parse_tables(self):
        for key,article in self._articles.items():
            if len(article.table)>0:
                ...
                
                    
    def get_dict(self)->dict:
        table = {}
        for key,article in self._articles.items():
            data =  article.get_dict()
            #suba = [ self._article.get(key).get_dict() for key in data["subarticles"]]
            #data["subarticles"] =  suba
            table[key] = data
        return table
                
                