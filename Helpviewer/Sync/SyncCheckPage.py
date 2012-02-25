# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the synchronization status wizard page.
"""

import os

from PyQt4.QtCore import QByteArray
from PyQt4.QtGui import QWizardPage, QMovie

from .Ui_SyncCheckPage import Ui_SyncCheckPage

import Preferences
import UI.PixmapCache

import Helpviewer.HelpWindow

from eric5config import getConfig


class SyncCheckPage(QWizardPage, Ui_SyncCheckPage):
    """
    Class implementing the synchronization status wizard page.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
    
    def initializePage(self):
        """
        Public method to initialize the page.
        """
        self.syncErrorLabel.hide()
        
        syncMgr = Helpviewer.HelpWindow.HelpWindow.syncManager()
        syncMgr.syncError.connect(self.__syncError)
        syncMgr.loadSettings()
        
        if Preferences.getHelp("SyncType") == 0:
            self.handlerLabel.setText(self.trUtf8("FTP"))
            self.hostLabel.setText(Preferences.getHelp("SyncFtpServer"))
        else:
            self.handlerLabel.setText(self.trUtf8("No Synchronization"))
            self.hostLabel.setText("")
        
        self.bookmarkMsgLabel.setText("")
        self.historyMsgLabel.setText("")
        self.passwordsMsgLabel.setText("")
        self.userAgentsMsgLabel.setText("")
        
        if not syncMgr.syncEnabled():
            self.bookmarkLabel.setPixmap(UI.PixmapCache.getPixmap("syncNo.png"))
            self.historyLabel.setPixmap(UI.PixmapCache.getPixmap("syncNo.png"))
            self.passwordsLabel.setPixmap(UI.PixmapCache.getPixmap("syncNo.png"))
            self.userAgentsLabel.setPixmap(UI.PixmapCache.getPixmap("syncNo.png"))
            return
        
        animationFile = os.path.join(getConfig("ericPixDir"), "loading.gif")
        
        # bookmarks
        if Preferences.getHelp("SyncBookmarks"):
            self.__makeAnimatedLabel(animationFile, self.bookmarkLabel)
        else:
            self.bookmarkLabel.setPixmap(UI.PixmapCache.getPixmap("syncNo.png"))
        
        # history
        if Preferences.getHelp("SyncHistory"):
            self.__makeAnimatedLabel(animationFile, self.historyLabel)
        else:
            self.historyLabel.setPixmap(UI.PixmapCache.getPixmap("syncNo.png"))
        
        # Passwords
        if Preferences.getHelp("SyncPasswords"):
            self.__makeAnimatedLabel(animationFile, self.passwordsLabel)
        else:
            self.passwordsLabel.setPixmap(UI.PixmapCache.getPixmap("syncNo.png"))
        
        # user agent settings
        if Preferences.getHelp("SyncUserAgents"):
            self.__makeAnimatedLabel(animationFile, self.userAgentsLabel)
        else:
            self.userAgentsLabel.setPixmap(UI.PixmapCache.getPixmap("syncNo.png"))
        
        handler = syncMgr.handler()
        handler.syncStatus.connect(self.__updatePage)
    
    def __makeAnimatedLabel(self, fileName, label):
        """
        Private slot to create an animated label.
        
        @param fileName name of the file containing the animation (string)
        @param label reference to the label to be animated (QLabel)
        """
        movie = QMovie(fileName, QByteArray(), label)
        movie.setSpeed(100)
        label.setMovie(movie)
        movie.start()
    
    def __updatePage(self, type_, done, msg):
        """
        Private slot to update the synchronization status info.
        
        @param type_ type of synchronization data (string)
        @param done flag indicating success (boolean)
        @param msg synchronization message (string)
        """
        if type_ == "bookmarks":
            if done:
                self.bookmarkLabel.setPixmap(
                    UI.PixmapCache.getPixmap("syncCompleted.png"))
            else:
                self.bookmarkLabel.setPixmap(UI.PixmapCache.getPixmap("syncFailed.png"))
            self.bookmarkMsgLabel.setText(msg)
        elif type_ == "history":
            if done:
                self.historyLabel.setPixmap(UI.PixmapCache.getPixmap("syncCompleted.png"))
            else:
                self.historyLabel.setPixmap(UI.PixmapCache.getPixmap("syncFailed.png"))
            self.historyMsgLabel.setText(msg)
        elif type_ == "passwords":
            if done:
                self.passwordsLabel.setPixmap(
                    UI.PixmapCache.getPixmap("syncCompleted.png"))
            else:
                self.passwordsLabel.setPixmap(UI.PixmapCache.getPixmap("syncFailed.png"))
            self.passwordsMsgLabel.setText(msg)
        elif type_ == "useragents":
            if done:
                self.userAgentsLabel.setPixmap(
                    UI.PixmapCache.getPixmap("syncCompleted.png"))
            else:
                self.userAgentsLabel.setPixmap(UI.PixmapCache.getPixmap("syncFailed.png"))
            self.userAgentsMsgLabel.setText(msg)
    
    def __syncError(self, message):
        """
        Private slot to handle general synchronization issues.
        
        @param message error message (string)
        """
        self.syncErrorLabel.show()
        self.syncErrorLabel.setText(
            self.trUtf8('<font color="#FF0000"><b>Error:</b> {0}</font>').format(message))
