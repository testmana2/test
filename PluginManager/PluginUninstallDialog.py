# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog for plugin deinstallation.
"""

import sys
import os
import imp
import shutil

from PyQt4.QtCore import pyqtSlot, pyqtSignal
from PyQt4.QtGui import QWidget, QDialog, QDialogButtonBox, QVBoxLayout

from E5Gui import E5MessageBox
from E5Gui.E5MainWindow import E5MainWindow
from E5Gui.E5Application import e5App

from .Ui_PluginUninstallDialog import Ui_PluginUninstallDialog

import Preferences
import UI.PixmapCache


class PluginUninstallWidget(QWidget, Ui_PluginUninstallDialog):
    """
    Class implementing a dialog for plugin deinstallation.
    """
    accepted = pyqtSignal()
    
    def __init__(self, pluginManager, parent=None):
        """
        Constructor
        
        @param pluginManager reference to the plugin manager object
        @param parent parent of this dialog (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        if pluginManager is None:
            # started as external plugin deinstaller
            from .PluginManager import PluginManager
            self.__pluginManager = PluginManager(doLoadPlugins=False)
            self.__external = True
        else:
            self.__pluginManager = pluginManager
            self.__external = False
        
        self.pluginDirectoryCombo.addItem(self.trUtf8("User plugins directory"),
            self.__pluginManager.getPluginDir("user"))
        
        globalDir = self.__pluginManager.getPluginDir("global")
        if globalDir is not None and os.access(globalDir, os.W_OK):
            self.pluginDirectoryCombo.addItem(self.trUtf8("Global plugins directory"),
                globalDir)
    
    @pyqtSlot(int)
    def on_pluginDirectoryCombo_currentIndexChanged(self, index):
        """
        Private slot to populate the plugin name combo upon a change of the
        plugin area.
        
        @param index index of the selected item (integer)
        """
        pluginDirectory = self.pluginDirectoryCombo\
                .itemData(index)
        pluginNames = sorted(self.__pluginManager.getPluginModules(pluginDirectory))
        self.pluginNameCombo.clear()
        for pluginName in pluginNames:
            fname = "{0}.py".format(os.path.join(pluginDirectory, pluginName))
            self.pluginNameCombo.addItem(pluginName, fname)
        self.buttonBox.button(QDialogButtonBox.Ok)\
            .setEnabled(self.pluginNameCombo.currentText() != "")
    
    @pyqtSlot()
    def on_buttonBox_accepted(self):
        """
        Private slot to handle the accepted signal of the button box.
        """
        if self.__uninstallPlugin():
            self.accepted.emit()
    
    def __uninstallPlugin(self):
        """
        Private slot to uninstall the selected plugin.
        
        @return flag indicating success (boolean)
        """
        pluginDirectory = self.pluginDirectoryCombo\
                .itemData(self.pluginDirectoryCombo.currentIndex())
        pluginName = self.pluginNameCombo.currentText()
        pluginFile = self.pluginNameCombo\
                .itemData(self.pluginNameCombo.currentIndex())
        
        if not self.__pluginManager.unloadPlugin(pluginName, pluginDirectory):
            E5MessageBox.critical(self,
                self.trUtf8("Plugin Uninstallation"),
                self.trUtf8("""<p>The plugin <b>{0}</b> could not be unloaded."""
                            """ Aborting...</p>""").format(pluginName))
            return False
        
        if not pluginDirectory in sys.path:
            sys.path.insert(2, pluginDirectory)
        module = imp.load_source(pluginName, pluginFile)
        if not hasattr(module, "packageName"):
            E5MessageBox.critical(self,
                self.trUtf8("Plugin Uninstallation"),
                self.trUtf8("""<p>The plugin <b>{0}</b> has no 'packageName' attribute."""
                            """ Aborting...</p>""").format(pluginName))
            return False
        
        package = getattr(module, "packageName")
        if package is None:
            package = "None"
            packageDir = ""
        else:
            packageDir = os.path.join(pluginDirectory, package)
        if hasattr(module, "prepareUninstall"):
            module.prepareUninstall()
        internalPackages = []
        if hasattr(module, "internalPackages"):
            # it is a comma separated string
            internalPackages = [p.strip() for p in module.internalPackages.split(",")]
        del module
        
        # clean sys.modules
        self.__pluginManager.removePluginFromSysModules(
            pluginName, package, internalPackages)
        
        try:
            if packageDir and os.path.exists(packageDir):
                shutil.rmtree(packageDir)
            
            fnameo = "{0}o".format(pluginFile)
            if os.path.exists(fnameo):
                os.remove(fnameo)
            
            fnamec = "{0}c".format(pluginFile)
            if os.path.exists(fnamec):
                os.remove(fnamec)
            
            os.remove(pluginFile)
        except OSError as err:
            E5MessageBox.critical(self,
                self.trUtf8("Plugin Uninstallation"),
                self.trUtf8("""<p>The plugin package <b>{0}</b> could not be"""
                            """ removed. Aborting...</p>"""
                            """<p>Reason: {1}</p>""").format(packageDir, str(err)))
            return False
        
        if not self.__external:
            ui = e5App().getObject("UserInterface")
            if ui.notificationsEnabled():
                ui.showNotification(UI.PixmapCache.getPixmap("plugin48.png"),
                self.trUtf8("Plugin Uninstallation"),
                self.trUtf8("""<p>The plugin <b>{0}</b> was uninstalled successfully"""
                            """ from {1}.</p>""")\
                    .format(pluginName, pluginDirectory))
                return True
        
        E5MessageBox.information(self,
            self.trUtf8("Plugin Uninstallation"),
            self.trUtf8("""<p>The plugin <b>{0}</b> was uninstalled successfully"""
                        """ from {1}.</p>""")\
                .format(pluginName, pluginDirectory))
        return True


class PluginUninstallDialog(QDialog):
    """
    Class for the dialog variant.
    """
    def __init__(self, pluginManager, parent=None):
        """
        Constructor
        
        @param pluginManager reference to the plugin manager object
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setSizeGripEnabled(True)
        
        self.__layout = QVBoxLayout(self)
        self.__layout.setMargin(0)
        self.setLayout(self.__layout)
        
        self.cw = PluginUninstallWidget(pluginManager, self)
        size = self.cw.size()
        self.__layout.addWidget(self.cw)
        self.resize(size)
        
        self.cw.buttonBox.accepted[()].connect(self.accept)
        self.cw.buttonBox.rejected[()].connect(self.reject)


class PluginUninstallWindow(E5MainWindow):
    """
    Main window class for the standalone dialog.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.cw = PluginUninstallWidget(None, self)
        size = self.cw.size()
        self.setCentralWidget(self.cw)
        self.resize(size)
        
        self.setStyle(Preferences.getUI("Style"), Preferences.getUI("StyleSheet"))
        
        self.cw.buttonBox.accepted[()].connect(self.close)
        self.cw.buttonBox.rejected[()].connect(self.close)
