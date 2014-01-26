# -*- coding: utf-8 -*-

"""
Module implementing a dialog to enter data needed for the initial creation
of a repository configuration file (hgrc).
"""

from PyQt4.QtCore import pyqtSlot, QUrl
from PyQt4.QtGui import QDialog, QLineEdit

from .Ui_HgRepoConfigDataDialog import Ui_HgRepoConfigDataDialog

import UI.PixmapCache


class HgRepoConfigDataDialog(QDialog, Ui_HgRepoConfigDataDialog):
    """
    Class implementing a dialog to enter data needed for the initial creation
    of a repository configuration file (hgrc).
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.defaultShowPasswordButton.setIcon(
            UI.PixmapCache.getIcon("showPassword.png"))
        self.defaultPushShowPasswordButton.setIcon(
            UI.PixmapCache.getIcon("showPassword.png"))
        
        self.resize(self.width(), self.minimumSizeHint().height())
    
    @pyqtSlot(bool)
    def on_defaultShowPasswordButton_clicked(self, checked):
        """
        Private slot to switch the default password visibility
        of the default password.
        """
        if checked:
            self.defaultPasswordEdit.setEchoMode(QLineEdit.Normal)
        else:
            self.defaultPasswordEdit.setEchoMode(QLineEdit.Password)
    
    @pyqtSlot(bool)
    def on_defaultPushShowPasswordButton_clicked(self, checked):
        """
        Private slot to switch the default password visibility
        of the default push password.
        """
        if checked:
            self.defaultPushPasswordEdit.setEchoMode(QLineEdit.Normal)
        else:
            self.defaultPushPasswordEdit.setEchoMode(QLineEdit.Password)
    
    def getData(self):
        """
        Public method to get the data entered into the dialog.
        
        @return tuple giving the default and default push URLs (tuple of
            two strings)
        """
        defaultUrl = QUrl.fromUserInput(self.defaultUrlEdit.text())
        username = self.defaultUserEdit.text()
        password = self.defaultPasswordEdit.text()
        if username:
            defaultUrl.setUserName(username)
        if password:
            defaultUrl.setPassword(password)
        if not defaultUrl.isValid():
            defaultUrl = ""
        else:
            defaultUrl = defaultUrl.toString()
        
        defaultPushUrl = QUrl.fromUserInput(self.defaultPushUrlEdit.text())
        username = self.defaultPushUserEdit.text()
        password = self.defaultPushPasswordEdit.text()
        if username:
            defaultPushUrl.setUserName(username)
        if password:
            defaultPushUrl.setPassword(password)
        if not defaultPushUrl.isValid():
            defaultPushUrl = ""
        else:
            defaultPushUrl = defaultPushUrl.toString()
        
        return defaultUrl, defaultPushUrl
