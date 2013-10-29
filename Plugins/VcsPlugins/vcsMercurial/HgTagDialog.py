# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a tagging operation.
"""

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox

from .Ui_HgTagDialog import Ui_HgTagDialog


class HgTagDialog(QDialog, Ui_HgTagDialog):
    """
    Class implementing a dialog to enter the data for a tagging operation.
    """
    CreateRegularTag = 1
    CreateLocalTag = 2
    DeleteTag = 3
    CreateBranch = 4
    
    def __init__(self, taglist, parent=None):
        """
        Constructor
        
        @param taglist list of previously entered tags (list of strings)
        @param parent parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
       
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.setEnabled(False)
        
        self.tagCombo.clear()
        self.tagCombo.addItems(sorted(taglist))
    
    @pyqtSlot(str)
    def on_tagCombo_editTextChanged(self, text):
        """
        Private method used to enable/disable the OK-button.
        
        @param text tag name entered in the combo (string)
        """
        self.okButton.setDisabled(text == "")
    
    def getParameters(self):
        """
        Public method to retrieve the tag data.
        
        @return tuple of string and int (tag, tag operation)
        """
        tag = self.tagCombo.currentText()
        tagOp = 0
        if self.createRegularButton.isChecked():
            tagOp = HgTagDialog.CreateRegularTag
        elif self.createLocalButton.isChecked():
            tagOp = HgTagDialog.CreateLocalTag
        elif self.deleteButton.isChecked():
            tagOp = HgTagDialog.DeleteTag
        return (tag, tagOp)
