'''
Created on Jan 29, 2014

@author: mstana
'''
#!/usr/bin/env python
'''
Created on Oct 15, 2013

@author: mstana
'''
from gi.repository import GObject, Gtk

import subprocess
import sys
import os


# probably not important imports
# import tuned.profiles.loader as loader
# import tuned.profiles.locator as locator
# import tuned.profiles.factory as factory
# import tuned.profiles.merger as merger


import tuned.exceptions
import tuned.logs
import tuned.consts as consts
import tuned.version as ver
import tuned.daemon.daemon as daemon








class Base(object):
    
    def __init__(self):
        
        
        self.builder = Gtk.Builder()
        self.builder.add_from_file("tuned-gui.glade")
        self.builder.connect_signals(self)

        # get widgets
        
        
        self.main_window = self.builder.get_object("main_window")
        self.actual_profile_variable = self.builder.get_object("actual_profile_variable")
        self.recomended_profile_variable = self.builder.get_object("recomended_profile_variable")
        self.comboboxtext1 = self.builder.get_object("comboboxtext1")
        self.button_fast_change_profile = self.builder.get_object("button_fast_change_profile")
        
        #Set factory values for objects
        
#         self.actual_profile_variable.set_text(self.app.profile_factory)
#         self.recomended_profile_variable.set_text(self.controller.recommend_profile())
#         self.profile_list = self.controller.profiles()
#         for profile in self.profile_list:
#             self.comboboxtext1.append_text(profile)
        
        
        # connections

        self.comboboxtext1.set_active(0)        
        self.button_fast_change_profile.connect("clicked", self.execute_change_profile)
        
        if (self.main_window):
            self.main_window.connect("destroy", Gtk.main_quit)
            
        self.main_window.show()   
            
    def execute_change_profile(self, profile):
                
        if profile is not None:
#             self.controller.switch_profile(self.comboboxtext1.get_active_text())
#             self.actual_profile_variable.set_text(self.controller.active_profile())
            pass

        
    def execute_cancel_button(self, button):
        exit(1)
    
    def inicialyze_tuned(self):
        
        if os.geteuid() != 0:
            print "si pako"
            os.error("Superuser permissions are required to run the daemon.")
            sys.exit(1)
            
        try:

            app = tuned.daemon.Application()
            app.attach_to_dbus(consts.DBUS_BUS, consts.DBUS_OBJECT, consts.DBUS_INTERFACE)
            app.run()
            
        except tuned.exceptions.TunedException as exception:
            os.error(str(exception))
            sys.exit(1)
        
    
if __name__ == '__main__':
    
    
    
    
    subprocess.call(["systemctl", "start", "tuned"])
    
    base = Base()            
#     base.inicialyze_tuned()
    Gtk.main()
    sys.exit(1)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
