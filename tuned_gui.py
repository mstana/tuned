#!/usr/bin/env python
'''
Created on Oct 15, 2013

@author: mstana
'''


from gi.repository import GObject, Gtk

import subprocess
import sys
import os
import signal


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

LICENSE = "licence"
NAME = "TUNED"
VERSION = "TUNED 2.3.0"
COPYRIGHT = "copyright"

AUTHORS = ["Authors"]




class Base(object):
    
    def __init__(self):
        
        
        
        self.about_dialog = Gtk.AboutDialog.new()
        self.about_dialog.set_name(NAME)
        self.about_dialog.set_version(VERSION)
        self.about_dialog.set_license(LICENSE)
        self.about_dialog.set_wrap_license(True)
        self.about_dialog.set_copyright(COPYRIGHT)
        self.about_dialog.set_authors(AUTHORS)

        
        
        
        
        
        self.builder = Gtk.Builder()
        self.builder.add_from_file("tuned-gui.glade")
        self.builder.connect_signals(self)

        # get widgets
        
        
        self.main_window = self.builder.get_object("main_window")
        
        self.imagemenuitem_quit = self.builder.get_object("imagemenuitem_quit")
        self.imagemenuitem_about = self.builder.get_object("imagemenuitem_about")
        
        
        self.actual_profile_variable = self.builder.get_object("actual_profile_variable")
        self.recomended_profile_variable = self.builder.get_object("recomended_profile_variable")
        
        
        
        
        self.comboboxtext1 = self.builder.get_object("comboboxtext1")
        self.button_fast_change_profile = self.builder.get_object("button_fast_change_profile")
        
        
        self.switch_tuned_start_stop = self.builder.get_object("switch_tuned_start_stop")
        self.switch_tuned_startup_start_stop = self.builder.get_object("switch_tuned_startup_start_stop")
        
        
        
        
        
        
        
        
        #Set factory values for objects
        
#         self.actual_profile_variable.set_text(self.app.profile_factory)
#         self.recomended_profile_variable.set_text(self.controller.recommend_profile())
#         self.profile_list = self.controller.profiles()
#         for profile in self.profile_list:
#             self.comboboxtext1.append_text(profile)
        
        
        # connections
        self.imagemenuitem_quit.connect("activate", Gtk.main_quit)
        self.imagemenuitem_about.connect("activate", self.execute_about)


        self.comboboxtext1.set_active(0)        
        self.button_fast_change_profile.connect("clicked", self.execute_change_profile)
    
        self.switch_tuned_start_stop.connect('button-press-event', self.execute_switch_tuned)
        self.switch_tuned_startup_start_stop.connect('button-press-event', self.execute_switch_tuned)
        
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
        
        
    def execute_switch_tuned(self, switch, no_idea_argument2):
        
        
        if switch == self.switch_tuned_start_stop:
              
            if self.switch_tuned_start_stop.get_active():
                subprocess.call(["service", "tuned", "stop"])
#                 print "service tuned stop"
            else:
                subprocess.call(["service", "tuned", "start"])
#                 print "service tuned start"    
                
        elif switch == self.switch_tuned_startup_start_stop: 
            
            if self.switch_tuned_startup_start_stop.get_active():

                subprocess.call(["systemctl", "disable", "tuned"])
#                 print "Control statement: systemctl enable tuned"
            else:

                subprocess.call(["systemctl", "enable", "tuned"])
#                 print "Control statement: systemctl disable tuned" 
            
            
    def execute_about(self, widget):
        self.about_dialog.run()
        self.about_dialog.hide()      
            
                
        
        
if __name__ == '__main__':
    
    
    if os.geteuid() != 0:
        os.error("Superuser permissions are required to run the daemon.")
        sys.exit(1)
    
    base = Base()            

    Gtk.main()
    sys.exit(1)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
