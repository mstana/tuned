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
<<<<<<< HEAD
        return repr(self.code)

    def ProfileAlreadyExists(self):
=======
>>>>>>> ed6f8623e5434eb87149fc82ab2aac78f06322b0
        return repr(self.code)