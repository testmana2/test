# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the downloader for GreaseMonkey scripts.
"""

import os

from PyQt4.QtCore import pyqtSignal, QObject, QSettings, QRegExp, QUrl
from PyQt4.QtGui import QDialog
from PyQt4.QtNetwork import QNetworkReply

from E5Gui import E5MessageBox

import Helpviewer.HelpWindow
from Helpviewer import HelpUtilities
from Helpviewer.Network.FollowRedirectReply import FollowRedirectReply

from .GreaseMonkeyScript import GreaseMonkeyScript
from .GreaseMonkeyAddScriptDialog import GreaseMonkeyAddScriptDialog


class GreaseMonkeyDownloader(QObject):
    """
    Class implementing the downloader for GreaseMonkey scripts.
    """
    finished = pyqtSignal()
    
    def __init__(self, request, manager):
        """
        Constructor
        
        @param request reference to the request object (QNetworkRequest)
        @param manager reference to the GreaseMonkey manager (GreaseMonkeyManager)
        """
        super().__init__()
        
        self.__manager = manager
        
        self.__reply = FollowRedirectReply(request.url(),
            Helpviewer.HelpWindow.HelpWindow.networkAccessManager())
        self.__reply.finished.connect(self.__scriptDownloaded)
        
        self.__fileName = ""
        self.__requireUrls = []
    
    def __scriptDownloaded(self):
        """
        Private slot to handle the finished download of a script.
        """
        if self.sender() != self.__reply:
            self.finished.emit()
            return
        
        response = bytes(self.__reply.readAll()).decode()
        
        if self.__reply.error() == QNetworkReply.NoError and \
           "// ==UserScript==" in response:
            filePath = os.path.join(self.__manager.scriptsDirectory(),
                HelpUtilities.getFileNameFromUrl(self.__reply.url()))
            self.__fileName = HelpUtilities.ensureUniqueFilename(filePath)
            
            try:
                f = open(self.__fileName, "w", encoding="utf-8")
            except (IOError, OSError) as err:
                E5MessageBox.critical(None,
                    self.trUtf8("GreaseMonkey Download"),
                    self.trUtf8("""<p>The file <b>{0}</b> could not be opened"""
                                """ for writing.<br/>Reason: {1}</p>""").format(
                                self.__fileName, str(err)))
                self.finished.emit()
                return
            f.write(response)
            f.close()
            
            settings = QSettings(os.path.join(self.__manager.requireScriptsDirectory(),
                                              "requires.ini"),
                                 QSettings.IniFormat)
            settings.beginGroup("Files")
            
            rx = QRegExp("@require(.*)\\n")
            rx.setMinimal(True)
            rx.indexIn(response)
            
            for i in range(1, rx.captureCount() + 1):
                url = rx.cap(i).strip()
                if url and not settings.contains(url):
                    self.__requireUrls.append(QUrl(url))
        
        self.__reply.deleteLater()
        self.__reply = None
        
        self.__downloadRequires()
    
    def __requireDownloaded(self):
        """
        Private slot to handle the finished download of a required script.
        """
        if self.sender() != self.__reply:
            self.finished.emit()
            return
        
        response = bytes(self.__reply.readAll()).decode()
        
        if self.__reply.error() == QNetworkReply.NoError and response:
            filePath = os.path.join(self.__manager.requireScriptsDirectory(),
                                    "require.js")
            fileName = HelpUtilities.ensureUniqueFilename(filePath, "{0}")
            
            try:
                f = open(fileName, "w", encoding="utf-8")
            except (IOError, OSError) as err:
                E5MessageBox.critical(None,
                    self.trUtf8("GreaseMonkey Download"),
                    self.trUtf8("""<p>The file <b>{0}</b> could not be opened"""
                                """ for writing.<br/>Reason: {1}</p>""").format(
                                fileName, str(err)))
                self.finished.emit()
                return
            f.write(response)
            f.close()
            
            settings = QSettings(os.path.join(self.__manager.requireScriptsDirectory(),
                                              "requires.ini"),
                                 QSettings.IniFormat)
            settings.beginGroup("Files")
            settings.setValue(self.__reply.originalUrl().toString(), fileName)
        
        self.__reply.deleteLater()
        self.__reply = None
        
        self.__downloadRequires()
    
    def __downloadRequires(self):
        """
        Private slot to initiate the download of required scripts.
        """
        if self.__requireUrls:
            self.__reply = FollowRedirectReply(self.__requireUrls.pop(0),
                Helpviewer.HelpWindow.HelpWindow.networkAccessManager())
            self.__reply.finished.connect(self.__requireDownloaded)
        else:
            deleteScript = True
            script = GreaseMonkeyScript(self.__manager, self.__fileName)
            
            if script.isValid():
                if not self.__manager.containsScript(script.fullName()):
                    dlg = GreaseMonkeyAddScriptDialog(self.__manager, script)
                    deleteScript = dlg.exec_() != QDialog.Accepted
                else:
                    E5MessageBox.information(None,
                        self.trUtf8("GreaseMonkey Download"),
                        self.trUtf8("""<p><b>{0}</b> is already installed.</p>""")
                            .format(script.name()))
            
            if deleteScript:
                try:
                    os.remove(self.__fileName)
                except (IOError, OSError):
                    # ignore
                    pass
            
            self.finished.emit()
