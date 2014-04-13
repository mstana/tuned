

import os
import sys
from configobj import ConfigObj

from tuned.exceptions import TunedException
from tuned import storage, units, monitors, plugins, profiles, exports, hardware

class Manager(object):
    
    def __init__(self):
        storage_provider = storage.PickleProvider()
        storage_factory = storage.Factory(storage_provider)

        monitors_repository = monitors.Repository()
        hardware_inventory = hardware.Inventory()
        device_matcher = hardware.DeviceMatcher()
        plugin_instance_factory = plugins.instance.Factory()




        plugins_repository = plugins.Repository(monitors_repository, storage_factory, hardware_inventory, device_matcher, plugin_instance_factory, self.config)
        unit_manager = units.Manager(plugins_repository, monitors_repository)
    
    

    
if __name__ == '__main__':
        
    if os.geteuid() != 0:
        os.error("Superuser permissions are required to run the daemon.")
        sys.exit(1)
  
    man = Manager()