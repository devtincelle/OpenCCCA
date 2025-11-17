

from utils.PathManager import PathManager
from model.ConventionScrapper2015 import ConventionScrapper2015
from model.ConventionScrapper2021 import ConventionScrapper2021
from view.ConventionViewBuilder import ConventionViewBuilder
import os
import json
import shutil

class OpenCCCA():
    
    _scrapper:ConventionScrapper2021= ConventionScrapper2021()
    _builder:ConventionViewBuilder= ConventionViewBuilder()
    _paths:PathManager = PathManager()
    

    def __init__(self):
        ...
    
    def build_html(self):
        json_path = self._paths.get_data_folder()+"/convention.json"
        if os.path.exists(json_path) == False:
            OpenCCCA._scrapper.parse(json_path)
        OpenCCCA._builder.generate_fonction_html(json_path)
        
    def format_json_name(self,_table_name:str)->str:
                return "_".join([
                    "ccfpa",
                    _table_name
                ])


    def export_json(self,_output_folder:str=None,_pdf:str=None,):
        
        self._pdf = _pdf or self._paths.get_data_folder()+"/la-convention-collective-nationale-de-lanimation-et-la-grille-des-minima.pdf"
        output_folder = _output_folder or self._paths.get_export_folder()
        ...

        data = OpenCCCA._scrapper.parse(self._pdf)
       # Save JSON with UTF-8 encoding
       
        version_folder = output_folder+"/convention_V"+(data.get("version_data").get('version_consolidated') or "default")
        for key in ["articles","jobs","categories","filieres"]:
            os.makedirs(version_folder,exist_ok=True)
            json_path = version_folder+"/"+self.format_json_name(key)+'.json'
            with open(json_path, "w", encoding="utf-8") as file:
                json.dump(data.get(key), file, ensure_ascii=False, indent=2)
                
        # join a copy of the pdf with the export 
        pdf_copy = output_folder+"/"+os.path.basename(self._pdf)
        if os.path.exists(pdf_copy) ==False:
            shutil.copy(self._pdf,pdf_copy)
        
        return True
    


