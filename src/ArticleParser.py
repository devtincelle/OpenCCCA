
import re

class Article():
    def __init__(self,_start_line=None):
        self.title = None
        self.start_line = _start_line
        self.number = None
        self.body = []
        self.tables = []
        self.sub_articles = []
        self.pages = []

    def __str__(self)->str:
        return f"<ARTICLE : {self.number } {self.title} --- {self.body[:20]}....{len(self.body)} >"
    
    def __repr__(self)->str:
        return str(self)
    
    def get_key(self)->str:
        sanitized_title = self.title.lower().split(" ")[0][:10]
        return f"{self.number}_{sanitized_title}"
    
    def print(self):
        print("--------------------------------------")
        print(self.number)
        print(self.title)
        print("--------------------------------------")
        print(f" TABLES {len(self.tables)}")
        if len(self.sub_articles)>0:
            for sa in self.sub_articles:
                sa.print()
        else:
            print(self.body)

class ArticleParser():
    
    _articles = {}
    _last_article_key = None


    def extraire_articles(self,texte: str):
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
            article = Article()
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
            articles = self.extraire_articles(line)
            if len(articles)>0:
                # new article detected 
                current_key = articles[0].get_key()
                self._articles[current_key] = articles[0]
                self._articles[current_key].page = _page_number
                self._last_article_key = current_key
                continue
            # add line to current article
            if self._articles.get(current_key):
                self._articles[current_key].body.append(line)
        
        if self._articles.get(current_key):
            print(self._articles.get(current_key))
            self._articles[current_key].pages.append(page)
            print(raw_tables)
            self._articles[current_key].tables.append(raw_tables)
                    
    def parse_sub_articles(self):
        index = -1
        for key,article in self._articles.items():
            index+=1
            line_number = -1
            current_subarticle = None
            for line in article.body:
                line_number+=1
                sub_articles = self.extraire_sous_articles(line,line_number)
                if len(sub_articles)>0:
                    if current_subarticle:
                        article.sub_articles.append(current_subarticle)
                    current_subarticle = sub_articles[0]
                    continue
                if current_subarticle:
                    current_subarticle.body.append(line)
                
                