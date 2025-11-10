
import re
import unicodedata

class ValueParser():
    
    def __init__(self):
        self._conform_table:dict = {
            "job_title":self._split_genders,
            "job_title_male":self._lower_capitalise,
            "job_title_female":self._lower_capitalise,
            "sector":self._lower_capitalise,
            "category":self._upper_strip_spaces,
            "position":self._lower_capitalise,
            "monthly_salary":self._extract_number,
            "daily_salary":self._extract_number,
            "is_cadre":self._cadre_to_bool
        }
        self._content_guess_table:dict = {
            "job_title":[self._is_job_title],
            "category":[self._is_roman_AB],
            "is_cadre":[self._is_NC_or_C],
            "definition":[self._is_paragraph],
            "position":[self._is_chef_or_confirme],
            "sector":[self._is_sector],
            "monthly_salary":[self._is_salary,self._greater_than_900],
            "weekly_salary":[self._is_salary,self._greater_than_400,self._lower_than_1000],
            "daily_salary":[self._is_salary,self._lower_than_300]
        }
        
    def _extract_number(self,s:str):
        if isinstance(s,str)==False:
            return s
        """
        Extracts the first number from a string, handling spaces as thousand separators.
        Returns the number as a float or None if no number is found.
        """
        # Remove spaces that are inside numbers
        s_cleaned = re.sub(r'(?<=\d) (?=\d)', '', s)
        
        # Match the first float or integer
        match = re.search(r'-?\d+(?:\.\d+)?', s_cleaned)
        if match:
            return float(match.group())
        return None
    def _matches_job_pattern_general(self,s,index=None):
        """
        Returns True if the string is likely a job title pattern:
        - Mostly uppercase letters
        - May optionally contain slashes '/' or line breaks '\n'
        """
        # Remove leading/trailing spaces
        s_clean = s.strip()
        
        # Regex pattern:
        # - Uppercase letters and accented letters
        # - Spaces
        # - Optional slashes '/' or line breaks '\n'
        pattern = r'^[A-ZÀ-Ÿ0-9\' ]+(?:[\/\n][A-ZÀ-Ÿ0-9\' ]+)*$'
        
        return bool(re.match(pattern, s_clean))
    
    def _is_paragraph(self,s,index=None):
        """
        Returns True if the string looks like a paragraph:
        - Contains multiple sentences ('.', '!', or '?')
        - Longer than a minimum length (e.g., 40 characters)
        """
        s_clean = s.strip()
        
        # Minimum length threshold
        if len(s_clean) < 40:
            return False
        
        if index:
            if index < 2:
             return False
        
        # Check if there is at least one sentence-ending punctuation
        if re.search(r'[.!?()]', s_clean):
            return True
        
        return False
    
    def to_english(self,text: str) -> str:
        # 1. Normalize the text to decompose accents (é -> e + ́)
        text = unicodedata.normalize('NFD', text)
        # 2. Remove accent characters
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        # 3. Remove all non-alphanumeric characters (keep letters, numbers, spaces)
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # 4. Optionally collapse multiple spaces and trim
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def guess_key(self,value,index=None)->str:
        if value is None:
            return 
        for key,check_list in self._content_guess_table.items():
            matches = [ check for check in check_list if check(value,index)]
            if len(matches) != len(check_list):
                continue
            return key  
        return None

    def _is_salary(self,value: str,index=None) -> bool:
        if isinstance(value,int) or isinstance(value,float):
            return True
        pattern = re.compile(r'^\s*\d{1,3}(?:[\s.,]\d{3})*(?:,\d{2})?\s*€\s*$')
        return bool(pattern.match(value))
    
    def _is_index2(self,s,index=None):
        return index==2
        
    def _is_job_title(self,s,index=None):
        
        """
        Returns True if the string contains only uppercase letters, spaces, slashes, or line breaks.
        """
        # Remove leading/trailing spaces
        s_clean = s.strip()
        
        # Regex: uppercase letters (including accented), spaces, slashes, line breaks
        pattern = r'^[A-ZÀ-Ÿ0-9\' /\\\n]+$'
        
        if len(s_clean)<2:
            return False
        
        is_uppercase =  re.match(pattern, s_clean) 
        is_capitalised = bool(self.is_upper(s_clean[0]) and self.is_upper(s_clean[1])==False)
        
        like = (is_uppercase or is_capitalised)
        
        return bool(
            like
            and len(s)>5
            and self._is_chef_or_confirme(s)==False
            and self._is_sector(s)==False
            and self._is_paragraph(s)==False
            and self._is_NC_or_C(s)==False
            )
    
    def _is_long_upper_case(self,value,index=None)->bool:
        return self.is_upper(value) and len(value) > 8 and len(value) < 30
    def _is_roman_AB(self,value,index=None)->bool:
        return value in ["I","II","III","IV","V","IIIA","III A","IIIB","III B","Hors catégorie"]
    def _is_NC_or_C(self,value,index=None)->bool:
        return value.upper() in ["NC","C"]  
    def _is_phrase(self,value,index=None)->bool:
        return self.is_upper(value)==False and len(value) > 30
    def _is_short_name(self,value,index=None)->bool:
        return self.is_upper(value,index=None)==False and len(value) < 30    
    def _is_sector(self,value,index=None)->bool:
        if len(value)<3:
            return False
        return (
            self.is_upper(value[0])==True 
            and index==0 or index==1
            and self.is_upper(value[1])==False 
            and len(value) < 30
            )
    def _has_euro_sign(self,value,index=None)->bool:
        return "€" in value
    def _greater_than_900(self,value,index=None)->bool:
        num = self._extract_number(value)
        if not num:
            return False
        return num > 900        

    def _greater_than_400(self,value,index=None)->bool:
        num = self._extract_number(value)
        if not num:
            return False
        return num > 400    
    def _lower_than_300(self,value,index=None)->bool:
        num = self._extract_number(value)
        if not num:
            return False
        return num < 300     
    def _lower_than_1000(self,value,index=None)->bool:
        num = self._extract_number(value)
        if not num:
            return False
        return num < 1000  
    def _is_chef_or_confirme(self,value,index=None)->bool:
        return self.to_english(value.lower()) in ["chef","confirme"]
    def is_upper(self,text,index=None):
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
    def _upper_strip_spaces(self,value):
        return self.strip(value.upper().replace(" ",""))


