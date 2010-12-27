# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the revisions for the hg diff command.
"""

from PyQt4.QtGui import QDialog

from .Ui_HgRevisionsSelectionDialog import Ui_HgRevisionsSelectionDialog

class HgRevisionsSelectionDialog(QDialog, Ui_HgRevisionsSelectionDialog):
    """
    Class implementing a dialog to enter the revisions for the hg diff command.
    """
    def __init__(self, tagsList, branchesList, parent = None):
        """
        Constructor
        
        @param tagsList list of tags (list of strings)
        @param branchesList list of branches (list of strings)
        @param parent parent widget of the dialog (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.tag1Combo.addItems(sorted(tagsList))
        self.tag2Combo.addItems(sorted(tagsList))
        self.branch1Combo.addItems(["default"] + sorted(branchesList))
        self.branch2Combo.addItems(["default"] + sorted(branchesList))
    
    def __getRevision(self, no):
        """
        Private method to generate the revision.
        
        @param no revision number to generate (1 or 2)
        @return revision (string)
        """
        if no == 1:
            numberButton = self.number1Button
            numberSpinBox = self.number1SpinBox
            idButton = self.id1Button
            idEdit = self.id1Edit
            tagButton = self.tag1Button
            tagCombo = self.tag1Combo
            branchButton = self.branch1Button
            branchCombo = self.branch1Combo
            tipButton = self.tip1Button
            prevButton = self.prev1Button
        else:
            numberButton = self.number2Button
            numberSpinBox = self.number2SpinBox
            idButton = self.id2Button
            idEdit = self.id2Edit
            tagButton = self.tag2Button
            tagCombo = self.tag2Combo
            branchButton = self.branch2Button
            branchCombo = self.branch2Combo
            tipButton = self.tip2Button
            prevButton = self.prev2Button
        
        if numberButton.isChecked():
            return str(numberSpinBox.value())
        elif idButton.isChecked():
            return idEdit.text()
        elif tagButton.isChecked():
            return tagCombo.currentText()
        elif branchButton.isChecked():
            return branchCombo.currentText()
        elif tipButton.isChecked():
            return "tip"
        elif prevButton.isChecked():
            return "."
    
    def getRevisions(self):
        """
        Public method to get the revisions.
        
        @return list two strings
        """
        rev1 = self.__getRevision(1)
        rev2 = self.__getRevision(2)
        
        return [rev1, rev2]
