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
        if not convention:
            print("Error: parser returned nothing")
            return {}

        return convention.filter_invalid().enrich().get_dict()
  