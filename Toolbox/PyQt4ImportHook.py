# -*- coding: utf-8 -*-

# Copyright (c) 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

try:
    import PyQt5    # __IGNORE_WARNING__ 
except ImportError:
    import sys

    # TODO: adapt this for Python2
    class PyQt4Importer(object):
        def __init__(self):
            """
            Constructor
            """
            self.__path = None
        
        def find_module(self, fullname, path=None):
            """
            Public method returning the module loader.
            
            @param fullname name of the module to be loaded (string)
            @param path path to resolve the module name (string)
            @return module loader object
            """
            if fullname.startswith("PyQt5"):
                self.__path = path
                return self
            
            return None
        
        def load_module(self, fullname):
            """
            Public method to load a module.
            
            @param fullname name of the module to be loaded (string)
            @return reference to the loaded module (module)
            """
            if fullname in ["PyQt5.QtWidgets", "PyQt5.QtPrintSupport"]:
                newname = "PyQt4.QtGui"
            elif fullname in ["PyQt5.QtWebKitWidgets"]:
                newname = "PyQt4.QtWebKit"
            else:
                newname = fullname.replace("PyQt5", "PyQt4")
            
            import importlib
            loader = importlib.find_loader(newname, self.__path)
            module = loader.load_module(newname)
            sys.modules[fullname] = module
            if fullname == "PyQt5.QtCore":
                import PyQt4.QtGui
                module.qInstallMessageHandler = module.qInstallMsgHandler
                module.QItemSelectionModel = PyQt4.QtGui.QItemSelectionModel
                module.QItemSelection = PyQt4.QtGui.QItemSelection
                module.QSortFilterProxyModel = \
                    PyQt4.QtGui.QSortFilterProxyModel
                module.QAbstractProxyModel = PyQt4.QtGui.QAbstractProxyModel
                module.QStringListModel = PyQt4.QtGui.QStringListModel
            return module

    sys.meta_path.insert(0, PyQt4Importer())
