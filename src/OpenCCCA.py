

from PathManager import PathManager
from ConventionScrapper2015 import ConventionScrapper2015
from ConventionScrapper2021 import ConventionScrapper2021
from ConventionViewBuilder import ConventionViewBuilder
import os

class OpenCCCA():
    
    _scrapper:ConventionScrapper2021= ConventionScrapper2021()
    _builder:ConventionViewBuilder= ConventionViewBuilder()
    _paths:PathManager = PathManager()
    

    def __init__(self):
        self._pdf = self._paths.get_data_folder()+"/CCN_production_animation_consolidee_01032015.pdf"
        self._pdf = self._paths.get_data_folder()+"/la-convention-collective-nationale-de-lanimation-et-la-grille-des-minima.pdf"
        ...

    
    def build_html(self):
        json_path = self._paths.get_data_folder()+"/convention.json"
        if os.path.exists(json_path) == False:
            OpenCCCA._scrapper.parse(json_path)
        OpenCCCA._builder.generate_fonction_html(json_path)


    def build_json(self):
        json_path = self._paths.get_data_folder()+"/conv_fonctions.json"
        OpenCCCA._scrapper.parse(self._pdf,json_path)
        return json_path


