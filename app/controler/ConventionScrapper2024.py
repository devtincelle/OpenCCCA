



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
            
            with open(file, "r", encoding="utf-8") as f:
                html = f.read()                              # ← only this needs the file open

            convention = ConventionParserHTML().parse(html)
            if not convention:
                print("Error: parser returned nothing")
                return {}

            final_data = convention.filter_invalid().enrich().get_dict()
            return final_data