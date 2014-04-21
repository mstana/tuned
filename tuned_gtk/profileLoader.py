'''
Created on Mar 29, 2014

@author: mstana
'''

import configobj
import os, sys
import tuned.profiles.profile as p
import tuned.profiles.merger as merger
import tuned.consts
import shutil
import managerException

class ProfileLoader(object):
    """
    Profiles loader for GUI Gtk purposes.
    """
    profiles = {}

    def __init__(self, directories):
        self.directories = directories
        self._load_all_profiles()


    def get_raw_profile(self, profile_name):
        file = self._locate_profile_path(profile_name) +"/" + profile_name +"/"+ "tuned.conf"
        with open(file, 'r') as f:
            return f.read()

    def set_raw_profile(self, profile_name, config):
        profilePath = self._locate_profile_path(profile_name)
        self.get_profile(profile_name).
        if (profilePath == tuned.consts.LOAD_DIRECTORIES[1]):
            file = profilePath +"/" + profile_name +"/"+ "tuned.conf"
            with open(file, 'w') as f:
                f.write(config)
        else:
            raise managerException.ManagerException(profile_name + " profile is stored in "+ profilePath + " and can not be storet do this location")

    def load_profile_config(self, profile_name, path):
        conf_path = path + "/" + profile_name + "/tuned.conf"     

        profile_config = configobj.ConfigObj(conf_path)
        return profile_config

    def _locate_profile_path(self, profileName):
        for d in self.directories:
            for profile in os.listdir(d):
                if os.path.isdir(d + "/"+ profile) and profile == profileName:
                    path = d
        return path

    def _load_all_profiles(self):    
        for d in self.directories:
            for profile in os.listdir(d):
                if os.path.isdir(d + "/"+ profile):
                    try:
                        self.profiles[profile] = p.Profile(profile,self.load_profile_config(profile, d))
                    except configobj.ParseError:
                        print "can not make \""+ profile +"\" profile without correct config on path: " + d 
#                     except:
#                         raise managerException.ManagerException("Can not make profile")
#                         print "can not make \""+ profile +"\" profile without correct config with path: " + d


    def save_profile(self, profile):
                
        path = tuned.consts.LOAD_DIRECTORIES[1] + "/" + profile.name     
        config = configobj.ConfigObj()
        config.filename = path + tuned.consts.CONF_PROFILE_FILE
        config.initial_comment = "#", "tuned configuration","#"
        
        try:
            config["main"] = profile.options
        except KeyError:
            pass #profile dont have main section 

        for name, unit in profile.units.items():
            config[name] = unit.options
            
        if not os.path.exists(path): 
            os.makedirs(path)  
        else:
#             mozes prepisat ale nesmies na nejaky co uz existuje!
            raise managerException.ManagerException("Profile Exists already")
        config.write()

    def update_profile(self, profile):
                
        path = tuned.consts.LOAD_DIRECTORIES[1] + "/" + profile.name     
        config = configobj.ConfigObj()
        config.filename = path + tuned.consts.CONF_PROFILE_FILE
        config.initial_comment = "#", "tuned configuration","#"
        
        try:
            config["main"] = profile.options
        except KeyError:
            pass #profile dont have main section 

        for name, unit in profile.units.items():
            config[name] = unit.options
#         hej, vazne chces prepisat? -> ano prepiseme, nie neprepiseme

        os.makedirs(path)  
        config.write()

        
    def get_names(self):
        return self.profiles.keys()
    
    
    def get_profile(self, profile):
        return self.profiles[profile]
    
    
    def add_profile(self, profile):
        self.profiles[profile.name] = profile
        self.save_profile(profile)
    
    def remove_profile(self, profileName):
        
        profilePath = self._locate_profile_path(profileName)
    
        if (self.is_profile_removable(profileName)):
            shutil.rmtree(profilePath + "/" + profileName)
            self._load_all_profiles()
        else:
            raise managerException.ManagerException(profileName + " profile is stored in "+ profilePath)
    
    def is_profile_removable(self, profile_name):
        #            profile is in /etc/profile
        profilePath = self._locate_profile_path(profile_name)
        if (profilePath == tuned.consts.LOAD_DIRECTORIES[1]):
            return True
        else:
            return False


        
# if __name__ == '__main__':
#        
#     if os.geteuid() != 0:
#         os.error("Superuser permissions are required to run the daemon.")
#         sys.exit(1)
#  
#        
#     t = ProfileLoader(tuned.consts.LOAD_DIRECTORIES)
# 
#     print t.get_raw_profile("myprofile")
#     t.set_raw_profile("myprofile", "a")
