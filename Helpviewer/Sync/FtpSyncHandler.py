# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a synchronization handler using FTP.
"""

from PyQt4.QtCore import pyqtSignal, QUrl, QIODevice, QTime, QThread, QTimer, QBuffer
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
        
        self.__state = "idle"
        self.__forceUpload = False
        
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
                "Uploading": self.trUtf8("Uploading local bookmarks file..."),
            },
            "history": {
                "RemoteExists": self.trUtf8(
                    "Remote history file exists! Syncing local copy..."),
                "RemoteMissing": self.trUtf8(
                    "Remote history file does NOT exists. Exporting local copy..."),
                "LocalMissing": self.trUtf8(
                    "Local history file does NOT exist. Skipping synchronization!"),
                "Uploading": self.trUtf8("Uploading local history file..."),
            },
            "passwords": {
                "RemoteExists": self.trUtf8(
                    "Remote logins file exists! Syncing local copy..."),
                "RemoteMissing": self.trUtf8(
                    "Remote logins file does NOT exists. Exporting local copy..."),
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
                "LocalMissing": self.trUtf8(
                    "Local user agent settings file does NOT exist."
                    " Skipping synchronization!"),
                "Uploading": self.trUtf8("Uploading local user agent settings file..."),
            },
        }
    
    def initialLoadAndCheck(self, forceUpload):
        """
        Public method to do the initial check.
        
        @keyparam forceUpload flag indicating a forced upload of the files (boolean)
        """
        if not Preferences.getHelp("SyncEnabled"):
            return
        
        self.__state = "initializing"
        self.__forceUpload = forceUpload
        
        self.__remoteFilesFound = []
        self.__syncIDs = {}
        
        self.__idleTimer = QTimer(self)
        self.__idleTimer.setInterval(Preferences.getHelp("SyncFtpIdleTimeout") * 1000)
        self.__idleTimer.timeout.connect(self.__idleTimeout)
        
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
                    if self.__ftp.currentCommand() == QFtp.Get:
                        self.__syncIDs[id][1].close()
                    self.syncStatus.emit(self.__syncIDs[id][0], False,
                        self.__ftp.errorString())
                    self.syncFinished.emit(self.__syncIDs[id][0], False,
                        self.__syncIDs[id][2])
                    del self.__syncIDs[id]
                    if not self.__syncIDs:
                        self.__state = "idle"
                        self.syncMessage.emit(self.trUtf8("Synchronization finished"))
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
                    if self.__ftp.currentCommand() == QFtp.Get:
                        self.__syncIDs[id][1].close()
                        ok, error = self.writeFile(self.__syncIDs[id][1].buffer(),
                                                   self.__syncIDs[id][3])
                        if ok:
                            self.syncStatus.emit(self.__syncIDs[id][0], True,
                                self.__messages[self.__syncIDs[id][0]]["RemoteExists"])
                        else:
                            self.syncStatus.emit(self.__syncIDs[id][0], False,
                                error)
                    self.syncFinished.emit(self.__syncIDs[id][0], True,
                        self.__syncIDs[id][2])
                    del self.__syncIDs[id]
                    if not self.__syncIDs:
                        self.__state = "idle"
                        self.syncMessage.emit(self.trUtf8("Synchronization finished"))
    
    def __storeReached(self):
        """
        Private slot executed, when the storage directory was reached.
        """
        if self.__state == "initializing":
            self.__ftp.list()
            self.__idleTimer.start()
    
    def __checkSyncFiles(self, info):
        """
        Private slot called for each entry sent by the FTP list command.
        
        @param info info about the entry (QUrlInfo)
        """
        if info.isValid() and info.isFile():
            if info.name() in self.__remoteFiles.values():
                self.__remoteFilesFound.append(info.name())
    
    def __downloadFile(self, type_, fileName):
        """
        Private method to downlaod the given file.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords" or "useragents")
        @param fileName name of the file to be downloaded (string)
        """
        buffer = QBuffer(self)
        buffer.open(QIODevice.WriteOnly)
        id = self.__ftp.get(self.__remoteFiles[type_], buffer)
        self.__syncIDs[id] = (type_, buffer, True, fileName)
    
    def __uploadFile(self, type_, fileName):
        """
        Private method to upload the given file.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords" or "useragents")
        @param fileName name of the file to be uploaded (string)
        """
        data = self.readFile(fileName)
        if data.isEmpty():
            self.syncStatus.emit(type_, True,
                self.__messages[type_]["LocalMissing"])
        else:
            id = self.__ftp.put(data, self.__remoteFiles[type_])
            self.__syncIDs[id] = (type_, data, False)
    
    def __initialSyncFile(self, type_, fileName):
        """
        Private method to do the initial synchronization of the given file.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords" or "useragents")
        @param fileName name of the file to be synchronized (string)
        """
        if not self.__forceUpload and \
           self.__remoteFiles[type_] in self.__remoteFilesFound:
            self.__downloadFile(type_, fileName)
        else:
            self.syncStatus.emit(type_, True,
                self.__messages[type_]["RemoteMissing"])
            self.__uploadFile(type_, fileName)
    
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
        
        self.__forceUpload = False
    
    def __syncFile(self, type_, fileName):
        """
        Private method to synchronize the given file.
        
        @param type_ type of the synchronization event (string one
            of "bookmarks", "history", "passwords" or "useragents")
        @param fileName name of the file to be synchronized (string)
        """
        if self.__state == "initializing":
            return
        
        self.__state = "uploading"
        self.syncStatus.emit(type_, True, self.__messages[type_]["Uploading"])
        self.__uploadFile(type_, fileName)
    
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
        if self.__idleTimer.isActive():
            self.__idleTimer.stop()
        
        t = QTime.currentTime()
        t.start()
        while t.elapsed() < 5000 and self.__ftp.hasPendingCommands():
            QThread.msleep(200)
        if self.__ftp.hasPendingCommands():
            self.__ftp.clearPendingCommands()
        if self.__ftp.currentCommand() != 0:
            self.__ftp.abort()
    
    def __idleTimeout(self):
        """
        Private slot to prevent a disconnect from the server.
        """
        self.__ftp.rawCommand("NOOP")
