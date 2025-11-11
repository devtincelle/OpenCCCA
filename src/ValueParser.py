
import re
import unicodedata
from GuessContext import GuessContext
from Utils import to_english

class ValueParser():
    
    def __init__(self):
        self._conform_table:dict = {
            "job_title":self._split_genders,
            "job_title_male":self._lower_capitalise,
            "job_title_female":self._lower_capitalise,
            "sector":self._lower_capitalise,
            "category":self._conform_category,
            "position":self._lower_capitalise,
            "monthly_salary":self._extract_number,
            "weekly_salary":self._extract_number,
            "daily_salary":self._extract_number,
            "is_cadre":self._cadre_to_bool
        }
        self._content_guess_table:dict = {
            "job_title":[self._is_job_title],
            "category":[self._is_roman_AB],
            "is_cadre":[self._is_NC_or_C],
            "definition":[self._is_definition],
            "position":[self._is_chef_or_confirme],
            "sector":[self._is_sector],
            "monthly_salary":[self._is_salary,self._greater_than_900],
            "weekly_salary":[self._is_salary,self._greater_than_400,self._lower_than_1000],
            "daily_salary":[self._is_salary,self._lower_than_300]
        }
        
    def _extract_number(self,text):
        if isinstance(text,str)==False:
            return text
        """
        Extracts the first number from a string, handling spaces as thousand separators.
        Returns the number as a float or None if no number is found.
        """
        # Remove spaces that are inside numbers
        s_cleaned = re.sub(r'(?<=\d) (?=\d)', '', text)
        
        # Match the first float or integer
        match = re.search(r'-?\d+(?:\.\d+)?', s_cleaned)
        if match:
            return float(match.group())
        return None

    
    def _is_definition(self,context:GuessContext=None):
        if self._from_admin_table(context):
            return False
        return self._is_paragraph(context)
    
    def _is_paragraph(self,context:GuessContext=None):
        """
        Returns True if the string looks like a paragraph:
        - Contains multiple sentences ('.', '!', or '?')
        - Longer than a minimum length (e.g., 40 characters)
        """
        s_clean = context.value.strip()
        
        # Minimum length threshold
        if len(s_clean) < 40:
            return False
        
        if context.column_index:
            if context.column_index <3:
             return False
        
        # Check if there is at least one sentence-ending punctuation
        if re.search(r'[.!?()]', s_clean):
            return True
        
        return False
    

    def guess_key(self,context:GuessContext=None)->str:
        if context is None:
            return 
        for key,check_list in self._content_guess_table.items():
            matches = [ check for check in check_list if check(context)]
            if len(matches) != len(check_list):
                continue
            return key  
        return None

    def _is_salary(self,context:GuessContext=None) -> bool:
        if isinstance(context.value,int) or isinstance(context.value,float):
            return True
        pattern = re.compile(r'^\s*\d{1,3}(?:[\s.,]\d{3})*(?:,\d{2})?\s*€\s*$')
        return bool(pattern.match(context.value))
    
    def _is_index2(self,context:GuessContext=None):
        return context.column_index==2
        
    def _from_admin_table(self,context:GuessContext=None):
        if context.table_number:
            return context.table_number in [1,2,3] and context.nb_columns < 20
        return False
        
    def _is_female_job_title(self,context:GuessContext=None):
        if self._from_admin_table(context)==False:
            return False
        print(context.value)
        return self._is_job_title(context) and self._first_word_is_female(context)
    
    def _first_word_is_female(self,context:GuessContext=None)->bool:
        return context.value.split(" ")[0][-1] in ['e']
    
    def _is_job_title(self,context:GuessContext=None):
        
        """
        Returns True if the string contains only uppercase letters, spaces, slashes, or line breaks.
        """
        # Remove leading/trailing spaces
        s_clean = context.value.strip()
        
        # Regex: uppercase letters (including accented), spaces, slashes, line breaks
        pattern = r'^[A-ZÀ-Ÿ0-9\' /\\\n]+$'
        
        if len(s_clean)<2:
            return False
        
        if self._from_admin_table(context):
            is_capitalised = bool(self.is_upper(s_clean[0]) and self.is_upper(s_clean[1])==False)
            return is_capitalised and self._is_roman_AB(context)==False
        
        is_uppercase =  re.match(pattern, s_clean) 
        return bool(
            is_uppercase
            and len(context.value)>5
            and self._is_roman_AB(context)==False
            and self._is_chef_or_confirme(context)==False
            and self._is_sector(context)==False
            and self._is_paragraph(context)==False
            and self._is_NC_or_C(context)==False
            )
    
    def _is_long_upper_case(self,context:GuessContext=None)->bool:
        return self.is_upper(context.value) and len(context.value) > 8 and len(context.value) < 30
    def _is_roman_AB(self,context:GuessContext=None)->bool:
        return context.value in ["I","II","III","IV","V","IIIA","III A","IIIB","III B","Hors catégorie"]
    def _is_NC_or_C(self,context:GuessContext=None)->bool:
        return context.value.upper() in ["NC","C"]  
    def _is_phrase(self,context:GuessContext=None)->bool:
        return self.is_upper(context.value)==False and len(context.value) > 30
    def _is_short_name(self,context:GuessContext=None)->bool:
        return self.is_upper(context.value)==False and len(context.value) < 30    
    def _is_capitalized(self,word:str)->bool:
        if len(word)<2:
            return False
        return self.is_upper(word[0]) and not self.is_upper(word[1])
    def _is_sector(self,context:GuessContext=None)->bool:
        if len(context.value)<3:
            return False
        words = context.value.split(" ")
        capitalized_words = [ w for w in words if self._is_capitalized(w)]
        all_capitalized = len(capitalized_words) == len(words)
        return (
            all_capitalized 
            and len(context.value) < 30
            )
    def _has_euro_sign(self,context:GuessContext=None)->bool:
        return "€" in context.value
    def _greater_than_900(self,context:GuessContext=None)->bool:
        num = self._extract_number(context.value)
        if not num:
            return False
        return num > 900        

    def _greater_than_400(self,context:GuessContext=None)->bool:
        num = self._extract_number(context.value)
        if not num:
            return False
        return num > 400    
    def _lower_than_300(self,context:GuessContext=None)->bool:
        num = self._extract_number(context.value)
        if not num:
            return False
        return num < 300     
    def _lower_than_1000(self,context:GuessContext=None)->bool:
        num = self._extract_number(context.value)
        if not num:
            return False
        return num < 1000  
    def _is_chef_or_confirme(self,context:GuessContext=None)->bool:
        return to_english(context.value.lower()) in ["chef","confirme"]
    
    def is_upper(self,text=None):
        """
        Check if the input string is fully uppercase (letters, including accented, and spaces).

        Args:
            text (str): Input string.

        Returns:
            bool: True if all letters are uppercase, False otherwise.
        """
        # Remove non-letter characters for the check
        letters_only = ''.join(c for c in text if c.isalpha())
        return letters_only.isupper() and len(letters_only) > 0
    
    def strip(self,_value)->str:
        return _value.replace("\n"," ")
    
    def conform(self,key,value):
        if not value:
            return value
        if not self._conform_table.get(key):
            return value
        conformed = self._conform_table[key](value)
        return conformed

    def _lower_capitalise(self,value):
        return self.strip(value.lower().capitalize())
    
    def _split_genders(self,value):
        data = {
            "neutral":"",
            "male":None,
            "female":None
        }
        if isinstance(value,str):
            words = value.replace("\n"," ").lower().split(" ")
            job_male = []
            job_female = []
            is_male = True
            first_letters = None
            for w in words:
                if not first_letters:
                    half = int(len(w)/2)
                    first_letters = w[:half]
                    job_male.append(w)
                    continue
                if first_letters in w:
                    is_male=False
                if is_male==False:
                    job_female.append(w)
                else:
                    job_male.append(w)
            data = {
                "male":self._lower_capitalise(" ".join(job_male)),
                "female":self._lower_capitalise(" ".join(job_female))
            }
        return data

    def _cadre_to_bool(self,value):
        if value == "NC":
            return False
        if value == "C":
            return True
        return value    
    
    def _conform_category(self,value):
        if value == "Hors catégorie":
            return value
        return self._upper_strip_spaces(value)
    
    
    def _upper_strip_spaces(self,value):
        if value == "Hors catégorie":
            return value
        return self.strip(value.upper().replace(" ",""))


