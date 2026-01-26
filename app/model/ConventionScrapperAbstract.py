



import os
import uuid
from abc import ABC,abstractmethod

class ConventionScrapperAbstract(ABC):

    @abstractmethod
    def parse(self, file: str) -> dict:
        '''
            parse the content file into the model 
        '''
        
        ...