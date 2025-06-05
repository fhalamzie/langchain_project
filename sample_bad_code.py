# Sample code with formatting and quality issues (for demonstration)

import sys,os
import numpy as np
from typing import List
import pandas as pd
import json,yaml


class   BadlyFormattedClass:
    def __init__(self,name,age,email=None):
        self.name=name
        self.age = age
        self.email=email
        
    def process_data(self,data):
        # Security issue: using eval (bandit would catch this)
        result = eval("2 + 2")  # This is dangerous!
        
        # Poor formatting
        if data==None:return None
        elif len(data)<1:
            return []
        else:
            processed=[]
            for item in data:
                if item!=None and item!="":
                    processed.append(item.strip().upper())
            return processed

    def get_info(self):
        password = "hardcoded_password_123"  # Security issue
        return f"Name: {self.name}, Age: {self.age}, Email: {self.email or 'Not provided'}"

def badly_formatted_function(param1,param2,param3=None,param4="default"):
    """Function with poor formatting and style issues."""
    
    # Long line that exceeds recommended length (Black would fix this)
    very_long_variable_name_that_makes_this_line_extremely_long = param1 + param2 + str(param3) + param4 + "some additional text to make it even longer"
    
    # Poor spacing
    result={'param1':param1,'param2':param2,'param3':param3,'param4':param4}
    
    # Inconsistent quotes
    message = 'Processing: ' + "param1=" + str(param1) + ', param2=' + str(param2)
    
    return result,message

# Unused imports (flake8 would catch these)
# Missing docstrings (flake8 would warn about these)
# Inconsistent spacing and formatting throughout

if __name__=="__main__":
    # Poor formatting in main block
    obj=BadlyFormattedClass("John",30,"john@example.com")
    print(obj.get_info())
    
    data=["  test  ","","  another  ",None,"final"]
    result=obj.process_data(data)
    print(result)