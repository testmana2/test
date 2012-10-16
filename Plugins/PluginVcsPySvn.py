# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the PySvn version control plugin.
"""

import os

from PyQt4.QtCore import QObject
from PyQt4.QtGui import QApplication

from E5Gui.E5Application import e5App

import Preferences
from Preferences.Shortcuts import readShortcuts

from VcsPlugins.vcsPySvn.SvnUtilities import getConfigPath, getServersPath

# Start-Of-Header
name = "PySvn Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = False
deactivateable = True
version = "5.1.0"
pluginType = "version_control"
pluginTypename = "PySvn"
className = "VcsPySvnPlugin"
packageName = "__core__"
shortDescription = "Implements the PySvn version control interface."
longDescription = """This plugin provides the PySvn version control interface."""
pyqtApi = 2
# End-Of-Header

error = ""


def exeDisplayData():
    """
    Public method to support the display of some executable info.
    
    @return dictionary containing the data to be shown
    """
    try:
        import pysvn
        try:
            text = os.path.dirname(pysvn.__file__)
        except AttributeError:
            text = "PySvn"
        version = ".".join([str(v) for v in pysvn.version])
    except ImportError:
        text = "PySvn"
        version = ""
    
    data = {
        "programEntry": False,
        "header": QApplication.translate("VcsPySvnPlugin",
                            "Version Control - Subversion (pysvn)"),
        "text": text,
        "version": version,
    }
    
    return data


def getVcsSystemIndicator():
    """
    Public function to get the indicators for this version control system.
    
    @return dictionary with indicator as key and a tuple with the vcs name (string)
        and vcs display string (string)
    """
    global pluginTypename
    data = {}
    try:
        import pysvn        # __IGNORE_WARNING__
        data[".svn"] = (pluginTypename, displayString())
        data["_svn"] = (pluginTypename, displayString())
    except ImportError:
        pass
    return data


def displayString():
    """
    Public function to get the display string.
    
    @return display string (string)
    """
    try:
        import pysvn        # __IGNORE_WARNING__
        return QApplication.translate('VcsPySvnPlugin', 'Subversion (pysvn)')
    except ImportError:
        return ""

subversionCfgPluginObject = None


def createConfigurationPage(configDlg):
    """
    Module function to create the configuration page.
    
    @return reference to the configuration page
    """
    global subversionCfgPluginObject
    from VcsPlugins.vcsPySvn.ConfigurationPage.SubversionPage import SubversionPage
    if subversionCfgPluginObject is None:
        subversionCfgPluginObject = VcsPySvnPlugin(None)
    page = SubversionPage(subversionCfgPluginObject)
    return page
    

def getConfigData():
    """
    Module function returning data as required by the configuration dialog.
    
    @return dictionary with key "zzz_subversionPage" containing the relevant data
    """
    return {
        "zzz_subversionPage": \
            [QApplication.translate("VcsPySvnPlugin", "Subversion"),
             os.path.join("VcsPlugins", "vcsPySvn", "icons",
                          "preferences-subversion.png"),
             createConfigurationPage, "vcsPage", None],
    }


def prepareUninstall():
    """
    Module function to prepare for an uninstallation.
    """
    if not e5App().getObject("PluginManager").isPluginLoaded("PluginVcsSubversion"):
        Preferences.Prefs.settings.remove("Subversion")
    

class VcsPySvnPlugin(QObject):
    """
    Class implementing the PySvn version control plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super().__init__(ui)
        self.__ui = ui
        
        self.__subversionDefaults = {
            "StopLogOnCopy": 1,
            "LogLimit": 100,
            "CommitMessages": 20,
        }
        
        from VcsPlugins.vcsPySvn.ProjectHelper import SvnProjectHelper
        self.__projectHelperObject = SvnProjectHelper(None, None)
        try:
            e5App().registerPluginObject(pluginTypename, self.__projectHelperObject,
                                         pluginType)
        except KeyError:
            pass    # ignore duplicate registration
        readShortcuts(pluginName=pluginTypename)
    
    def getProjectHelper(self):
        """
        Public method to get a reference to the project helper object.
        
        @return reference to the project helper object
        """
        return self.__projectHelperObject

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of reference to instantiated viewmanager and
            activation status (boolean)
        """
        from VcsPlugins.vcsPySvn.subversion import Subversion
        self.__object = Subversion(self, self.__ui)
        return self.__object, True
    
    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        self.__object = None
    
    def getPreferences(self, key):
        """
        Public method to retrieve the various settings.
        
        @param key the key of the value to get
        @param prefClass preferences class used as the storage area
        @return the requested refactoring setting
        """
        if key in ["StopLogOnCopy"]:
            return Preferences.toBool(Preferences.Prefs.settings.value(
                "Subversion/" + key, self.__subversionDefaults[key]))
        elif key in ["LogLimit", "CommitMessages"]:
            return int(Preferences.Prefs.settings.value("Subversion/" + key,
                self.__subversionDefaults[key]))
        elif key in ["Commits"]:
            return Preferences.toList(Preferences.Prefs.settings.value(
                "Subversion/" + key))
        else:
            return Preferences.Prefs.settings.value("Subversion/" + key)
    
    def setPreferences(self, key, value):
        """
        Public method to store the various settings.
        
        @param key the key of the setting to be set
        @param value the value to be set
        @param prefClass preferences class used as the storage area
        """
        Preferences.Prefs.settings.setValue("Subversion/" + key, value)
    
    def getServersPath(self):
        """
        Public method to get the filename of the servers file.
        
        @return filename of the servers file (string)
        """
        return getServersPath()
    
    def getConfigPath(self):
        """
        Public method to get the filename of the config file.
        
        @return filename of the config file (string)
        """
        return getConfigPath()
    
    def prepareUninstall(self):
        """
        Public method to prepare for an uninstallation.
        """
        e5App().unregisterPluginObject(pluginTypename)
