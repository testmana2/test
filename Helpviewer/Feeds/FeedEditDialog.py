# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to edit feed data.
"""

from PyQt4.QtCore import pyqtSlot, QUrl
from PyQt4.QtGui import QDialog, QDialogButtonBox

from .Ui_FeedEditDialog import Ui_FeedEditDialog


class FeedEditDialog(QDialog, Ui_FeedEditDialog):
    """
    Class implementing a dialog to edit feed data.
    """
    def __init__(self, urlString, title, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        self.titleEdit.setText(title)
        self.urlEdit.setText(urlString)
    
    def __setOkButton(self):
        """
        Private slot to enable or disable the OK button.
        """
        enable = True
        
        enable = enable and bool(self.titleEdit.text())
        
        urlString = self.urlEdit.text()
        enable = enable and bool(urlString)
        if urlString:
            url = QUrl(urlString)
            enable = enable and bool(url.scheme())
            enable = enable and bool(url.host())
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enable)
    
    @pyqtSlot(str)
    def on_titleEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the feed title.
        
        @param txt new feed title (string)
        """
        self.__setOkButton()
    
    @pyqtSlot(str)
    def on_urlEdit_textChanged(self, p0):
        """
        Private slot to handle changes of the feed URL.
        
        @param txt new feed URL (string)
        """
        self.__setOkButton()
    
    def getData(self):
        """
        Public method to get the entered feed data.
        
        @return tuple of two strings giving the feed URL and feed title
            (string, string)
        """
        return (self.urlEdit.text(), self.titleEdit.text())
