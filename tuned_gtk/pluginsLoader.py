'''
Created on Apr 12, 2014

@author: mstana
'''

import tuned.consts as const
from tuned import plugins 


class PluginLoader(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        _path = plugins.__path__ 
        plugins.Repository()
        self._set_loader_parameters()
                           
                           
    @property
    def plugins(self):
        return self._plugins

    def _set_loader_parameters(self):
        self._namespace = "tuned.plugins"
        self._prefix = "plugin_"
    def load_plugins(self):
        
        
        
#     
# if __name__ == "__main__":
#         
#     for path in  plugins.__path__:
#         print path