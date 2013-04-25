# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module defining common data to be used by all modules.
"""

import sys
import os

from PyQt4.QtCore import QDir, QLibraryInfo

# names of the various settings objects
settingsNameOrganization = "Eric5"
settingsNameGlobal = "eric5"
settingsNameRecent = "eric5recent"

# key names of the various recent entries
recentNameMultiProject = "MultiProjects"
recentNameProject = "Projects"
recentNameFiles = "Files"
recentNameHosts = "Hosts6"

configDir = None


def isWindowsPlatform():
    """
    Function to check, if this is a Windows platform.
    
    @return flag indicating Windows platform (boolean)
    """
    return sys.platform.startswith("win")


def isMacPlatform():
    """
    Function to check, if this is a Mac platform.
    
    @return flag indicating Mac platform (boolean)
    """
    return sys.platform == "darwin"


def isLinuxPlatform():
    """
    Function to check, if this is a Linux platform.
    
    @return flag indicating Linux platform (boolean)
    """
    return sys.platform.startswith("linux")


def checkBlacklistedVersions():
    """
    Module functions to check for blacklisted versions of the prerequisites.
    
    @return flag indicating good versions were found (boolean)
    """
    from install import BlackLists, PlatformsBlackLists
    
    # determine the platform dependent black list
    if isWindowsPlatform():
        PlatformBlackLists = PlatformsBlackLists["windows"]
    elif isLinuxPlatform():
        PlatformBlackLists = PlatformsBlackLists["linux"]
    else:
        PlatformBlackLists = PlatformsBlackLists["mac"]
    
    # check version of sip
    try:
        import sipconfig
        sipVersion = sipconfig.Configuration().sip_version_str
        # always assume, that snapshots are good
        if "snapshot" not in sipVersion:
            # check for blacklisted versions
            for vers in BlackLists["sip"] + PlatformBlackLists["sip"]:
                if vers == sipVersion:
                    print('Sorry, sip version {0} is not compatible with eric5.'\
                          .format(vers))
                    print('Please install another version.')
                    return False
    except ImportError:
        pass
    
    # check version of PyQt
    from PyQt4.QtCore import PYQT_VERSION_STR
    pyqtVersion = PYQT_VERSION_STR
    # always assume, that snapshots are good
    if "snapshot" not in pyqtVersion:
        # check for blacklisted versions
        for vers in BlackLists["PyQt4"] + PlatformBlackLists["PyQt4"]:
            if vers == pyqtVersion:
                print('Sorry, PyQt4 version {0} is not compatible with eric5.'\
                      .format(vers))
                print('Please install another version.')
                return False
    
    # check version of QScintilla
    from PyQt4.Qsci import QSCINTILLA_VERSION_STR
    scintillaVersion = QSCINTILLA_VERSION_STR
    # always assume, that snapshots are new enough
    if "snapshot" not in scintillaVersion:
        # check for blacklisted versions
        for vers in BlackLists["QScintilla2"] + PlatformBlackLists["QScintilla2"]:
            if vers == scintillaVersion:
                print('Sorry, QScintilla2 version {0} is not compatible with eric5.'\
                      .format(vers))
                print('Please install another version.')
                return False
    
    return True


def getConfigDir():
    """
    Module function to get the name of the directory storing the config data.
    
    @return directory name of the config dir (string)
    """
    if configDir is not None and os.path.exists(configDir):
        hp = configDir
    else:
        if isWindowsPlatform():
            cdn = "_eric5"
        else:
            cdn = ".eric5"
            
        hp = QDir.homePath()
        dn = QDir(hp)
        dn.mkdir(cdn)
        hp += "/" + cdn
    return QDir.toNativeSeparators(hp)


def setConfigDir(d):
    """
    Module function to set the name of the directory storing the config data.
    
    @param d name of an existing directory (string)
    """
    global configDir
    configDir = os.path.expanduser(d)


def getPythonModulesDirectory():
    """
    Function to determine the path to Python's modules directory.
    
    @return path to the Python modules directory (string)
    """
    import distutils.sysconfig
    return distutils.sysconfig.get_python_lib(True)


def getPyQt4ModulesDirectory():
    """
    Function to determine the path to PyQt4's modules directory.
    
    @return path to the PyQt4 modules directory (string)
    """
    import distutils.sysconfig
    return os.path.join(distutils.sysconfig.get_python_lib(True), "PyQt4")
    

def getQtBinariesPath():
    """
    Module function to get the path of the Qt binaries.
    
    @return path of the Qt binaries (string)
    """
    path = ""
    if isWindowsPlatform():
        # check for PyQt4 installer first (designer is test object)
        modDir = getPyQt4ModulesDirectory()
        if os.path.exists(os.path.join(modDir, "bin", "designer.exe")):
            path = os.path.join(modDir, "bin")
        elif os.path.exists(os.path.join(modDir, "designer.exe")):
            path = modDir
    
    if not path:
        path = QLibraryInfo.location(QLibraryInfo.BinariesPath)
        if not os.path.exists(path):
            path = ""
    
    return QDir.toNativeSeparators(path)


################################################################################
## functions for searching a Python2 interpreter
################################################################################


def findPython2Interpreters():
    """
    Module function for searching a Python2 interpreter.
    
    @return list of interpreters found (list of strings)
    """
    winPathList = ["C:\\Python25", "C:\\Python26", "C:\\Python27", "C:\\Python28"]
    posixPathList = ["/usr/bin", "/usr/local/bin"]
    posixVersionsList = ["2.5", "2.6", "2.7", "2.8"]
    
    interpreters = []
    if isWindowsPlatform():
        # search the interpreters on Windows platforms
        for path in winPathList:
            exeList = [
                "python.exe",
                "python{0}.{1}.exe".format(path[-2], path[-1]),
            ]
            for exe in exeList:
                interpreter = os.path.join(path, exe)
                if os.path.isfile(interpreter):
                    interpreters.append(interpreter)
    else:
        # search interpreters on Posix and Mac platforms
        for path in posixPathList:
            for version in posixVersionsList:
                interpreter = os.path.join(path, "python{0}".format(version))
                if os.path.isfile(interpreter):
                    interpreters.append(interpreter)
    
    return interpreters
