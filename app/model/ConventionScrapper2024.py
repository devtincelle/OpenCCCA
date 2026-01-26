



import os
from dataclasses import asdict
from model.ConventionParserHTML import ConventionParserHTML
from model.ConventionScrapperAbstract import ConventionScrapperAbstract


class ConventionScrapper2024(ConventionScrapperAbstract):

        def parse(self,file: str = None) -> dict:
            
            print("2024")
            print(file)
            
            if not file:
                print("Error file is None")
                return {}
            
            with open(file,"r") as f:
                html = f.read()
                convention = ConventionParserHTML().parse(html)
                final_data =  convention.get_dict()

                return final_data