

from PathManager import PathManager
from ConventionScrapper import ConventionScrapper
from ConventionViewBuilder import ConventionViewBuilder
import os

class OpenCCCA():
    
    _scrapper:ConventionScrapper= ConventionScrapper()
    _builder:ConventionViewBuilder= ConventionViewBuilder()
    _paths:PathManager = PathManager()
    

    def __init__(self):
        self._pdf = self._paths.get_data_folder()+"/CCN_production_animation_consolidee_01032015.pdf"
        ...

    
    def build_html(self):
        json_path = self._paths.get_data_folder()+"/convention.json"
        if os.path.exists(json_path) == False:
            OpenCCCA._scrapper.parse_job_table(json_path)
        OpenCCCA._builder.generate_fonction_html(json_path)


    def build_json(self):
        json_path = self._paths.get_data_folder()+"/conv_fonctions.json"
        OpenCCCA._scrapper.parse_job_table(self._pdf,json_path)
        return json_path


