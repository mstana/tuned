#!/usr/bin/env python
'''
Created on Oct 15, 2013

@author: mstana
'''



import gi.repository.GObject as GObject
import gi.repository.Gtk as Gtk

import subprocess
import sys
import os
import re

import tuned.logs
import tuned.consts as consts
import tuned.version as ver
import tuned.daemon.daemon as daemon
import tuned.utils.commands as commands
import tuned.admin.dbus_controller
import tuned_gtk.profileLoader
import tuned_gtk.gui_plugin_loader

from tuned_gtk.managerException import ManagerException




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
        self.manager = tuned_gtk.profileLoader.ProfileLoader(tuned.consts.LOAD_DIRECTORIES)
        self.plugin_loader = tuned_gtk.gui_plugin_loader.GuiPluginLoader()
        self.builder = Gtk.Builder()
        self.builder.add_from_file("tuned-gui.glade")
        self.builder.connect_signals(self)        
        #
        #    WINDOW MAIN
        #
        self.main_window = self.builder.get_object("mainWindow")
        #
        #    WINDOW PROFILE EDITOR
        #
        self.window_profile_editor = self.builder.get_object("windowProfileEditor")
        self.window_profile_editor.connect("delete-event", self.on_delete_event)
        self.entry_profile_name = self.builder.get_object("entryProfileName")
        self.combobox_include_profile = self.builder.get_object("comboboxIncludeProfile")
        self.notebook_plugins = self.builder.get_object("notebookPlugins")
        
        self.button_add_plugin = self.builder.get_object("buttonAddPlugin")
        self.button_open_raw = self.builder.get_object("buttonOpenRaw")
        self.button_cancel = self.builder.get_object("buttonCancel")
        
        self.button_open_raw.connect("clicked", self.execute_open_raw_button)
        self.button_add_plugin.connect("clicked", self.execute_add_plugin_to_notebook)
        self.button_cancel.connect("clicked", self.execute_cancel_window_profile_editor)

        #
        #    WINDOW PROFILE EDITOR RAW
        #  
        self.window_profile_editor_raw = self.builder.get_object("windowProfileEditorRaw")
        self.window_profile_editor_raw.connect("delete-event", self.on_delete_event)
        self.button_apply = self.builder.get_object("buttonApply")
        self.button_apply.connect("clicked", self.execute_apply_window_profile_editor_raw)
        self.button_cancel_raw = self.builder.get_object("buttonCancelRaw")
        self.button_cancel_raw.connect("clicked", self.execute_cancel_window_profile_editor_raw)
        self.textview1 = self.builder.get_object("textview1")
        self.textview1.set_editable(True)
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
        #    DIALOG MESSAGE ERROR
        #
        self.messagedialog_pperation_error = self.builder.get_object("messagedialogOperationError")
        #
        #    DIALOG MESSAGE ADD PLUGIN
        #        
        self.treestore_actual_plugins = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING)

        self.dialog_add_plugin = self.builder.get_object("dialogAddPlugin")
        #
        #    GET WIDGETS
        #
        self.imagemenuitem_quit = self.builder.get_object("imagemenuitem_quit")
        self.imagemenuitem_about = self.builder.get_object("imagemenuitem_about")

        self.label_actual_profile = self.builder.get_object("label_actual_profile")
        self.label_recommended_profile = self.builder.get_object("label_recommemnded_profile")
        self.label_dbus_status = self.builder.get_object("label_dbus_status")
        self.label_summary_profile = self.builder.get_object("summary_profile_name")

        self.comboboxtext1 = self.builder.get_object("comboboxtext1")
        self.button_fast_change_profile = self.builder.get_object("buttonFastChangeProfile")
        self.spinner_fast_change_profile = self.builder.get_object("spinnerFastChangeProfile")
        self.spinner_fast_change_profile.hide()

        self.switch_tuned_start_stop = self.builder.get_object("switch_tuned_start_stop")
        self.switch_tuned_startup_start_stop = self.builder.get_object("switch_tuned_startup_start_stop")

        self.treeview_profile_manager = self.builder.get_object("treeviewProfileManager")
        self.treeview_actual_plugins = self.builder.get_object("treeviewActualPlugins")
        #
        #    SET WIDGETS
        #

        
        self.dict_profiles = {}
