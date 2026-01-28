import os

class PathManager():
    
    def __init__(self):
        self._root = os.path.dirname(os.path.dirname(__file__))
        ...

    def get_html_template_folder(self):
        return self._root+"/app/view/templates"

    def get_data_folder(self):
        return self._root+"/../resources"
    
    def get_export_folder(self):
        return self._root+"/export"
