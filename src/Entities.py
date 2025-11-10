
import re
from dataclasses import dataclass

@dataclass
class Filiere():
    start_line:int=None
    name:str=None
    number:str=None
    line_number:int=None
    key:str=None
    article:str=None
    
@dataclass
class Category():
    start_line:int=None
    name:str=None
    number:str=None
    key:str=None
    article:str=None
    
@dataclass
class Sector():
    start_line:int=None
    name:str=None
    number:str=None
    key:str=None 
    article:str=None
       
@dataclass
class Job():
    start_line:int=None
    name:str=None
    number:str=None
    key:str=None
    article:str=None
    
    
       
