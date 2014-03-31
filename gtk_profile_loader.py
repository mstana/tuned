'''
Created on Mar 29, 2014

@author: mstana
'''

from configobj import ConfigObj
import os, sys
import tuned.profiles.profile as p
import tuned.profiles.merger as merger
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

        for profile, config in self.profiles.items():
             
            print profile
            print config
        print self.profiles.get("balanced").units
        
        
        
        
        print "test done"
                
    def load_profile_config(self, profile_name, path):

        conf_path = path + "/" + profile_name + "/tuned.conf"
        profile_config = ConfigObj(conf_path)        

        for section in profile_config.keys():
          for option in profile_config[section].keys(): 
            
            if (section == "main" and option == "include"):
                
                config = self.load_profile_config(profile_config[section][option], 
                                                    self._locate_profile_path(profile_config[section][option]))                
                config.merge(profile_config)

                return config

                        
                            
                        
#             here I return config obj - if it will have the same "values" as my conf - ok, if not 


        return profile_config
    
    def _locate_profile_path(self, profile_name):
        
        for d in self.directories:
            for profile in os.listdir(d):
                if os.path.isdir(d + "/"+ profile) and profile == profile_name:
                    return d
    
    
    def _load_all_profiles(self):    
            
        for d in self.directories:
            for profile in os.listdir(d):
                if os.path.isdir(d + "/"+ profile):
#                     print d
                    self.profiles[profile] = p.Profile(profile,self.load_profile_config( profile, d) )

                 
    def save_profile(self, profile):
        
        config = ConfigObj()

#         https://wiki.python.org/moin/ConfigObj -  not big issue
#         config['section'] = value
#         config['option'] = {'key': 'value', 'key2': ['val1', 'val2']}

        config.filename = tuned.consts.LOAD_DIRECTORIES[1] + "/" + profile.name + "/tuned.conf"
        config.write()
        

        
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
#     test.test_print_all_loaded()
    
#     test.save_profile(test.get_profile("myprofile"))
#     print test.get_profile("myprofile").units

    
    print test.get_names()
       
#     print test.profiles.get("balanced")
