# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select a revision.
"""

from PyQt4.QtGui import QDialog

from .Ui_HgRevisionSelectionDialog import Ui_HgRevisionSelectionDialog

class HgRevisionSelectionDialog(QDialog, Ui_HgRevisionSelectionDialog):
    """
    Class implementing a dialog to select a revision.
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
       
        self.tagCombo.addItems(list(sorted(tagsList)))
        self.branchCombo.addItems(list(sorted(["default"] + branchesList)))
    
    def getRevision(self):
        """
        Public method to retrieve the selected revision.
        
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
        
        return rev
