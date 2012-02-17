# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a synchronization handler using FTP.
"""

from PyQt4.QtCore import pyqtSignal, QUrl, QFile, QIODevice, QTime, QThread
from PyQt4.QtNetwork import QFtp, QNetworkProxyQuery, QNetworkProxy, QNetworkProxyFactory

from .SyncHandler import SyncHandler

import Helpviewer.HelpWindow

import Preferences


class FtpSyncHandler(SyncHandler):
    """
    Class implementing a synchronization handler using FTP.
    
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
        
        self.__state = "idle"
        
        self.__remoteFiles = {
            "bookmarks": "Bookmarks",
            "history": "History",
            "passwords": "Logins",
            "useragents": "UserAgentSettings"
        }
        self.__remoteFilesFound = []
        
        self.__messages = {
            "bookmarks": {
                "RemoteExists": self.trUtf8(
                    "Remote bookmarks file exists! Syncing local copy..."),
                "RemoteMissing": self.trUtf8(
                    "Remote bookmarks file does NOT exists. Exporting local copy..."),
                "LocalMissing": self.trUtf8(
                    "Local bookmarks file does NOT exist. Skipping synchronization!"),
            },
            "history": {
                "RemoteExists": self.trUtf8(
                    "Remote history file exists! Syncing local copy..."),
                "RemoteMissing": self.trUtf8(
                    "Remote history file does NOT exists. Exporting local copy..."),
                "LocalMissing": self.trUtf8(
                    "Local history file does NOT exist. Skipping synchronization!"),
            },
            "passwords": {
                "RemoteExists": self.trUtf8(
                    "Remote logins file exists! Syncing local copy..."),
                "RemoteMissing": self.trUtf8(
                    "Remote logins file does NOT exists. Exporting local copy..."),
                "LocalMissing": self.trUtf8(
                    "Local logins file does NOT exist. Skipping synchronization!"),
            },
            "useragents": {
                "RemoteExists": self.trUtf8(
                    "Remote user agent settings file exists! Syncing local copy..."),
                "RemoteMissing": self.trUtf8(
                    "Remote user agent settings file does NOT exists."
                    " Exporting local copy..."),
                "LocalMissing": self.trUtf8(
                    "Local user agent settings file does NOT exist."
                    " Skipping synchronization!"),
            },
        }
    
    def initialLoadAndCheck(self):
        """
        Public method to do the initial check.
        """
        if not Preferences.getHelp("SyncEnabled"):
            return
        
        self.__state = "initializing"
        
        self.__remoteFilesFound = []
        self.__syncIDs = {}
        
        self.__ftp = QFtp(self)
        self.__ftp.commandFinished.connect(self.__commandFinished)
        self.__ftp.listInfo.connect(self.__checkSyncFiles)
        
        # do proxy setup
        url = QUrl("ftp://{0}:{1}".format(
            Preferences.getHelp("SyncFtpServer"),
            Preferences.getHelp("SyncFtpPort")
        ))
        query = QNetworkProxyQuery(url)
        proxyList = QNetworkProxyFactory.proxyForQuery(query)
        ftpProxy = QNetworkProxy()
        for proxy in proxyList:
            if proxy.type() == QNetworkProxy.NoProxy or \
               proxy.type() == QNetworkProxy.FtpCachingProxy:
                ftpProxy = proxy
                break
        if ftpProxy.type() == QNetworkProxy.DefaultProxy:
            self.syncError.emit(self.trUtf8("No suitable proxy found."))
            return
        elif ftpProxy.type() == QNetworkProxy.FtpCachingProxy:
            self.__ftp.setProxy(ftpProxy.hostName(), ftpProxy.port())
        
        self.__ftp.connectToHost(Preferences.getHelp("SyncFtpServer"),
                                 Preferences.getHelp("SyncFtpPort"))
        self.__ftp.login(Preferences.getHelp("SyncFtpUser"),
                         Preferences.getHelp("SyncFtpPassword"))
    
    def __changeToStore(self):
        """
        Private slot to change to the storage directory.
        
        This action might cause the storage path to be created on the server.
        """
        self.__storePathList = \
            Preferences.getHelp("SyncFtpPath").replace("\\", "/").split("/")
        if self.__storePathList[0] == "":
            del self.__storePathList[0]
            self.__ftp.cd(self.__storePathList[0])
    
    def __commandFinished(self, id, error):
        """
        Private slot handling the end of a command.
        
        @param id id of the finished command (integer)
        @param error flag indicating an error situation (boolean)
        """
        if error:
            if self.__ftp.currentCommand() in [
                QFtp.ConnectToHost, QFtp.Login, QFtp.Mkdir, QFtp.List]:
                self.syncError.emit(self.__ftp.errorString())
            elif self.__ftp.currentCommand() == QFtp.Cd:
                self.__ftp.mkdir(self.__storePathList[0])
                self.__ftp.cd(self.__storePathList[0])
            else:
                if id in self.__syncIDs:
                    self.__syncIDs[id][1].close()
                    self.syncStatus.emit(self.__syncIDs[id][0], False,
                        self.__ftp.errorString())
                    self.syncFinished.emit(self.__syncIDs[id][0], False,
                        self.__syncIDs[id][2])
                    del self.__syncIDs[id]
        else:
            if self.__ftp.currentCommand() == QFtp.Login:
                self.__changeToStore()
            elif self.__ftp.currentCommand() == QFtp.Cd:
                del self.__storePathList[0]
                if self.__storePathList:
                    self.__ftp.cd(self.__storePathList[0])
                else:
                    self.__storeReached()
            elif self.__ftp.currentCommand() == QFtp.List:
                self.__initialSync()
            else:
                if id in self.__syncIDs:
                    self.__syncIDs[id][1].close()
                    self.syncFinished.emit(self.__syncIDs[id][0], True,
                        self.__syncIDs[id][2])
                    del self.__syncIDs[id]
    
    def __storeReached(self):
        """
        Private slot executed, when the storage directory was reached.
        """
        self.__ftp.list()
    
    def __checkSyncFiles(self, info):
        """
        Private slot called for each entry sent by the FTP list command.
        
        @param info info about the entry (QUrlInfo)
        """
        if info.isValid() and info.isFile():
            if info.name() in self.__remoteFiles.values():
                self.__remoteFilesFound.append(info.name())
    
    def __initialSyncFile(self, type_, fileName):
        """
        Private method to do the initial synchronization of the given file.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords" or "useragents")
        @param fileName name of the file to be synchronized (string)
        """
        f = QFile(fileName)
        if self.__remoteFiles[type_] in self.__remoteFilesFound:
            self.syncStatus.emit(type_, True,
                self.__messages[type_]["RemoteExists"])
            f.open(QIODevice.WriteOnly)
            id = self.__ftp.get(self.__remoteFiles[type_], f)
            self.__syncIDs[id] = (type_, f, True)
        else:
            if f.exists():
                self.syncStatus.emit(type_, True,
                    self.__messages[type_]["RemoteMissing"])
                f.open(QIODevice.ReadOnly)
                id = self.__ftp.put(f, self.__remoteFiles[type_])
                self.__syncIDs[id] = (type_, f, False)
            else:
                self.syncStatus.emit(type_, True,
                    self.__messages[type_]["LocalMissing"])
    
    def __initialSync(self):
        """
        Private slot to do the initial synchronization.
        """
        # Bookmarks
        if Preferences.getHelp("SyncBookmarks"):
            self.__initialSyncFile("bookmarks",
                Helpviewer.HelpWindow.HelpWindow.bookmarksManager().getFileName())
        
        # History
        if Preferences.getHelp("SyncHistory"):
            self.__initialSyncFile("history",
                Helpviewer.HelpWindow.HelpWindow.historyManager().getFileName())
        
        # Passwords
        if Preferences.getHelp("SyncPasswords"):
            self.__initialSyncFile("passwords",
                Helpviewer.HelpWindow.HelpWindow.passwordManager().getFileName())
        
        # User Agent Settings
        if Preferences.getHelp("SyncUserAgents"):
            self.__initialSyncFile("useragents",
                Helpviewer.HelpWindow.HelpWindow.userAgentsManager().getFileName())
    
    def __syncFile(self, type_, fileName):
        """
        Private method to synchronize the given file.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords" or "useragents")
        @param fileName name of the file to be synchronized (string)
        """
        f = QFile(fileName)
        if f.exists():
            f.open(QIODevice.ReadOnly)
            id = self.__ftp.put(f, self.__remoteFiles[type_])
            self.__syncIDs[id] = (type_, f, False)
    
    def syncBookmarks(self):
        """
        Public method to synchronize the bookmarks.
        """
        self.__syncFile("bookmarks",
            Helpviewer.HelpWindow.HelpWindow.bookmarksManager().getFileName())
    
    def syncHistory(self):
        """
        Public method to synchronize the history.
        """
        self.__syncFile("history",
            Helpviewer.HelpWindow.HelpWindow.historyManager().getFileName())
    
    def syncPasswords(self):
        """
        Public method to synchronize the passwords.
        """
        self.__syncFile("passwords",
            Helpviewer.HelpWindow.HelpWindow.passwordManager().getFileName())
    
    def syncUserAgents(self):
        """
        Public method to synchronize the user agents.
        """
        self.__syncFile("useragents",
            Helpviewer.HelpWindow.HelpWindow.userAgentsManager().getFileName())
    
    def shutdown(self):
        """
        Public method to shut down the handler.
        """
        t = QTime.currentTime()
        t.start()
        while t.elapsed() < 5000 and self.__ftp.hasPendingCommands():
            QThread.msleep(200)
        if self.__ftp.hasPendingCommands():
            self.__ftp.clearPendingCommands()
        if self.__ftp.currentCommand() != 0:
            self.__ftp.abort()