#         TO DO: DO IT IN BETTER WAY! Q: How to set up value in combobox if I know text not possition in liststore?
        self.profile_name_store = Gtk.ListStore(str)
        self.profile_name_store.append([None])
        self.dict_profiles[None] = 0
        
        i = 1
        for profile in self.manager.get_names():
            self.dict_profiles[profile] = i
            i = i+1
            self.profile_name_store.append([profile])
        
        self.treestore_plugins = Gtk.ListStore(GObject.TYPE_STRING)
        self.treestore_plugins.append([None])
        
        for plugin in self.plugin_loader.plugins:
            print plugin.name
            self.treestore_plugins.append([plugin.name])
        
        self.combobox_plugins = self.builder.get_object("comboboxPlugins")
        self.combobox_plugins.set_model(self.treestore_plugins)
        cell = Gtk.CellRendererText()
        self.combobox_plugins.pack_start(cell, True)
        self.combobox_plugins.add_attribute(cell,'text', 0 )
        
        self.combobox_main_plugins = self.builder.get_object("comboboxMainPlugins")
        self.combobox_main_plugins.set_model(self.treestore_plugins)
        cell = Gtk.CellRendererText()
        self.combobox_main_plugins.pack_start(cell, True)
        self.combobox_main_plugins.add_attribute(cell,'text', 0 )
        
        self.combobox_include_profile.set_model(self.profile_name_store)
        cell = Gtk.CellRendererText()
        self.combobox_include_profile.pack_start(cell, True)
        self.combobox_include_profile.add_attribute(cell,'text', 0 )

        self.treestore_profile_manager = Gtk.ListStore(GObject.TYPE_STRING)
        self.treeview_profile_manager.append_column(Gtk.TreeViewColumn("Profile", Gtk.CellRendererText(), text=0))
        self.treeview_profile_manager.set_model(self.treestore_profile_manager)

        for profile in self.manager.get_names():
            self.treestore_profile_manager.append([profile])
        self.treeview_profile_manager.get_selection().select_path(0)

        self.button_create_profile = self.builder.get_object("buttonCreateProfile")
        self.button_upadte_selected_profile = self.builder.get_object("buttonUpadteSelectedProfile")
        self.button_delete_selected_profile = self.builder.get_object("buttonDeleteSelectedProfile")

        self.label_actual_profile.set_text(self.controller.active_profile())
        self.label_recommended_profile.set_text(self.controller.recommend_profile())
        self.refresh_summary_of_actual_profile()

        self.comboboxtext1.set_model(self.profile_name_store)
#             TO DO: probably exist better way to print this
        self.label_dbus_status.set_text(str(bool(self.controller.is_running())))

#       TO DO:  need Add check if its correct in system
#       just ask system if for some properties

        self.switch_tuned_start_stop.set_active(self.is_service_running("tuned"))
        self.switch_tuned_startup_start_stop.set_active(self.service_run_on_start_up("tuned"))
        #
        #    CONNECTIONS
        #
        self.imagemenuitem_quit.connect("activate", Gtk.main_quit)
        self.imagemenuitem_about.connect("activate", self.execute_about)

        self.comboboxtext1.set_active(0)
        self.button_fast_change_profile.connect("clicked", self.execute_change_profile)

        self.switch_tuned_start_stop.connect('button-press-event', self.execute_switch_tuned)
        self.switch_tuned_startup_start_stop.connect('button-press-event', self.execute_switch_tuned)

        self.button_create_profile.connect('clicked', self.execute_create_profile)
        self.button_upadte_selected_profile.connect('clicked', self.execute_update_profile)
        self.button_delete_selected_profile.connect('clicked', self.execute_remove_profile)

        self.button_confirm_profile_create = self.builder.get_object("buttonConfirmProfileCreate")
        self.button_confirm_profile_update = self.builder.get_object("buttonConfirmProfileUpdate")
        
        self.button_confirm_profile_create.connect("clicked", self.execute_make_profile)
        self.button_confirm_profile_update.connect("clicked", self.execute_modify_profile)
        

        self.main_window.connect("destroy", Gtk.main_quit)
        self.main_window.show()

    
    def execute_make_profile(self, button):
        raise NotImplemented()
    
    def execute_modify_profile(self, button):
        
