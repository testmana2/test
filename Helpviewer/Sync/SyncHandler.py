# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module containing a base class for synchronization handlers.
"""

import os

from PyQt4.QtCore import QObject, pyqtSignal, QByteArray

import Preferences

from Utilities.crypto import dataEncrypt, dataDecrypt


class SyncHandler(QObject):
    """
    Base class for synchronization handlers.
    
    @signal syncStatus(type_, done, message) emitted to indicate the synchronization
        status (string one of "bookmarks", "history", "passwords" or "useragents",
        boolean, string)
    @signal syncError(message) emitted for a general error with the error message (string)
    @signal syncMessage(message) emitted to send a message about synchronization (string)
    @signal syncFinished(type_, done, download) emitted after a synchronization has
        finished (string one of "bookmarks", "history", "passwords" or "useragents",
        boolean, boolean)
    """
    syncStatus = pyqtSignal(str, bool, str)
    syncError = pyqtSignal(str)
    syncMessage = pyqtSignal(str)
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
    
    def initialLoadAndCheck(self, forceUpload):
        """
        Public method to do the initial check.
        
        @keyparam forceUpload flag indicating a forced upload of the files (boolean)
        """
        raise NotImplementedError
    
    def shutdown(self):
        """
        Public method to shut down the handler.
        """
        raise NotImplementedError
    
    def readFile(self, fileName):
        """
        Public method to read a file.
        
        If encrypted synchronization is enabled, the data will be encrypted using
        the relevant encryption key.
        
        @param fileName name of the file to be read (string)
        @return data of the file, optionally encrypted (QByteArray)
        """
        if os.path.exists(fileName):
            try:
                inputFile = open(fileName, "rb")
                data = inputFile.read()
                inputFile.close()
            except IOError:
                return QByteArray()
            
            if Preferences.getHelp("SyncEncryptData"):
                key = Preferences.getHelp("SyncEncryptionKey")
                if not key:
                    return QByteArray()
                
                data, ok = dataEncrypt(data, key)
                if not ok:
                    return QByteArray()
            
            return QByteArray(data)
        
        return QByteArray()
    
    def writeFile(self, data, fileName):
        """
        Public method to write the data to a file.
        
        If encrypted synchronization is enabled, the data will be decrypted using
        the relevant encryption key.
        
        @param data data to be written and optionally decrypted (QByteArray)
        @param fileName name of the file the data is to be written to (string)
        @return tuple giving a success flag and an error string (boolean, string)
        """
        data = bytes(data)
        
        if Preferences.getHelp("SyncEncryptData"):
            key = Preferences.getHelp("SyncEncryptionKey")
            if not key:
                return False, self.trUtf8("Invalid encryption key given.")
            
            data, ok = dataDecrypt(data, key)
            if not ok:
                return False, self.trUtf8("Data cannot be decrypted.")
        
        try:
            outputFile = open(fileName, "wb")
            outputFile.write(data)
            outputFile.close()
            return True, ""
        except IOError as error:
            return False, str(error)
