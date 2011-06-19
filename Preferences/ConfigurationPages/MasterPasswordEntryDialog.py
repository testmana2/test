# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter or change the master password.
"""

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox

from .Ui_MasterPasswordEntryDialog import Ui_MasterPasswordEntryDialog

from Utilities.crypto.py3PBKDF2 import verifyPassword


class MasterPasswordEntryDialog(QDialog, Ui_MasterPasswordEntryDialog):
    """
    Class implementing a dialog to enter or change the master password.
    """
    def __init__(self, oldPasswordHash, parent=None):
        """
        Constructor
        
        @param oldPasswordHash hash of the current password (string)
        @param parent reference to the parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.__oldPasswordHash = oldPasswordHash
        if self.__oldPasswordHash == "":
            self.currentPasswordEdit.setEnabled(False)
            if hasattr(self.currentPasswordEdit, "setPlaceholderText"):
                self.currentPasswordEdit.setPlaceholderText(
                    self.trUtf8("(not defined yet)"))
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
    
    def __updateUI(self):
        """
        Private slot to update the variable parts of the UI.
        """
        enable = True
        error = ""
        if self.currentPasswordEdit.isEnabled():
            enable = \
                verifyPassword(self.currentPasswordEdit.text(), self.__oldPasswordHash)
            if not enable:
                error = error or self.trUtf8("Wrong password entered.")
        
        if self.newPasswordEdit.text() == "":
            enable = False
            error = error or self.trUtf8("New password must not be empty.")
        
        if self.newPasswordEdit.text() != "" and \
           self.newPasswordEdit.text() != self.newPasswordAgainEdit.text():
            enable = False
            error = error or self.trUtf8("Repeated password is wrong.")
        
        if self.currentPasswordEdit.isEnabled():
            if self.newPasswordEdit.text() == self.currentPasswordEdit.text():
                enable = False
                error = error or self.trUtf8("Old and new password must not be the same.")
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enable)
        self.errorLabel.setText(error)
    
    @pyqtSlot(str)
    def on_currentPasswordEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the current password.
        
        @param txt content of the edit widget (string)
        """
        self.__updateUI()
    
    @pyqtSlot(str)
    def on_newPasswordEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the new password.
        
        @param txt content of the edit widget (string)
        """
        self.passwordMeter.checkPasswordStrength(txt)
        self.__updateUI()
    
    @pyqtSlot(str)
    def on_newPasswordAgainEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the new again password.
        
        @param txt content of the edit widget (string)
        """
        self.__updateUI()
    
    def getMasterPassword(self):
        """
        Public method to get the new master password.
        """
        return self.newPasswordEdit.text()
    
    def getCurrentPassword(self):
        """
        Public method to get the current master password.
        """
        return self.currentPasswordEdit.text()