#!/usr/bin/env python
'''
Created on Oct 15, 2013

@author: mstana
'''


from gi.repository import GObject, Gtk

import subprocess
import sys
import os
import re
import signal


# probably not important imports

import tuned.profiles.locator as locator
import tuned.profiles.loader as loader
# import tuned.profiles.factory as factory
# import tuned.profiles.merger as merger


import tuned.exceptions
import tuned.logs
import tuned.consts as consts
import tuned.version as ver
import tuned.daemon.daemon as daemon
import tuned.utils.commands as commands
import tuned.admin.dbus_controller
import gtk_profile_loader




LICENSE = "licence"
NAME = "TUNED"
VERSION = "TUNED 2.3.0"
COPYRIGHT = "copyright"

AUTHORS = [
"",
"Based on old tuned/ktune code by:",
"- Philip Knirsch",
"- Thomas Woerner",

"Significant contributors:",
"- Jan Vcelak",
"- Jan Kaluza",
"- Jaroslav Skarvada",

"Other contributors:",
"- Petr Lautrbach",
"- Marcela Maslanova",
"- Jarod Wilson",
"- Jan Hutar"
]



class Base(object):
    
    def __init__(self):
        
        
        self.controller = tuned.admin.DBusController(consts.DBUS_BUS, consts.DBUS_OBJECT, consts.DBUS_INTERFACE)
#         admin = tuned.admin.Admin(self.controller)

        self.manager = gtk_profile_loader.Gtk_profile_loader(tuned.consts.LOAD_DIRECTORIES)
        
        
        
        
        
#         print active_profile.units['main']
#         someblock = None
#         for unit in  active_profile.units.keys():
#             someblock.prop1 = unit.name
#             someblock.prop2 = unit.type
#             someblock.prop3 = unit.option
#         
        
        #
        #    DIALOG ABOUT
        #
        self.about_dialog = Gtk.AboutDialog.new()
        self.about_dialog.set_name(NAME)
        self.about_dialog.set_version(VERSION)
        self.about_dialog.set_license(LICENSE)
        self.about_dialog.set_wrap_license(True)
        self.about_dialog.set_copyright(COPYRIGHT)
        self.about_dialog.set_authors(AUTHORS)
        #
        #    WINDOW MAIN
        #        
        self.builder = Gtk.Builder()
        self.builder.add_from_file("tuned-gui.glade")
        self.builder.connect_signals(self)
        #
        #    WIDGETS
        #
        self.main_window = self.builder.get_object("main_window")
        self.imagemenuitem_quit = self.builder.get_object("imagemenuitem_quit")
        self.imagemenuitem_about = self.builder.get_object("imagemenuitem_about")
        
        self.label_actual_profile = self.builder.get_object("label_actual_profile")
        self.label_recommended_profile = self.builder.get_object("label_recommemnded_profile")
        self.label_dbus_status = self.builder.get_object("label_dbus_status")
        self.label_summary_profile = self.builder.get_object("summary_profile_name")

        
#         test
        
        
        
        
        self.comboboxtext1 = self.builder.get_object("comboboxtext1")
        self.button_fast_change_profile = self.builder.get_object("button_fast_change_profile")
        
        self.switch_tuned_start_stop = self.builder.get_object("switch_tuned_start_stop")
        self.switch_tuned_startup_start_stop = self.builder.get_object("switch_tuned_startup_start_stop")
        #
        #Set factory values for objects
        #
        self.label_actual_profile.set_text(self.controller.active_profile())
        self.label_recommended_profile.set_text(self.controller.recommend_profile())
        self.refresh_summary_of_actual_profile()
        
        self.profile_list = self.controller.profiles()
        
        
        for profile in self.profile_list:
            self.comboboxtext1.append_text(profile)
            
#             TO DO: probably exist better way to print this
        self.label_dbus_status.set_text(str(bool(self.controller.is_running())))


#       TO DO:  need Add check if its correct in system
#       just ask system if for some properties
        
        self.switch_tuned_start_stop.set_active(True)
        self.switch_tuned_startup_start_stop.set_active(False)

        

        #
        #    CONNECTIONS
        #
        
        self.imagemenuitem_quit.connect("activate", Gtk.main_quit)
        self.imagemenuitem_about.connect("activate", self.execute_about)


        self.comboboxtext1.set_active(0)        
        self.button_fast_change_profile.connect("clicked", self.execute_change_profile)
    
        self.switch_tuned_start_stop.connect('button-press-event', self.execute_switch_tuned)
        self.switch_tuned_startup_start_stop.connect('button-press-event', self.execute_switch_tuned)
        
        if (self.main_window):
            self.main_window.connect("destroy", Gtk.main_quit)
            
        self.main_window.show()   
        
        
        
    def refresh_summary_of_actual_profile(self):
        
        
        self.active_profile = self.manager.get_profile(self.controller.active_profile())
        self.label_summary_profile.set_text(self.active_profile.name)
        
        text = ""
        for u in self.active_profile.units:
            
            text += "\n" + u + "\n" + "___________" + "\n" 

            
            for o in self.active_profile.units[u].options:
                text += "\n"+ o + " = " + self.active_profile.units[u].options[o]
                text += "\n"  
                
#         print self.text_view

#         buffer.insert_at_cursor(text)
        
            
    def execute_change_profile(self, profile):
                
        if profile is not None:
            self.controller.switch_profile(self.comboboxtext1.get_active_text())
            self.label_actual_profile.set_text(self.controller.active_profile())
            
        self.refresh_summary_of_actual_profile()
            

            
            
            
        
    def execute_switch_tuned(self, switch, no_idea_argument2):
        
        
        if switch == self.switch_tuned_start_stop:
              
            if self.switch_tuned_start_stop.get_active():
                subprocess.call(["service", "tuned", "stop"])
                
                
#                 print "service tuned stop"
            else:
                subprocess.call(["service", "tuned", "start"])
                self.controller = tuned.admin.DBusController(consts.DBUS_BUS, consts.DBUS_OBJECT, consts.DBUS_INTERFACE)
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
        
        
        
        
        
            
    def findProcess(self, processId):
        self.ps = subprocess.Popen("ps -ef | grep "+processId, shell=True, stdout=subprocess.PIPE)
        self.output = self.ps.stdout.read()
        self.ps.stdout.close()
        self.ps.wait()
        return self.output
    
    def isProcessRunning(self, processId):
        self.output = self.findProcess(processId)
        if re.search(processId, self.output) is None:
            return True
        else:
            return False
                
                
        
        
if __name__ == '__main__':
    
    if os.geteuid() != 0:
        os.error("Superuser permissions are required to run the daemon.")
        sys.exit(1)
        
#     Now we expect that tuned starts here with no problem and switch is prepared - need to add statement for check properties
    subprocess.call(["service", "tuned", "start"])


    base = Base()            
    Gtk.main()
 
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
