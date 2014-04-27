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
import configobj

import tuned.logs
import tuned.consts as consts
import tuned.version as ver
import tuned.daemon.daemon as daemon
import tuned.utils.commands as commands
import tuned.admin.dbus_controller
import tuned_gtk.profileLoader
import tuned_gtk.gui_plugin_loader
import tuned.profiles.profile as profile

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
    
    """
    GUI class for program Tuned.
    """

    def __init__(self):
        

        self.controller = tuned.admin.DBusController(consts.DBUS_BUS, consts.DBUS_OBJECT, consts.DBUS_INTERFACE)
        self.manager = tuned_gtk.profileLoader.ProfileLoader(tuned.consts.LOAD_DIRECTORIES)
        self.plugin_loader = tuned_gtk.gui_plugin_loader.GuiPluginLoader()
        self.builder = Gtk.Builder()
        self.builder.add_from_file("tuned-gui.glade")
        self.builder.connect_signals(self)        
        
        print "Here are supproted devices: "
        
        for plugin in self.plugin_loader.plugins:
            try:
                print plugin._get_config_options()
            except:
                print "no value for " + str(plugin.name)
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
        self.button_remove_plugin = self.builder.get_object("buttonRemovePlugin")
        self.button_open_raw = self.builder.get_object("buttonOpenRaw")
        self.button_cancel = self.builder.get_object("buttonCancel")

        self.button_open_raw.connect("clicked", self.execute_open_raw_button)
        self.button_add_plugin.connect("clicked", self.execute_add_plugin_to_notebook)
        self.button_remove_plugin.connect("clicked", self.execute_remove_plugin_from_notebook)
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
        self.active_combo_text = None
        self.treeview_profile_manager = self.builder.get_object("treeviewProfileManager")

        self.treeview_actual_plugins = self.builder.get_object("treeviewActualPlugins")
        #
        #    SET WIDGETS
        #
        self.treestore_actual_plugins = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING)
        self.treestore_profile_manager = Gtk.ListStore(GObject.TYPE_STRING)



        self.treestore_plugins = Gtk.ListStore(GObject.TYPE_STRING)
        self.treestore_plugins.append([None])
        for plugin in self.plugin_loader.plugins:
            print plugin.name
            self.treestore_plugins.append([plugin.name])

        self.combobox_plugins = self.builder.get_object("comboboxPlugins")
        self.combobox_plugins.set_model(self.treestore_plugins)


        self.combobox_main_plugins = self.builder.get_object("comboboxMainPlugins")
        self.combobox_main_plugins.set_model(self.treestore_plugins)
        cell = Gtk.CellRendererText()
        self.combobox_main_plugins.pack_start(cell, True)
        self.combobox_main_plugins.add_attribute(cell,'text', 0 )

        self.combobox_include_profile.set_model(self.treestore_profile_manager)
        cell = Gtk.CellRendererText()
        self.combobox_include_profile.pack_start(cell, True)
        self.combobox_include_profile.add_attribute(cell,'text', 0 )

        
        self.treeview_profile_manager.append_column(Gtk.TreeViewColumn("Profile", Gtk.CellRendererText(), text=0))
        self.treeview_profile_manager.set_model(self.treestore_profile_manager)
        self.treestore_profile_manager.append([None])
        for profile in self.manager.get_names():
            self.treestore_profile_manager.append([profile])
        self.treeview_profile_manager.get_selection().select_path(0)

        self.button_create_profile = self.builder.get_object("buttonCreateProfile")
        self.button_upadte_selected_profile = self.builder.get_object("buttonUpadteSelectedProfile")
        self.button_delete_selected_profile = self.builder.get_object("buttonDeleteSelectedProfile")

        self.label_actual_profile.set_text(self.controller.active_profile())
        self.label_recommended_profile.set_text(self.controller.recommend_profile())
        self.refresh_summary_of_actual_profile()

        self.comboboxtext1.set_model(self.treestore_profile_manager)
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

        self.button_confirm_profile_create.connect("clicked", self.on_click_button_confirm_profile_create)
        self.button_confirm_profile_update.connect("clicked", self.on_click_button_confirm_profile_update)

        self.main_window.connect("destroy", Gtk.main_quit)
        self.main_window.show()

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
        label9 = self.builder.get_object("label9")
        label9.set_text(text)    
        

    def _get_active_profile_name(self):
        return self.manager.get_profile(self.controller.active_profile()).name

    def execute_remove_profile(self, button):
        profile = self.get_treeview_selected()
        try:
            if (self._get_active_profile_name() == profile):
                self.error_dialog("You can not remove active profile", "Please deactivate profile by choosind another!")
                return
            self.manager.remove_profile(profile)
            for item in self.treestore_profile_manager:
                if item[0] == profile:
                    iter = self.treestore_profile_manager.get_iter(item.path)
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

    def on_click_choose_plugin_dialog_add_button(self, data):
        plugin_name = self.combobox_plugins.get_active_text()
        if (plugin_name == -1 or plugin_name == None):
            self.error_dialog("No plugin selected", "To add plugin You have to select one.")
        else: 
            self.dialog_add_plugin.hide()
            self.active_combo_text = self.combobox_plugins.get_active_text()

    def execute_add_plugin_to_notebook(self, data):
        self.choose_plugin_dialog()
        plugin_name = self.active_combo_text

