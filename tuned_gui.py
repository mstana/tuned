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
        #
        #    WINDOW MAIN
        #
        self.builder = Gtk.Builder()
        self.builder.add_from_file("tuned-gui.glade")
        self.builder.connect_signals(self)

        self.main_window = self.builder.get_object("mainWindow")
        self.windowProfileEditor = self.builder.get_object("windowProfileEditor")
        #
        #    WINDOW PROFILE EDITOR
        #
        self.windowProfileEditor.connect("delete-event", self.on_delete_event)

        self.entry_profile_name = self.builder.get_object("entryProfileName")
        self.combobox_include_profile = self.builder.get_object("comboboxIncludeProfile")
        self.notebook_plugins = self.builder.get_object("notebookPlugins")
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

        self.switch_tuned_start_stop = self.builder.get_object("switch_tuned_start_stop")
        self.switch_tuned_startup_start_stop = self.builder.get_object("switch_tuned_startup_start_stop")

        self.treeview_profile_manager = self.builder.get_object("treeviewProfileManager")
        #
        #    SET WIDGETS
        #
        self.treestore_profile_manager = Gtk.ListStore(GObject.TYPE_STRING)
        self.treeview_profile_manager.append_column(Gtk.TreeViewColumn("Profile", Gtk.CellRendererText(), text=0))
        self.treeview_profile_manager.set_model(self.treestore_profile_manager)

        for profile in self.manager.get_names():
            self.treestore_profile_manager.append([profile])
        self.treeview_profile_manager.get_selection().select_path(0)

        self.button_create_profile = self.builder.get_object("buttonCreateProfile")
        self.button_upadte_selected_profile = self.builder.get_object("buttonUpadteSelectedProfile")
        self.button_delete_selected_profile = self.builder.get_object("buttonDeleteSelectedProfile")

        self.button_cancel = self.builder.get_object("buttonCancel")
        self.button_cancel.connect("clicked", self.execute_cancel_window)

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

        self.switch_tuned_start_stop.set_active(self.is_service_running("tuned"))
        self.switch_tuned_startup_start_stop.set_active(self.service_run_on_start_up("tuned"))
        #
        #    CONNECTIONS
        #
        self.imagemenuitem_quit.connect("activate", Gtk.main_quit)
        self.imagemenuitem_about.connect("activate", self.execute_about)

        self.comboboxtext1.set_active(0)
        self.button_fast_change_profile.connect("clicked", self.execute_change_profile)

#     fix this with documnetation
        self.switch_tuned_start_stop.connect('button-press-event', self.execute_switch_tuned)
        self.switch_tuned_startup_start_stop.connect('button-press-event', self.execute_switch_tuned)

        self.button_create_profile.connect('clicked', self.execute_create_profile)
        self.button_upadte_selected_profile.connect('clicked', self.execute_update_profile)
        self.button_delete_selected_profile.connect('clicked', self.execute_remove_profile)

        self.button_confirm_profile = self.builder.get_object("buttonConfirmProfile")
        self.button_confirm_profile.connect("clicked", self.make_profile)

        self.main_window.connect("destroy", Gtk.main_quit)
        self.main_window.show()


    def make_profile(self, button):
#             TO DO - get values from window to object!
        profile = None
        profile.name = self.entry_profile_name.get_text()

        self.manager.add_profile(profile)

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

    def execute_remove_profile(self, button):
        profile = self.get_treeview_selected()
        try:
            self.manager.remove_profile(profile)
            self.treestore_profile_manager.remove(iter)
        except ManagerException as ex:
            self.error_dialog("Profile can not be remove", ex.__str__())

    def execute_cancel_window(self, button):
        self.windowProfileEditor.close()

    def execute_create_profile(self, button):
        self.reset_values_window_edit_profile()
        self.windowProfileEditor.show()

    def reset_values_window_edit_profile(self):
        self.entry_profile_name.set_text("")
#         self.combobox_include_profile.set_active() -- set to NONE
        for child in self.notebook_plugins.get_children():
            self.notebook_plugins.remove(child)



# 
#         self.label1 = self.builder.get_object("label12")
# 
#         self.notebook_plugins.append_page_menu(temp, None, self.label1)
# 
#         self.notebook_plugins.show_all()


    def get_treeview_selected(self):
        selection = self.treeview_profile_manager.get_selection()
        (model, iter) = selection.get_selected()
        if iter is None:
            self.error_dialog("No profile selected", "")
        return self.treestore_profile_manager.get_value(iter, 0)

    def execute_update_profile(self, button):
        profile = self.get_treeview_selected()
        try:
# TO DO: fill values in windowProfileManager
            pass
        except ManagerException as ex:
            self.error_dialog("Profile can not be remove", ex.__str__())

    def execute_change_profile(self, profile):
        self.spinner_fast_change_profile.start()
        if profile is not None:
            self.controller.switch_profile(self.comboboxtext1.get_active_text())
            self.label_actual_profile.set_text(self.controller.active_profile())

        self.refresh_summary_of_actual_profile()
        self.spinner_fast_change_profile.stop()


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
#                 print "Control statement: systemctl enable tuned"
            else:
                subprocess.call(["systemctl", "disable", "tuned"])
#                 print "Control statement: systemctl disable tuned"


    def execute_about(self, widget):
        self.about_dialog.run()
        self.about_dialog.hide()

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

if __name__ == '__main__':

    if os.geteuid() != 0:
        print os.error("Superuser permissions are required to run the daemon.")
        print "Aplication ends."
        sys.exit(1)

    subprocess.call(["service", "tuned", "start"])
    base = Base()

    Gtk.main()