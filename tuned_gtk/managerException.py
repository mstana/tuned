'''
Created on Apr 6, 2014

@author: mstana
'''

class ManagerException(Exception):
    """
    """
    
    def __init__(self, code):
        self.code = code
        
    def __str__(self):

        return repr(self.code)
    def profile_already_exists(self, text):
        return repr(text)

    def profile_already_exists(self):
        return repr(self.code)