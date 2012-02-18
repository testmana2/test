# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the synchronization manager class.
"""

from PyQt4.QtCore import QObject, pyqtSignal

from .FtpSyncHandler import FtpSyncHandler
from .SyncAssistantDialog import SyncAssistantDialog

import Preferences

import Helpviewer.HelpWindow


class SyncManager(QObject):
    """
    Class implementing the synchronization manager.
    
    @signal syncError(message) emitted for a general error with the error message (string)
    """
    syncError = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__handler = None
        
        self.loadSettings()
    
    def handler(self):
        """
        Public method to get a reference to the sync handler object.
        
        @return reference to the sync handler object (SyncHandler)
        """
        return self.__handler
    
    def showSyncDialog(self):
        """
        Public method to show the synchronization dialog.
        """
        dlg = SyncAssistantDialog()
        dlg.exec_()
    
    def loadSettings(self):
        """
        Public method to load the settings.
        """
        if self.syncEnabled():
            if Preferences.getHelp("SyncType") == 0:
                if self.__handler is not None:
                    self.__handler.syncError.disconnect(self.__syncError)
                    self.__handler.syncFinished.disconnect(self.__syncFinished)
                    self.__handler.shutdown()
                self.__handler = FtpSyncHandler(self)
                self.__handler.syncError.connect(self.__syncError)
                self.__handler.syncFinished.connect(self.__syncFinished)
            
            self.__handler.initialLoadAndCheck()
            
            # connect sync manager to bookmarks manager
            if Preferences.getHelp("SyncBookmarks"):
                Helpviewer.HelpWindow.HelpWindow.bookmarksManager().bookmarksSaved\
                    .connect(self.__syncBookmarks)
            else:
                try:
                    Helpviewer.HelpWindow.HelpWindow.bookmarksManager().bookmarksSaved\
                        .disconnect(self.__syncBookmarks)
                except TypeError:
                    pass
            
            # connect sync manager to history manager
            if Preferences.getHelp("SyncHistory"):
                Helpviewer.HelpWindow.HelpWindow.historyManager().historySaved\
                    .connect(self.__syncHistory)
            else:
                try:
                    Helpviewer.HelpWindow.HelpWindow.historyManager().historySaved\
                        .disconnect(self.__syncHistory)
                except TypeError:
                    pass
            
            # connect sync manager to passwords manager
            if Preferences.getHelp("SyncPasswords"):
                Helpviewer.HelpWindow.HelpWindow.passwordManager().passwordsSaved\
                    .connect(self.__syncPasswords)
            else:
                try:
                    Helpviewer.HelpWindow.HelpWindow.passwordManager().passwordsSaved\
                        .disconnect(self.__syncPasswords)
                except TypeError:
                    pass
            
            # connect sync manager to user agent manager
            if Preferences.getHelp("SyncUserAgents"):
                Helpviewer.HelpWindow.HelpWindow.userAgentsManager()\
                    .userAgentSettingsSaved.connect(self.__syncUserAgents)
            else:
                try:
                    Helpviewer.HelpWindow.HelpWindow.userAgentsManager()\
                        .userAgentSettingsSaved.disconnect(self.__syncUserAgents)
                except TypeError:
                    pass
        else:
            if self.__handler is not None:
                self.__handler.syncError.disconnect(self.__syncError)
                self.__handler.syncFinished.disconnect(self.__syncFinished)
                self.__handler.shutdown()
            self.__handler = None
            
            try:
                Helpviewer.HelpWindow.HelpWindow.bookmarksManager().bookmarksSaved\
                    .disconnect(self.__syncBookmarks)
            except TypeError:
                pass
            try:
                Helpviewer.HelpWindow.HelpWindow.historyManager().historySaved\
                    .disconnect(self.__syncHistory)
            except TypeError:
                pass
            try:
                Helpviewer.HelpWindow.HelpWindow.passwordManager().passwordsSaved\
                    .disconnect(self.__syncPasswords)
            except TypeError:
                pass
            try:
                Helpviewer.HelpWindow.HelpWindow.userAgentsManager()\
                    .userAgentSettingsSaved.disconnect(self.__syncUserAgents)
            except TypeError:
                pass
    
    def syncEnabled(self):
        """
        Public method to check, if synchronization is enabled.
        
        @return flag indicating enabled synchronization
        """
        return Preferences.getHelp("SyncEnabled") and \
               Preferences.getHelp("SyncType") > -1
    
    def __syncBookmarks(self):
        """
        Private slot to synchronize the bookmarks.
        """
        if self.__handler is not None:
            self.__handler.syncBookmarks()
    
    def __syncHistory(self):
        """
        Private slot to synchronize the history.
        """
        if self.__handler is not None:
            self.__handler.syncHistory()
    
    def __syncPasswords(self):
        """
        Private slot to synchronize the passwords.
        """
        if self.__handler is not None:
            self.__handler.syncPasswords()
    
    def __syncUserAgents(self):
        """
        Private slot to synchronize the user agent settings.
        """
        if self.__handler is not None:
            self.__handler.syncUserAgents()
    
    def __syncError(self, message):
        """
        Private slot to handle general synchronization issues.
        
        @param message error message (string)
        """
        self.syncError.emit(message)
    
    def __syncFinished(self, type_, status, download):
        """
        Private slot to handle a finished synchronization event.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords" or "useragents")
        @param status flag indicating success (boolean)
        @param download flag indicating a download of a file (boolean)
        """
        if status and download:
            if type_ == "bookmarks":
                Helpviewer.HelpWindow.HelpWindow.bookmarksManager().reload()
            elif type_ == "history":
                Helpviewer.HelpWindow.HelpWindow.historyManager().reload()
            elif type_ == "passwords":
                Helpviewer.HelpWindow.HelpWindow.passwordManager().reload()
            elif type_ == "useragents":
                Helpviewer.HelpWindow.HelpWindow.userAgentsManager().reload()
    
    def close(self):
        """
        Public slot to shut down the synchronization manager.
        """
        if not self.syncEnabled():
            return
        
        if self.__handler is not None:
            self.__handler.shutdown()
