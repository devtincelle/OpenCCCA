

from jinja2 import Environment, FileSystemLoader
from utils.PathManager import PathManager
import json

class ConventionViewBuilder():

    _paths:PathManager = PathManager()

    def __init__(self):
        ...

    def generate_fonction_html(self,_json_path:str=None):

        data = {}
        with open(_json_path,"r") as file:
            data= json.loads(file.read())

        # Setup Jinja environment
        path = self._paths.get_html_template_folder()
        env = Environment(loader=FileSystemLoader(path))
        template = env.get_template('template_fonctions.html')

        # Render template
        output = template.render(roles=data)
        output_path = self._paths.get_data_folder()+"/tableau_fonctions.html"

        # Save output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
