# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a merge operation.
"""

from PyQt4.QtGui import QDialog

from .Ui_HgMergeDialog import Ui_HgMergeDialog

class HgMergeDialog(QDialog, Ui_HgMergeDialog):
    """
    Class implementing a dialog to enter the data for a merge operation.
    """
    def __init__(self, force, tagsList, branchesList, parent = None):
        """
        Constructor
        
        @param force flag indicating a forced merge (boolean)
        @param tagsList list of tags (list of strings)
        @param branchesList list of branches (list of strings)
        @param parent parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
       
        self.forceCheckBox.setChecked(force)
        self.tagCombo.addItems(sorted(tagsList))
        self.branchCombo.addItems(["default"] + sorted(branchesList))
    
    def getParameters(self):
        """
        Public method to retrieve the merge data.
        
        @return tuple naming the revision and a flag indicating a 
            forced merge (string, boolean)
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
        
        return rev, self.forceCheckBox.isChecked()
