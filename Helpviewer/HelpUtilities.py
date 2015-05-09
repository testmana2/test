# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing some global helper functions.
"""

from __future__ import unicode_literals

import os

from PyQt5.QtCore import QUrl


def getFileNameFromUrl(url):
    """
    Module function to generate a file name based on the given URL.
    
    @param url URL (QUrl)
    @return file name (string)
    """
    fileName = url.toString(QUrl.RemoveFragment | QUrl.RemoveQuery |
                            QUrl.RemoveScheme | QUrl.RemovePort)
    if fileName.find("/") != -1:
        pos = fileName.rfind("/")
        fileName = fileName[pos:]
        fileName = fileName.replace("/", "")
    
    fileName = filterCharsFromFilename(fileName)
    
    if not fileName:
        fileName = filterCharsFromFilename(url.host().replace(".", "_"))
    
    return fileName


def filterCharsFromFilename(name):
    """
    Module function to filter illegal characters.
    
    @param name name to be sanitized (string)
    @return sanitized name (string)
    """
    return name\
        .replace("/", "_")\
        .replace("\\", "")\
        .replace(":", "")\
        .replace("*", "")\
        .replace("?", "")\
        .replace('"', "")\
        .replace("<", "")\
        .replace(">", "")\
        .replace("|", "")


def ensureUniqueFilename(name, appendFormat="({0})"):
    """
    Module function to generate an unique file name based on a pattern.
    
    @param name desired file name (string)
    @param appendFormat format pattern to be used to make the unique name
        (string)
    @return unique file name
    """
    if not os.path.exists(name):
        return name
    
    tmpFileName = name
    i = 1
    while os.path.exists(tmpFileName):
        tmpFileName = name
        index = tmpFileName.rfind(".")
        
        appendString = appendFormat.format(i)
        if index == -1:
            tmpFileName += appendString
        else:
            tmpFileName = tmpFileName[:index] + appendString + \
                tmpFileName[index:]
        i += 1
    
    return tmpFileName