#      TO DO:   toto nechceme aby prebehlo ked choose_plugin dialog vrati cancel alebo 
        if plugin_name == None:
            self.error_dialog("Please, choose some plugin" , "")
        plugin_to_tab = None
        for plugin in self.plugin_loader.plugins:
            if plugin.name == plugin_name:
                for children in self.notebook_plugins:

                    if plugin_name == self.notebook_plugins.get_menu_label_text(children):
                        self.error_dialog("Plugin " + plugin_name + " is already in profile." , "")
                        return
                plugin_to_tab = plugin
                self.notebook_plugins.append_page_menu( self.make_treestore_for_data(plugin_to_tab._get_config_options()) , Gtk.Label(plugin_to_tab.name), Gtk.Label(plugin_to_tab.name))
                self.notebook_plugins.show_all()

    def execute_remove_plugin_from_notebook(self, data):  

        treestore = Gtk.ListStore(GObject.TYPE_STRING)
        for children in self.notebook_plugins.get_children():
            treestore.append([self.notebook_plugins.get_menu_label_text(children)])
        self.combobox_plugins.set_model(treestore)
        result = self.choose_plugin_dialog()

        selected = self.combobox_plugins.get_active_text()
        for children in self.notebook_plugins.get_children():
            if (self.notebook_plugins.get_menu_label_text(children) == selected):
                self.notebook_plugins.remove(children)
        self.combobox_plugins.set_model(self.treestore_plugins)
#        TO DO: treba este refresh tohto profilu v hlavnom okne

        
    def execute_apply_window_profile_editor_raw(self, data):
        text_buffer = self.textview1.get_buffer()
        start = text_buffer.get_start_iter()
        end = text_buffer.get_end_iter()
        profile_name = self.get_treeview_selected()
        self.manager.set_raw_profile(profile_name, text_buffer.get_text(start,end, True))
        self.error_dialog("Profile Editor will be closed.", "for next updates reopen profile.")
        self.window_profile_editor.hide()
