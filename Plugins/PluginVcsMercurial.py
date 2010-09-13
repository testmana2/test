# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Mercurial version control plugin.
"""

import os

from PyQt4.QtCore import QObject
from PyQt4.QtGui import QApplication

from E5Gui.E5Application import e5App

import Preferences
from Preferences.Shortcuts import readShortcuts

from VcsPlugins.vcsMercurial.HgUtilities import getConfigPath

import Utilities

# Start-Of-Header
name = "Mercurial Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = False
deactivateable = True
version = "5.1.0"
pluginType = "version_control"
pluginTypename = "Mercurial"
className = "VcsMercurialPlugin"
packageName = "__core__"
shortDescription = "Implements the Mercurial version control interface."
longDescription = """This plugin provides the Mercurial version control interface."""
pyqtApi = 2
# End-Of-Header

error = ""

def exeDisplayData():
    """
    Public method to support the display of some executable info.
    
    @return dictionary containing the data to query the presence of
        the executable
    """
    exe = 'hg'
    if Utilities.isWindowsPlatform():
        exe += '.exe'
    
    data = {
        "programEntry"      : True, 
        "header"            : QApplication.translate("VcsMercurialPlugin",
                                "Version Control - Mercurial"), 
        "exe"               : exe, 
        "versionCommand"    : 'version', 
        "versionStartsWith" : 'Mercurial', 
        "versionPosition"   : -1, 
        "version"           : "", 
        "versionCleanup"    : (0, -1), 
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
    exe = 'hg'
    if Utilities.isWindowsPlatform():
        exe += '.exe'
    if Utilities.isinpath(exe):
        data[".hg"] = (pluginTypename, displayString())
        data["_hg"] = (pluginTypename, displayString())
    return data

def displayString():
    """
    Public function to get the display string.
    
    @return display string (string)
    """
    exe = 'hg'
    if Utilities.isWindowsPlatform():
        exe += '.exe'
    if Utilities.isinpath(exe):
        return QApplication.translate('VcsMercurialPlugin', 'Mercurial')
    else:
        return ""

mercurialCfgPluginObject = None

def createConfigurationPage(configDlg):
    """
    Module function to create the configuration page.
    
    @return reference to the configuration page
    """
    global mercurialCfgPluginObject
    from VcsPlugins.vcsMercurial.ConfigurationPage.MercurialPage import MercurialPage
    if mercurialCfgPluginObject is None:
        mercurialCfgPluginObject = VcsMercurialPlugin(None)
    page = MercurialPage(mercurialCfgPluginObject)
    return page
    
def getConfigData():
    """
    Module function returning data as required by the configuration dialog.
    
    @return dictionary with key "zzz_mercurialPage" containing the relevant data
    """
    return {
        "zzz_mercurialPage" : \
            [QApplication.translate("VcsMercurialPlugin", "Mercurial"), 
             os.path.join("VcsPlugins", "vcsMercurial", "icons", 
                          "preferences-mercurial.png"),
             createConfigurationPage, "vcsPage", None],
    }

def prepareUninstall():
    """
    Module function to prepare for an uninstallation.
    """
    if not e5App().getObject("PluginManager").isPluginLoaded("PluginVcsMercurial"):
        Preferences.Prefs.settings.remove("Mercurial")
    
class VcsMercurialPlugin(QObject):
    """
    Class implementing the Mercurial version control plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        self.__ui = ui
        
        self.__mercurialDefaults = {
            "StopLogOnCopy"  : True, # used in log browser
            "UseLogBrowser"  : True, 
            "LogLimit"       : 100, 
            "CommitMessages" : 20, 
            "PullUpdate"     : False,
            "ServerPort"     : 8000, 
            "ServerStyle"    : "", 
        }
        
        from VcsPlugins.vcsMercurial.ProjectHelper import HgProjectHelper
        self.__projectHelperObject = HgProjectHelper(None, None)
        try:
            e5App().registerPluginObject(pluginTypename, self.__projectHelperObject, 
                                         pluginType)
        except KeyError:
            pass    # ignore duplicate registration
        readShortcuts(pluginName = pluginTypename)
    
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
        from VcsPlugins.vcsMercurial.hg import Hg
        self.__object = Hg(self, self.__ui)
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
        @return the requested setting
        """
        if key in ["StopLogOnCopy", "UseLogBrowser", "PullUpdate"]:
            return Preferences.toBool(Preferences.Prefs.settings.value(
                "Mercurial/" + key, self.__mercurialDefaults[key]))
        elif key in ["LogLimit", "CommitMessages", "ServerPort"]:
            return int(Preferences.Prefs.settings.value("Mercurial/" + key,
                self.__mercurialDefaults[key]))
        elif key in ["Commits"]:
            return Preferences.toList(Preferences.Prefs.settings.value(
                "Mercurial/" + key))
        else: 
            return Preferences.Prefs.settings.value("Mercurial/" + key)
    
    def setPreferences(self, key, value):
        """
        Public method to store the various settings.
        
        @param key the key of the setting to be set
        @param value the value to be set
        """
        Preferences.Prefs.settings.setValue("Mercurial/" + key, value)
    
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
