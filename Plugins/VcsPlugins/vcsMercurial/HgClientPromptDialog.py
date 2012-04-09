# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a prompt dialog for the Mercurial command server.
"""

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox, QTextCursor

from .Ui_HgClientPromptDialog import Ui_HgClientPromptDialog


class HgClientPromptDialog(QDialog, Ui_HgClientPromptDialog):
    """
    Class implementing a prompt dialog for the Mercurial command server.
    """
    def __init__(self, size, message, parent=None):
        """
        Constructor
        
        @param size maximum length of the requested input (integer)
        @param message message sent by the server (string)
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        self.inputEdit.setMaxLength(size)
        self.messageEdit.setPlainText(message)
        
        tc = self.messageEdit.textCursor()
        tc.movePosition(QTextCursor.End)
        self.messageEdit.setTextCursor(tc)
        self.messageEdit.ensureCursorVisible()
    
    @pyqtSlot(str)
    def on_inputEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the user input.
        
        @param txt text entered by the user (string)
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(bool(txt))
    
    def getInput(self):
        """
        Public method to get the user input.
        
        @return user input (string)
        """
        return self.inputEdit.text()
