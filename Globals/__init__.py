# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module defining common data to be used by all modules.
"""

import sys
import os

# names of the various settings objects
settingsNameOrganization = "Eric5"
settingsNameGlobal = "eric5"
settingsNameRecent = "eric5recent"

# key names of the various recent entries
recentNameMultiProject = "MultiProjects"
recentNameProject = "Projects"
recentNameFiles = "Files"
recentNameHosts = "Hosts6"


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
