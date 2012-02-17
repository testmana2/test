# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module containing a base class for synchronization handlers.
"""

from PyQt4.QtCore import QObject, pyqtSignal


class SyncHandler(QObject):
    """
    Base class for synchronization handlers.
    
    @signal syncStatus(type_, done, message) emitted to indicate the synchronization
        status (string one of "bookmarks", "history", "passwords" or "useragents",
        boolean, string)
    @signal syncError(message) emitted for a general error with the error message (string)
    @signal syncFinished(type_, done, download) emitted after a synchronization has
        finished (string one of "bookmarks", "history", "passwords" or "useragents",
        boolean, boolean)
    """
    syncStatus = pyqtSignal(str, bool, str)
    syncError = pyqtSignal(str)
    syncFinished = pyqtSignal(str, bool, bool)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self._firstTimeSynced = False
    
    def syncBookmarks(self):
        """
        Public method to synchronize the bookmarks.
        """
        raise NotImplementedError
    
    def syncHistory(self):
        """
        Public method to synchronize the history.
        """
        raise NotImplementedError
    
    def syncPasswords(self):
        """
        Public method to synchronize the passwords.
        """
        raise NotImplementedError
    
    def syncUserAgents(self):
        """
        Public method to synchronize the user agents.
        """
        raise NotImplementedError
    
    def initialLoadAndCheck(self):
        """
        Public method to do the initial check.
        """
        raise NotImplementedError
    
    def shutdown(self):
        """
        Public method to shut down the handler.
        """
        raise NotImplementedError
