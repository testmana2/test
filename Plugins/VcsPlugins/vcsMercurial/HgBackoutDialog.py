# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a backout operation.
"""

from PyQt4.QtCore import pyqtSlot, QDateTime
from PyQt4.QtGui import QDialog, QDialogButtonBox

from .Ui_HgBackoutDialog import Ui_HgBackoutDialog

class HgBackoutDialog(QDialog, Ui_HgBackoutDialog):
    """
    Class implementing a dialog to enter the data for a backout operation.
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
        
        self.tagCombo.addItems(sorted(tagsList))
        self.branchCombo.addItems(["default"] + sorted(branchesList))
        
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.setEnabled(False)
        
        self.__initDateTime = QDateTime.currentDateTime()
        self.dateEdit.setDateTime(self.__initDateTime)
    
    @pyqtSlot(bool)
    def on_noneButton_toggled(self, checked):
        """
        Private slot to handle the toggling of the None revision button.
        
        @param checked flag indicating the checked state (boolean)
        """
        self.okButton.setEnabled(not checked)
    
    def getParameters(self):
        """
        Public method to retrieve the backout data.
        
        @return tuple naming the revision, a flag indicating a 
            merge, the commit date, the commit user and a commit message
            (string, boolean, string, string, string)
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
        
        if self.dateEdit.dateTime() != self.__initDateTime:
            date = self.dateEdit.dateTime().toString("yyyy-MM-dd hh:mm")
        else:
            date = ""
        
        if self.messageEdit.toPlainText():
            msg = self.messageEdit.toPlainText()
        else:
            msg = self.trUtf8("Backed out changeset <{0}>.").format(rev)
        
        return (rev, 
                self.mergeCheckBox.isChecked, 
                date, 
                self.userEdit.text(), 
                msg
        )
