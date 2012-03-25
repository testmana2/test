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
    
    @signal syncStatus(type_, message) emitted to indicate the synchronization
        status (string one of "bookmarks", "history", "passwords", "useragents" or
        "speeddial", string)
    @signal syncError(message) emitted for a general error with the error message (string)
    @signal syncMessage(message) emitted to send a message about synchronization (string)
    @signal syncFinished(type_, done, download) emitted after a synchronization has
        finished (string one of "bookmarks", "history", "passwords", "useragents" or
        "speeddial", boolean, boolean)
    """
    syncStatus = pyqtSignal(str, str)
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
        
        self._remoteFiles = {
            "bookmarks": "Bookmarks",
            "history": "History",
            "passwords": "Logins",
            "useragents": "UserAgentSettings",
            "speeddial": "SpeedDial",
        }
        
        self._messages = {
            "bookmarks": {
                "RemoteExists": self.trUtf8(
                    "Remote bookmarks file exists! Syncing local copy..."),
                "RemoteMissing": self.trUtf8(
                    "Remote bookmarks file does NOT exists. Exporting local copy..."),
                "LocalNewer": self.trUtf8(
                    "Local bookmarks file is NEWER. Exporting local copy..."),
                "LocalMissing": self.trUtf8(
                    "Local bookmarks file does NOT exist. Skipping synchronization!"),
                "Uploading": self.trUtf8("Uploading local bookmarks file..."),
            },
            "history": {
                "RemoteExists": self.trUtf8(
                    "Remote history file exists! Syncing local copy..."),
                "RemoteMissing": self.trUtf8(
                    "Remote history file does NOT exists. Exporting local copy..."),
                "LocalNewer": self.trUtf8(
                    "Local history file is NEWER. Exporting local copy..."),
                "LocalMissing": self.trUtf8(
                    "Local history file does NOT exist. Skipping synchronization!"),
                "Uploading": self.trUtf8("Uploading local history file..."),
            },
            "passwords": {
                "RemoteExists": self.trUtf8(
                    "Remote logins file exists! Syncing local copy..."),
                "RemoteMissing": self.trUtf8(
                    "Remote logins file does NOT exists. Exporting local copy..."),
                "LocalNewer": self.trUtf8(
                    "Local logins file is NEWER. Exporting local copy..."),
                "LocalMissing": self.trUtf8(
                    "Local logins file does NOT exist. Skipping synchronization!"),
                "Uploading": self.trUtf8("Uploading local logins file..."),
            },
            "useragents": {
                "RemoteExists": self.trUtf8(
                    "Remote user agent settings file exists! Syncing local copy..."),
                "RemoteMissing": self.trUtf8(
                    "Remote user agent settings file does NOT exists."
                    " Exporting local copy..."),
                "LocalNewer": self.trUtf8(
                    "Local user agent settings file is NEWER. Exporting local copy..."),
                "LocalMissing": self.trUtf8(
                    "Local user agent settings file does NOT exist."
                    " Skipping synchronization!"),
                "Uploading": self.trUtf8("Uploading local user agent settings file..."),
            },
            "speeddial": {
                "RemoteExists": self.trUtf8(
                    "Remote speed dial settings file exists! Syncing local copy..."),
                "RemoteMissing": self.trUtf8(
                    "Remote speed dial settings file does NOT exists."
                    " Exporting local copy..."),
                "LocalNewer": self.trUtf8(
                    "Local speed dial settings file is NEWER. Exporting local copy..."),
                "LocalMissing": self.trUtf8(
                    "Local speed dial settings file does NOT exist."
                    " Skipping synchronization!"),
                "Uploading": self.trUtf8("Uploading local speed dial settings file..."),
            },
        }
    
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
    
    def syncSpeedDial(self):
        """
        Public method to synchronize the speed dial data.
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
    
    def readFile(self, fileName, type_):
        """
        Public method to read a file.
        
        If encrypted synchronization is enabled, the data will be encrypted using
        the relevant encryption key.
        
        @param fileName name of the file to be read (string)
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords", "useragents" or "speeddial")
        @return data of the file, optionally encrypted (QByteArray)
        """
        if os.path.exists(fileName):
            try:
                inputFile = open(fileName, "rb")
                data = inputFile.read()
                inputFile.close()
            except IOError:
                return QByteArray()
            
            if Preferences.getHelp("SyncEncryptData") and \
               (not Preferences.getHelp("SyncEncryptPasswordsOnly") or \
                (Preferences.getHelp("SyncEncryptPasswordsOnly") and \
                 type_ == "passwords")):
                key = Preferences.getHelp("SyncEncryptionKey")
                if not key:
                    return QByteArray()
                
                data, ok = dataEncrypt(data, key,
                    keyLength=Preferences.getHelp("SyncEncryptionKeyLength"),
                    hashIterations=100)
                if not ok:
                    return QByteArray()
            
            return QByteArray(data)
        
        return QByteArray()
    
    def writeFile(self, data, fileName, type_, timestamp=0):
        """
        Public method to write the data to a file.
        
        If encrypted synchronization is enabled, the data will be decrypted using
        the relevant encryption key.
        
        @param data data to be written and optionally decrypted (QByteArray)
        @param fileName name of the file the data is to be written to (string)
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords", "useragents" or "speeddial")
        @param timestamp timestamp to be given to the file (int)
        @return tuple giving a success flag and an error string (boolean, string)
        """
        data = bytes(data)
        
        if Preferences.getHelp("SyncEncryptData") and \
           (not Preferences.getHelp("SyncEncryptPasswordsOnly") or \
            (Preferences.getHelp("SyncEncryptPasswordsOnly") and type_ == "passwords")):
            key = Preferences.getHelp("SyncEncryptionKey")
            if not key:
                return False, self.trUtf8("Invalid encryption key given.")
            
            data, ok = dataDecrypt(data, key,
                keyLength=Preferences.getHelp("SyncEncryptionKeyLength"))
            if not ok:
                return False, self.trUtf8("Data cannot be decrypted.")
        
        try:
            outputFile = open(fileName, "wb")
            outputFile.write(data)
            outputFile.close()
            if timestamp > 0:
                os.utime(fileName, (timestamp, timestamp))
            return True, ""
        except IOError as error:
            return False, str(error)
