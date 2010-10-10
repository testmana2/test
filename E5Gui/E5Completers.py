# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing various kinds of completers.
"""

from PyQt4.QtCore import QDir, Qt
from PyQt4.QtGui import QCompleter, QDirModel, QStringListModel

from Globals import isWindowsPlatform

class E5FileCompleter(QCompleter):
    """
    Class implementing a completer for file names.
    """
    def __init__(self, parent = None, 
                 completionMode = QCompleter.PopupCompletion, 
                 showHidden = False):
        """
        Constructor
        
        @param parent parent widget of the completer (QWidget)
        @keyparam completionMode completion mode of the 
            completer (QCompleter.CompletionMode)
        @keyparam showHidden flag indicating to show hidden entries as well (boolean)
        """
        QCompleter.__init__(self, parent)
        self.__model = QDirModel(self)
        if showHidden:
            self.__model.setFilter(\
                QDir.Filters(QDir.Dirs | QDir.Files | QDir.Drives | \
                             QDir.AllDirs | QDir.Hidden))
        else:
            self.__model.setFilter(\
                QDir.Filters(QDir.Dirs | QDir.Files | QDir.Drives | QDir.AllDirs))
        self.setModel(self.__model)
        self.setCompletionMode(completionMode)
        if isWindowsPlatform():
            self.setCaseSensitivity(Qt.CaseInsensitive)
        if parent:
            parent.setCompleter(self)

class E5DirCompleter(QCompleter):
    """
    Class implementing a completer for directory names.
    """
    def __init__(self, parent = None, 
                 completionMode = QCompleter.PopupCompletion, 
                 showHidden = False):
        """
        Constructor
        
        @param parent parent widget of the completer (QWidget)
        @keyparam completionMode completion mode of the 
            completer (QCompleter.CompletionMode)
        @keyparam showHidden flag indicating to show hidden entries as well (boolean)
        """
        QCompleter.__init__(self, parent)
        self.__model = QDirModel(self)
        if showHidden:
            self.__model.setFilter(\
                QDir.Filters(QDir.Drives | QDir.AllDirs | QDir.Hidden))
        else:
            self.__model.setFilter(\
                QDir.Filters(QDir.Drives | QDir.AllDirs))
        self.setModel(self.__model)
        self.setCompletionMode(completionMode)
        if isWindowsPlatform():
            self.setCaseSensitivity(Qt.CaseInsensitive)
        if parent:
            parent.setCompleter(self)

class E5StringListCompleter(QCompleter):
    """
    Class implementing a completer for string lists.
    """
    def __init__(self, parent = None, strings = [],
                 completionMode = QCompleter.PopupCompletion):
        """
        Constructor
        
        @param parent parent widget of the completer (QWidget)
        @param strings list of string to load into the completer (list of strings)
        @keyparam completionMode completion mode of the 
            completer (QCompleter.CompletionMode)
        """
        QCompleter.__init__(self, parent)
        self.__model = QStringListModel(strings, parent)
        self.setModel(self.__model)
        self.setCompletionMode(completionMode)
        if parent:
            parent.setCompleter(self)
