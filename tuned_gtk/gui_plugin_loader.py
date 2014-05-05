#!/usr/bin/env python
'''
Created on Mar 30, 2014

@author: mstana
'''

import os
from validate import Validator

import tuned.plugins.base
import tuned.consts as consts
import tuned.logs
import tuned.plugins.repository as repository
import configobj as ConfigObj
import tuned.exceptions as TunedException

from tuned import plugins 
from tuned.utils.plugin_loader import PluginLoader
from tuned import storage, units, monitors, plugins, profiles, exports, hardware


import tuned.plugins as Plugins

__all__ = ["GTKPluginLoader"]

global_config_spec = ["dynamic_tuning = boolean(default=%s)" % consts.CFG_DEF_DYNAMIC_TUNING,
            "sleep_interval = integer(default=%s)" % consts.CFG_DEF_SLEEP_INTERVAL,
            "update_interval = integer(default=%s)" % consts.CFG_DEF_UPDATE_INTERVAL]

class GuiPluginLoader(PluginLoader):
    '''
    Class for scan, import and load actual avaible plugins.
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self._plugins = set()
        self.plugins_doc = {}

        storage_provider = storage.PickleProvider()
        storage_factory = storage.Factory(storage_provider)
        monitors_repository = monitors.Repository()
        hardware_inventory = hardware.Inventory()
        device_matcher = hardware.DeviceMatcher()
        plugin_instance_factory = plugins.instance.Factory()

        self.repo = repository.Repository(monitors_repository, storage_factory, hardware_inventory, device_matcher, plugin_instance_factory, self._set_loader_parameters())
        self.create_all(self._import_plugin_names())

    @property
    def plugins(self):
        return self.repo.plugins

    def _set_loader_parameters(self):
        '''
        Sets private atributes.
        '''
        self._namespace = "tuned.plugins"
        self._prefix = "plugin_"
        self._sufix = ".py"
        self._interface = tuned.plugins.base.Plugin

    def _import_plugin_names(self): 
        '''
        Scan directories and find names to load
        '''
        names = []
        for name in os.listdir(Plugins.__path__[0]):
            file = name.split(self._prefix).pop()
            if  file.endswith(self._sufix):
                file_name, file_extension = os.path.splitext(file)
                names.append(file_name)
        return names

    def create_all(self, names):
        for plugin_name in names:
            try:
                self._plugins.add(self.repo.create(plugin_name))
            except ImportError:
                print str(ImportError) + plugin_name
            except tuned.plugins.exceptions.NotSupportedPluginException:
                print plugin_name + " is not supported!"


    def get_plugin(self, plugin_name):
        for plugin in self.plugins:
            if plugin_name == plugin.name:
                return plugin

    def _load_global_config(self, file_name = consts.GLOBAL_CONFIG_FILE):
        """
        Loads global configuration file.
        """
        try:
            config = ConfigObj(file_name, configspec=global_config_spec, raise_errors = True, file_error = True)
        except IOError as e:
            raise TunedException("Global tuned configuration file '%s' not found." % file_name)
        except ConfigObj.ConfigObjError as e:
            raise TunedException("Error parsing global tuned configuration file '%s'." % file_name)
        vdt = Validator()
        if (not config.validate(vdt, copy=True)):
            raise TunedException("Global tuned configuration file '%s' is not valid." % file_name)
        return config    