# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to get the data to rename a bookmark.
"""

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox

from .Ui_HgBookmarkRenameDialog import Ui_HgBookmarkRenameDialog


class HgBookmarkRenameDialog(QDialog, Ui_HgBookmarkRenameDialog):
    """
    Class implementing a dialog to get the data to rename a bookmark.
    """
    def __init__(self, bookmarksList, parent=None):
        """
        Constructor
        
        @param bookmarksList list of bookmarks (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
       
        self.bookmarkCombo.addItems(sorted(bookmarksList))
    
    def __updateUI(self):
        """
        Private slot to update the UI.
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            self.nameEdit.text() != "" and \
            self.bookmarkCombo.currentText() != ""
        )
    
    @pyqtSlot(str)
    def on_nameEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the bookmark name.
        
        @param txt text of the edit (string)
        """
        self.__updateUI()
    
    @pyqtSlot(str)
    def on_bookmarkCombo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the selected bookmark.
        
        @param txt name of the selected bookmark (string)
        """
        self.__updateUI()
    
    def getData(self):
        """
        Public method to retrieve the entered data.
        
        @return tuple naming the new and old bookmark names
            (string, string)
        """
        return self.nameEdit.text(), self.bookmarkCombo.currentText()