#             TO DO - get values from window to object!
        modify_profile = self.manager.get_profile(self.get_treeview_selected())
        modify_profile.name = self.entry_profile_name.get_text()
        
        try:
            self.manager.add_profile(modify_profile)
            self.window_profile_editor.close()
        except ManagerException:
            self.error_dialog("You can not do this.", "info")
        
        
        
    def on_delete_event(self, window, data):
        window.hide()
        return True

    def refresh_summary_of_actual_profile(self):
        self.active_profile = self.manager.get_profile(self.controller.active_profile())
        self.label_summary_profile.set_text(self.active_profile.name)
        text = ""
        for u in self.active_profile.units:
            text += "\n" + u + "\n" + "___________" + "\n"
            for o in self.active_profile.units[u].options:
                text += "\n"+ o + " = " + self.active_profile.units[u].options[o]
                text += "\n"

    def _get_active_profile_name(self):
        return self.manager.get_profile(self.controller.active_profile()).name


    def execute_remove_profile(self, button):
        profile = self.get_treeview_selected()
        try:
            if (self._get_active_profile_name() == profile):
                self.error_dialog("You can not remove active profile", "Please deactivate profile by choosind another!")
                return
            self.manager.remove_profile(profile)
            self.treestore_profile_manager.remove(iter)
        except ManagerException as ex:
            self.error_dialog("Profile can not be remove", ex.__str__())

    def execute_cancel_window_profile_editor(self, button):
        self.window_profile_editor.close()
        
    def execute_cancel_window_profile_editor_raw(self, button):
        self.window_profile_editor_raw.close()      
      
    def execute_open_raw_button(self, data):
        
        profile_name = self.get_treeview_selected()
        text_buffer = self.textview1.get_buffer()
        text_buffer.set_text(self.manager.get_raw_profile(profile_name))
        self.window_profile_editor_raw.show_all()  


    def execute_choose_plugin_dialog(self):

        self.button_add_plugin = self.builder.get_object("buttonAddPluginDialog")
        self.button_cancel_add_plugin_dialog = self.builder.get_object("buttonCloseAddPlugin")        
        self.button_cancel_add_plugin_dialog.connect('clicked', lambda d: self.dialog_add_plugin.hide())
        self.button_add_plugin.connect('clicked', self.execute_add_plugin_dialog_choose)
        
        self.dialog_add_plugin.connect('destroy', lambda d: self.dialog_add_plugin.hide())

        self.dialog_add_plugin.run()
        self.dialog_add_plugin.hide()

    def execute_add_plugin_dialog_choose(self, data):            
        if (self.combobox_plugins.get_active() == -1 or
           self.combobox_plugins.get_active() == None):
            self.error_dialog("No plugin selected", "To add plugin You have to select one.")
        else:     
            self.dialog_add_plugin.hide()
            return self.combobox_plugins.get_active()

    def execute_add_plugin_to_notebook(self, data):

        plugin = self.execute_choose_plugin_dialog() 

        if (plugin == None):
            return
        
        treestore = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING)        
