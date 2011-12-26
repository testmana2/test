# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing some common utility functions for the Mercurial package.
"""

import os

import Utilities

def getConfigPath():
    """
    Public method to get the filename of the config file.
    
    @return filename of the config file (string)
    """
    if Utilities.isWindowsPlatform():
        userprofile = os.environ["USERPROFILE"]
        return os.path.join(userprofile, "Mercurial.ini")
    else:
        homedir = Utilities.getHomeDir()
        return os.path.join(homedir, ".hgrc")
