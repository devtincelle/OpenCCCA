



import os
from dataclasses import asdict
from model.ConventionParser import ConventionParser

class ConventionScrapper2021():

    def parse(self, _pdf: str = None) -> dict:
        
        if not _pdf:
            print("Error pdf is None")
            return {}
        if not os.path.exists(_pdf):
            print("Error pdf does not exist:", _pdf)
            return {}
    
        convention = ConventionParser().parse(_pdf)
        final_data =  asdict(convention)

        return final_data
  
    

