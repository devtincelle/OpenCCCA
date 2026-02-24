import os
from dataclasses import asdict
from model.ConventionParserPDF  import ConventionParserPDF
from model.ConventionScrapperAbstract import ConventionScrapperAbstract

class ConventionScrapper2015(ConventionScrapperAbstract):

    def parse(self, file: str = None) -> dict:
        
        if not file:
            print("Error pdf is None")
            return {}
        if not os.path.exists(file):
            print("Error pdf does not exist:", file)
            return {}
    
        convention = ConventionParserPDF().parse(file)
        final_data =  convention.get_dict()

        return final_data
  