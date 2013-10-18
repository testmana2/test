# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing some common utility functions for the Mercurial package.
"""

import os

from PyQt4.QtCore import QProcessEnvironment

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


def prepareProcess(proc, encoding="", language=""):
    """
    Public method to prepare the given process.
    
    @param proc reference to the proces to be prepared (QProcess)
    @param encoding encoding to be used by the process (string)
    @param language language to be set (string)
    """
    env = QProcessEnvironment.systemEnvironment()
    env.insert("HGPLAIN", '1')
    
    # set the encoding for the process
    if encoding:
        env.insert("HGENCODING", encoding)
    
    # set the language for the process
    if language:
        env.insert("LANGUAGE", language)
    
    proc.setProcessEnvironment(env)