#         TO DO: store data to treestore - option, value for plugin

        plugin_data = self.plugin_loader.load_plugin(plugin)
        print plugin_data
        
        treestore.append(["testOption","testValue"])

        treeview = Gtk.TreeView(treestore) 
        renderer = Gtk.CellRendererText()
        column_option = Gtk.TreeViewColumn("Option", renderer, text=0)
        column_value = Gtk.TreeViewColumn("Value", renderer, text=1)
        treeview.append_column(column_value)
        treeview.append_column(column_option)
        
#         TO DO: Store Name of plugin
        plugin_name = Gtk.Label(plugin.name)
        
        
        
#         add plugin to profile backend
        
        self.notebook_plugins.append_page_menu( treeview, plugin_name, None)
        self.notebook_plugins.show_all()
        
        
        
#         profile = self.manager.get_profile("powersave")
#         print profile.name
#         
#         
#         print "units -------------"
#         
#         for name, unit in profile.units.items():
#             print "======================================================================"
#             print name # name of section - sysctl
#             
#             print 
#             print "options: " + str(unit._options) # option = value
#             print "------"
#             print "name: " + str(unit.name)
#             print "------"
#             print "type: " + str(unit.type)
#             print "------"
#             print "enabled: " + str(unit.enabled)
#             print "------"
#             print "replace: " + str(unit.replace)
#             print "------"
#             print "devices: " + str(unit.devices)
#             
#         print "done"
#         

        
    
    def execute_apply_window_profile_editor_raw(self, data):
        print data
        text_buffer = self.textview1.get_buffer()
        start = text_buffer.get_start_iter()
        end = text_buffer.get_end_iter()
        profile_name = self.get_treeview_selected()
        self.manager.set_raw_profile(profile_name, text_buffer.get_text(start,end, True))
        
        
#         refresh window_profile_editor
    
    def execute_create_profile(self, button):
        self.reset_values_window_edit_profile()
        self.button_confirm_profile_create.show()
        self.button_confirm_profile_update.hide()
        self.button_open_raw.hide()
        self.window_profile_editor.show()


    def reset_values_window_edit_profile(self):
        self.entry_profile_name.set_text("")
        self.combobox_include_profile.set_active(0)
        for child in self.notebook_plugins.get_children():
            self.notebook_plugins.remove(child)


    def get_treeview_selected(self):
        selection = self.treeview_profile_manager.get_selection()
        (model, iter) = selection.get_selected()
        if iter is None:
            self.error_dialog("No profile selected", "")
        return self.treestore_profile_manager.get_value(iter, 0)


    def unit_to_plugin(self, profile_units):
        """
        conver units to plugins 
        """        
        
        print profile_units
        
        plugins = self.plugin_loader.plugins
        
        active_plugins = set()
        
        for name, unit in profile_units.items():
            for plugin in plugins:
                if (plugin.name == unit.name):
#                     firt set up values of plugin and then add
#                     options: {'kernel.sched_autogroup_enabled': '1'}
                    print str(plugin.name) + str(unit.name)
                    
                    print "options " + str(plugin._get_config_options())

                    active_plugins.add(plugin)
            
            
            print "======================================================================"
            print name # name of section - sysctl
            
            print 
            print "options: " + str(unit._options) # option = value
            print "------"
            print "name: " + str(unit.name)
            print "------"
            print "type: " + str(unit.type)
            print "------"
            print "enabled: " + str(unit.enabled)
            print "------"
            print "replace: " + str(unit.replace)
            print "------"
            print "devices: " + str(unit.devices)
            
        print "done"
        
        return plugins


    def execute_update_profile(self, button):
        
        self.button_confirm_profile_create.hide()
        self.button_confirm_profile_update.show()
        self.button_open_raw.show()
        label12 = self.builder.get_object("label12")
        label12.set_text("Update Profile")
        
        for child in self.notebook_plugins.get_children():
            self.notebook_plugins.remove(child)

        profile_name = self.get_treeview_selected()

        if profile_name == None :
            self.error_dialog("No profile Selected", "To update profile please select profile.")
            return
        if (self._get_active_profile_name() == profile_name):
            self.error_dialog("You can not update active profile", "Please deactivate profile by choosing another!")
            return
        
        if (self.manager.is_profile_removable(profile_name)):
            
            profile = self.manager.get_profile(profile_name)

            self.entry_profile_name.set_text(profile.name)
            try:
                included = profile.options["include"]
                profile.options["include"]
