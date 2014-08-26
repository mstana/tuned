

import os
import sys

import tuned.plugins.repository

from tuned.exceptions import TunedException



class Manager(object):
    
    def __init__(self):
        self.repository = tuned.plugins.repository.Repository()
    
    

    
if __name__ == '__main__':
        
    if os.geteuid() != 0:
        os.error("Superuser permissions are required to run the daemon.")
        sys.exit(1)
  
    man = Manager()