

from utils.PathManager import PathManager
from controler.ConventionScrapper2015 import ConventionScrapper2015
from controler.ConventionScrapper2021 import ConventionScrapper2021
from controler.ConventionScrapper2024 import ConventionScrapper2024
from model.ConventionScrapperAbstract import ConventionScrapperAbstract
from view.ConventionViewBuilder import ConventionViewBuilder
import os
import json
import shutil
from typing import Dict

class OpenCCCA():
    
    _scrapper:ConventionScrapperAbstract= None
    _builder:ConventionViewBuilder= ConventionViewBuilder()
    _paths:PathManager = PathManager()
    
    _conventions_files:Dict[str,dict]= {
        "2015":"CCN_production_animation_consolidee_01032015.pdf",
        "2021":"la-convention-collective-nationale-de-lanimation-et-la-grille-des-minima.pdf",
        "2024":"gov_site_copypaste.html"
    }
    

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
                

    def _get_scrapper(self,_year:str,_file:str)->ConventionScrapperAbstract:
        extension = _file.split(".")[-1]
        if extension == "pdf":
            if _year=="2015":
                return ConventionScrapper2015()            
            if _year=="2021":
                return ConventionScrapper2021()
        if extension == "html":
            if _year=="2024":
                return ConventionScrapper2024()
        return ConventionScrapperAbstract()
        


    def export_json(self,_output_folder:str=None,_year:str="2024",_file_path=None):
        
        file_path = _file_path or self._paths.get_data_folder()+"/"+OpenCCCA._conventions_files.get(_year)
        file_path = file_path.replace("\\","/")
        output_folder = _output_folder or self._paths.get_export_folder()
        
        print(file_path)

        scrapper = self._get_scrapper(_year,file_path)
        print(scrapper)
        data = scrapper.parse(file_path)
       # Save JSON with UTF-8 encoding
       
        print(data)
        
        if not data :
            return 
       
        version_folder = output_folder+"/convention_V"+(data.get("version_data").get('version_consolidated') or "default")
        for key in ["articles","jobs","categories","filieres"]:
            os.makedirs(version_folder,exist_ok=True)
            json_path = version_folder+"/"+self.format_json_name(key)+'.json'
            with open(json_path, "w", encoding="utf-8") as file:
                json.dump(data.get(key), file, ensure_ascii=False, indent=2)
                
        # join a copy of the source with the export 
        source_copy = output_folder+"/"+os.path.basename(file_path)
        if os.path.exists(source_copy) ==False:
            shutil.copy(file_path,source_copy)
        
        return True
    


