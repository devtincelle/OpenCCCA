


import pdfplumber
import json
import uuid
import os

class PathManager():
    
    def __init__(self):
        self._root = os.path.dirname(os.path.dirname(__file__))
        ...

    def get_html_template_folder(self):
        return self._root+"/src/templates"

    def get_data_folder(self):
        return self._root+"/data"
