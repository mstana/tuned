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
    
    
    def test_values_in_profile(self, profile):
        
        print "fst"
        print profile.units.keys()
        print "scnd"
        for i in profile.units.keys():
            print i
        
        

    def test_print_all_loaded(self):
        print "test begin"  
        for profile, config in self.profiles.items():             
            print profile + " " + str(config.units.keys())
        print "test done"
        
        
                
    def load_profile_config(self, profile_name, path):
        conf_path = path + "/" + profile_name + "/tuned.conf"                
        profile_config = ConfigObj(conf_path)
        return profile_config


#         FLAT VERSION
#  
#         conf_path = path + "/" + profile_name + "/tuned.conf"        
#         profile_config = ConfigObj(conf_path)
#         for section in profile_config:
#             if (section == "main"):
#                 print profile_config[section]
#                 
#                 config = self.load_profile_config(profile_config[section]["include"], 
#                                                     self._locate_profile_path(profile_config[section]["include"]))                
#                 config.merge(profile_config)
#                 return config
#             
#         return profile_config
    
    def _locate_profile_path(self, profile_name):
        
        for d in self.directories:
            for profile in os.listdir(d):
                if os.path.isdir(d + "/"+ profile) and profile == profile_name:
                    return d
    
    
    def _load_all_profiles(self):    
            
        for d in self.directories:
            for profile in os.listdir(d):
                if os.path.isdir(d + "/"+ profile):
                    self.profiles[profile] = p.Profile(profile,self.load_profile_config(profile, d))
                    
                 
    def save_profile(self, profile):
                
        path = tuned.consts.LOAD_DIRECTORIES[1] + "/" + profile.name     
        config = ConfigObj()
        config.filename = path + tuned.consts.CONF_PROFILE_FILE
        config.initial_comment = "#", "tuned configuration","#"

        print profile.units.items()    
        print profile.name
        print profile.options
#         print profile.units["main"].options
        
        try:
            config["main"] = profile.options
             
#             {"include" : profile.options["include"]}
        except KeyError: 
            
            pass #no problem just profile dont have include

        for name, unit in profile.units.items():
            config[name] = unit.options
            
        if not os.path.exists(path): 
# TO DO: add exception for rewrite profile!
            os.makedirs(path)            
        config.write()

        
    def get_names(self):
        return self.profiles.keys()
    
    def get_profile(self, profile):
        return self.profiles[profile]

 
if __name__ == '__main__':
      
    if os.geteuid() != 0:
        os.error("Superuser permissions are required to run the daemon.")
        sys.exit(1)

      
    t = Gtk_profile_loader(tuned.consts.LOAD_DIRECTORIES)
    
#     pr = t.get_profile("sap")
    
    
    t.save_profile(t.get_profile("sap"))
