# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a bundle operation.
"""

from PyQt4.QtGui import QDialog

from .Ui_HgBundleDialog import Ui_HgBundleDialog

class HgBundleDialog(QDialog, Ui_HgBundleDialog):
    """
    Class implementing a dialog to enter the data for a bundle operation.
    """
    def __init__(self, tagsList, branchesList, parent = None):
        """
        Constructor
        
        @param tagsList list of tags (list of strings)
        @param branchesList list of branches (list of strings)
        @param parent parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.compressionCombo.addItems(["", "bzip2", "gzip", "none"])
        self.tagCombo.addItems(sorted(tagsList))
        self.branchCombo.addItems(["default"] + sorted(branchesList))
    
    def getParameters(self):
        """
        Public method to retrieve the bundle data.
        
        @return tuple naming the revision, the compression type and a flag indicating 
            to bundle all changesets (string, string, boolean)
        """
        if self.numberButton.isChecked():
            rev = str(self.numberSpinBox.value())
        elif self.idButton.isChecked():
            rev = self.idEdit.text()
        elif self.tagButton.isChecked():
            rev = self.tagCombo.currentText()
        elif self.branchButton.isChecked():
            rev = self.branchCombo.currentText()
        else:
            rev = ""
        
        return rev, self.compressionCombo.currentText(), self.allCheckBox.isChecked()