#                 do in better way man!
                self.combobox_include_profile.set_active(self.dict_profiles[profile.options["include"]])
            except KeyError:
                self.combobox_include_profile.set_active(0)

            for name, unit in profile.units.items():
                self.notebook_plugins.append_page_menu(self.make_treestore_for_profile_unit(unit),Gtk.Label(unit.name), None)

            self.notebook_plugins.show_all()
            self.window_profile_editor.show()
        else:
            self.error_dialog("You can not update Factory profile", "")

    def make_treestore_for_profile_unit(self, profile_unit):

        treestore = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING)                
        for option, value in profile_unit.options.items():
            treestore.append([value,option])
        
        treeview = Gtk.TreeView(treestore) 
        renderer = Gtk.CellRendererText()
        column_option = Gtk.TreeViewColumn("Option", renderer, text=0)
        column_value = Gtk.TreeViewColumn("Value", renderer, text=1)
        treeview.append_column(column_value)
        treeview.append_column(column_option)

        return treeview

    def execute_change_profile(self, profile):
        self.spinner_fast_change_profile.show()
        self.spinner_fast_change_profile.start()
        if profile is not None:
            self.controller.switch_profile(self.comboboxtext1.get_active_text())
            self.label_actual_profile.set_text(self.controller.active_profile())
        self.refresh_summary_of_actual_profile()
        self.spinner_fast_change_profile.stop()
        self.spinner_fast_change_profile.hide()


    def execute_switch_tuned(self, switch, no_idea_argument2):
        if switch == self.switch_tuned_start_stop:
            if self.switch_tuned_start_stop.get_active():
                subprocess.call(["service", "tuned", "stop"])
            else:
                subprocess.call(["service", "tuned", "start"])
                self.controller = tuned.admin.DBusController(consts.DBUS_BUS, consts.DBUS_OBJECT, consts.DBUS_INTERFACE)
        elif switch == self.switch_tuned_startup_start_stop:
            if self.switch_tuned_startup_start_stop.get_active():
                subprocess.call(["systemctl", "enable", "tuned"])
            else:
                subprocess.call(["systemctl", "disable", "tuned"])




    def find_process(self, processId):
        self.ps = subprocess.Popen("ps -ef | grep "+processId, shell=True, stdout=subprocess.PIPE)
        self.output = self.ps.stdout.read()
        self.ps.stdout.close()
        self.ps.wait()
        return self.output

    def is_process_running(self, processId):
        self.output = self.find_process(processId)
        if re.search(processId, self.output) is None:
            return True
        else:
            return False

    def is_service_running(self, service):
        if subprocess.call(["service", service, "status"]) == 0:
            return True
        return False

    def service_run_on_start_up(self, service):
        if subprocess.call(["systemctl", "status", service]) == 0:
            return True
        return False

    def error_dialog(self, error, info):
        self.messagedialog_pperation_error.set_markup(error)
        self.messagedialog_pperation_error.format_secondary_text(info)
        self.messagedialog_pperation_error.run()
        self.messagedialog_pperation_error.hide()
    
    def execute_about(self, widget):
        self.about_dialog.run()
        self.about_dialog.hide()

if __name__ == '__main__':

    if os.geteuid() != 0:
        print os.error("Superuser permissions are required to run the daemon.")
        print "Aplication ends."
        sys.exit(1)

    subprocess.call(["service", "tuned", "start"])
    base = Base()

    Gtk.main()