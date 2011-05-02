# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the bookmark dialog.
"""

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox

from .Ui_HgBookmarkDialog import Ui_HgBookmarkDialog


class HgBookmarkDialog(QDialog, Ui_HgBookmarkDialog):
    """
    Class mplementing the bookmark dialog.
    """
    def __init__(self, tagsList, branchesList, bookmarksList, parent=None):
        """
        Constructor
        
        @param tagsList list of tags (list of strings)
        @param branchesList list of branches (list of strings)
        @param bookmarksList list of bookmarks (list of strings)
        @param parent reference to the parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
       
        self.tagCombo.addItems(sorted(tagsList))
        self.branchCombo.addItems(["default"] + sorted(branchesList))
        self.bookmarkCombo.addItems(sorted(bookmarksList))
    
    @pyqtSlot(str)
    def on_nameEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the bookmark name.
        
        @param txt text of the edit (string)
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(txt != "")
    
    def getData(self):
        """
        Public method to retrieve the entered data.
        
        @return tuple naming the revision and the bookmark name
            (string, string)
        """
        if self.numberButton.isChecked():
            rev = str(self.numberSpinBox.value())
        elif self.idButton.isChecked():
            rev = self.idEdit.text()
        elif self.tagButton.isChecked():
            rev = self.tagCombo.currentText()
        elif self.branchButton.isChecked():
            rev = self.branchCombo.currentText()
        elif self.bookmarkButton.isChecked():
            rev = self.bookmarkCombo.currentText()
        else:
            rev = ""
        
        return rev, self.nameEdit.text()
