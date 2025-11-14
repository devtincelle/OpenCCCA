


class DBImportPreparator():
  
    ''''

        "fonction": "Mouleur volume",
        "version_feminisee": "Mouleuse volume",
        "category": "IV",
        "definition": "Fabrique les moules et les versions d\u00e9finitives des objets et personnages dans les mat\u00e9riaux retenus.",
        "nom": "Mouleur volume",
        "salaire_brut_mensuel": 1624.0,
        "salaire_brut_journalier": 82.45,
        "id": "2ac2b7ba"

    '''
    
    def prepare(self,_dict)->dict:
        jobs = _dict.get("jobs")
        filieres = _dict.get("filieres")
        sectors = _dict.get("sectors")
        articles = _dict.get("articles")
        
        prepared = {}
        
        if isinstance(jobs,list) : 
            for j in jobs:
                print(j)
        if isinstance(filieres,list) : 
            for f in filieres:
                print(f)
        if isinstance(sectors,list) : 
            for s in sectors:
                print(s)
        if isinstance(articles,list) : 
            for a in articles:
                print(a)
                
        return prepared
            