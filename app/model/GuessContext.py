from dataclasses import dataclass

@dataclass
class GuessContext():
    value:any=None
    table_number:int=None
    row_number:int=None
    nb_columns:int=None
    column_index:int=None
    page_number:int=None
    line_number:int=None

       
