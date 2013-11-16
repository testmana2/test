# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Plugin Manager configuration page.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

import os

from PyQt4.QtCore import pyqtSlot

from E5Gui.E5Completers import E5DirCompleter
from E5Gui import E5FileDialog

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_PluginManagerPage import Ui_PluginManagerPage

import Preferences
import Utilities


class PluginManagerPage(ConfigurationPageBase, Ui_PluginManagerPage):
    """
    Class implementing the Plugin Manager configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super(PluginManagerPage, self).__init__()
        self.setupUi(self)
        self.setObjectName("PluginManagerPage")
        
        self.downloadDirCompleter = E5DirCompleter(self.downloadDirEdit)
        
        # set initial values
        self.activateExternalPluginsCheckBox.setChecked(
            Preferences.getPluginManager("ActivateExternal"))
        self.downloadDirEdit.setText(
            Preferences.getPluginManager("DownloadPath"))
        
    def save(self):
        """
        Public slot to save the Viewmanager configuration.
        """
        Preferences.setPluginManager(
            "ActivateExternal",
            self.activateExternalPluginsCheckBox.isChecked())
        Preferences.setPluginManager(
            "DownloadPath",
            self.downloadDirEdit.text())
    
    @pyqtSlot()
    def on_downloadDirButton_clicked(self):
        """
        Private slot to handle the directory selection via dialog.
        """
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.trUtf8("Select plugins download directory"),
            self.downloadDirEdit.text(),
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
            
        if directory:
            dn = Utilities.toNativeSeparators(directory)
            while dn.endswith(os.sep):
                dn = dn[:-1]
            self.downloadDirEdit.setText(dn)
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    @return reference to the instantiated page (ConfigurationPageBase)
    """
    page = PluginManagerPage()
    return page
