'''
Created on Mar 29, 2014

@author: mstana
'''

from configobj import ConfigObj
import os, sys
import tuned.profiles.profile as p

import tuned.consts

class Gtk_profile_loader(object):
    """
    Profiles loader for GUI Gtk purposes.
    """


    profiles = {}
    
    def __init__(self, directories):
        self.directories = directories
        self._load_all_profiles()

    def test_print_all_loaded(self):

        print "test begin"  

#         for profile, config in self.profiles.items():
#             
#             print profile
#             print config
#         print self.profiles.get("balanced").units
        
        
        
        
        print "test done"
                
    def load_profile_config(self, path):
        
        profile_config = ConfigObj(path)
                
        for section in profile_config.keys():
          for option in profile_config[section].keys():
            unit = profile_config[section][option]
                   
        return profile_config
    
    
    def _load_all_profiles(self):    
            
        for d in self.directories:
            
            for profile in os.listdir(d):
            
                if os.path.isdir(d + "/"+ profile):
                    self.profiles[profile] = p.Profile(profile,self.load_profile_config(d + "/" + profile + "/tuned.conf") )

                 
    def save_profile(self, profile):
        pass
        

        
    def get_names(self):
        return self.profiles.keys()
    
    def get_profile(self, profile):
        return self.profiles.get(profile)
        
        
        
        

if __name__ == '__main__':
    
    if os.geteuid() != 0:
        os.error("Superuser permissions are required to run the daemon.")
        sys.exit(1)
    print
    print
    
    test = Gtk_profile_loader(tuned.consts.LOAD_DIRECTORIES)
    test.test_print_all_loaded()
    print test.get_profile("balanced").name

    print
    print

#     print test.get_names()
    
#     print test.profiles.get("balanced")