#         refresh window_profile_editor
    
    def execute_create_profile(self, button):
        self.reset_values_window_edit_profile()
        self.button_confirm_profile_create.show()
        self.button_confirm_profile_update.hide()
        self.button_open_raw.hide()

        for child in self.notebook_plugins.get_children():
            self.notebook_plugins.remove(child)

        self.window_profile_editor.show()

    def reset_values_window_edit_profile(self):
        self.entry_profile_name.set_text("")
        self.combobox_include_profile.set_active(0)
        for child in self.notebook_plugins.get_children():
            self.notebook_plugins.remove(child)

    def get_treeview_selected(self):
        """
        Return value of treeview which is selected at calling moment of this function.
        """
        selection = self.treeview_profile_manager.get_selection()
        (model, iter) = selection.get_selected()
        if iter is None:
            self.error_dialog("No profile selected", "")
        return self.treestore_profile_manager.get_value(iter, 0)

    def on_click_button_confirm_profile_update(self, data):                
            profile_name = self.get_treeview_selected()
            prof = self.data_to_profile_config()
            self.manager.remove_profile(profile_name)
            for item in self.treestore_profile_manager:
                try: 
                    if item[0] == profile_name:
                        iter = self.treestore_profile_manager.get_iter(item.path)
                        self.treestore_profile_manager.remove(iter)
                except KeyError:
                    raise KeyError(" this cant happen ")
                except:
                    pass
            self.manager.update_profile(prof)
            self.treestore_profile_manager.append([prof.name])
            self.window_profile_editor.hide()

    def data_to_profile_config(self):
        name = self.entry_profile_name.get_text() 
        config = configobj.ConfigObj()

        activated = self.combobox_include_profile.get_active()
        model = self.combobox_include_profile.get_model()

        include = model[activated][0]
        if include != None:
            config["main"] = {"include":include}
        for children in self.notebook_plugins:
            acumulate_options = {}
            for item in children.get_model():
                if item[0] != "None":
                    acumulate_options[item[1]]= item[0]

            config[self.notebook_plugins.get_menu_label_text(children)] = acumulate_options    
        return profile.Profile(name, config)

    def on_click_button_confirm_profile_create(self, data):
        try:
            prof = self.data_to_profile_config()
            self.manager.save_profile(prof)
            self.manager._load_all_profiles()
            self.treestore_profile_manager.append([prof.name])
            self.window_profile_editor.hide()
        except:
            self.error_dialog("Profile with name " + prof.name + " already exist.", "Please choose another name for profile")

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
            model = self.combobox_include_profile.get_model()
            selected = 0
            for item in model:
                try: 
                    if item[0] == profile.options["include"]:
                        selected = int(item.path.to_string())     
                except:
                    pass   
            self.combobox_include_profile.set_active(selected)
            for name, unit in profile.units.items():
                self.notebook_plugins.append_page_menu(self.make_treestore_for_data(unit.options),Gtk.Label(unit.name), Gtk.Label(unit.name))
            self.notebook_plugins.show_all()
            self.window_profile_editor.show()
        else:
            self.error_dialog("You can not update Factory profile", "")

    def make_treestore_for_data(self, data):
        """
        This prepare treestore and treeview for data and return treeview
        """
        treestore = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING)                
        for option, value in data.items():
            treestore.append([str(value),option])
        
        treeview = Gtk.TreeView(treestore) 
        renderer = Gtk.CellRendererText()
        column_option = Gtk.TreeViewColumn("Option", renderer, text=0)
        column_value = Gtk.TreeViewColumn("Value", renderer, text=1)
        treeview.append_column(column_value)
        treeview.append_column(column_option)
        treeview.enable_grid_lines = True
        treeview.connect('row-activated', self.change_value_dialog)

        return treeview

    def execute_change_profile(self, button):
        self.spinner_fast_change_profile.show()
        self.spinner_fast_change_profile.start()
        if button is not None:
            text = self.comboboxtext1.get_active_text()
            if text is not None:
                self.controller.switch_profile(text)
                self.label_actual_profile.set_text(self.controller.active_profile())
                self.refresh_summary_of_actual_profile()
            else:
                self.error_dialog("No profile selected", "")
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
        """
        General error dialog with two fields. Primary and secondary text fields.
        """
        self.messagedialog_pperation_error.set_markup(error)
        self.messagedialog_pperation_error.format_secondary_text(info)
        self.messagedialog_pperation_error.run()
        self.messagedialog_pperation_error.hide()

    def execute_about(self, widget):
        self.about_dialog.run()
        self.about_dialog.hide()

    def change_value_dialog(self, tree_view, path, treeview_column):
    
        """
        Shows up dialog after double click on treeview which has to be stored in notebook of plugins. 
        This dialog allows you to chagne specific option's value in plugin.
        """
        model = tree_view.get_model() 
        dialog = self.builder.get_object("changeValueDialog")
        button_apply = self.builder.get_object("buttonApplyChangeValue")
        button_cancel = self.builder.get_object("buttonCancel1")
        entry1 = self.builder.get_object("entry1")
        text = self.builder.get_object("labelTextDialogChangeValue")

        text.set_text(model.get_value(model.get_iter(path), 1))
        entry1.set_text(model.get_value(model.get_iter(path), 0))

        dialog.connect('destroy', lambda d: dialog.hide())
        button_cancel.connect('clicked', lambda d: dialog.hide())
        signal_id_apply = button_apply.connect('clicked',lambda x : dialog.hide() )
        signal_id_apply1 = button_apply.connect('clicked', lambda d: model.set_value(model.get_iter(path), 0, entry1.get_text()))

        dialog.run()
        dialog.hide()
        button_cancel.disconnect(signal_id_apply)
        button_apply.disconnect(signal_id_apply1)



    def choose_plugin_dialog(self):
        """
        Shows up dialog with combobox where are stored plugins avaible to add.
        """
        self.button_add_plugin = self.builder.get_object("buttonAddPluginDialog")
        self.button_cancel_add_plugin_dialog = self.builder.get_object("buttonCloseAddPlugin")        
        self.button_cancel_add_plugin_dialog.connect('clicked', lambda d: self.dialog_add_plugin.hide())
        self.dialog_add_plugin.connect('destroy', lambda d: self.dialog_add_plugin.hide())
        self.button_add_plugin.connect('clicked', self.on_click_choose_plugin_dialog_add_button)
        return self.dialog_add_plugin.run()
        self.dialog_add_plugin.hide()



if __name__ == '__main__':

    if os.geteuid() != 0:
        print os.error("Superuser permissions are required to run the daemon.")
        print "Aplication ends."
        sys.exit(1)

    subprocess.call(["service", "tuned", "start"])
    base = Base()

    Gtk.main()