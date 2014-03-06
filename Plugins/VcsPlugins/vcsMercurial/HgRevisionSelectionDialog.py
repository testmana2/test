# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select a revision.
"""

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox

from .Ui_HgRevisionSelectionDialog import Ui_HgRevisionSelectionDialog


class HgRevisionSelectionDialog(QDialog, Ui_HgRevisionSelectionDialog):
    """
    Class implementing a dialog to select a revision.
    """
    def __init__(self, tagsList, branchesList, bookmarksList=None,
                 showNone=False, parent=None):
        """
        Constructor
        
        @param tagsList list of tags (list of strings)
        @param branchesList list of branches (list of strings)
        @param bookmarksList list of bookmarks (list of strings)
        @param showNone flag influencing the label of the 'None' selection
            (boolean)
        @param parent parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
       
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        
        self.tagCombo.addItems(sorted(tagsList))
        self.branchCombo.addItems(["default"] + sorted(branchesList))
        if bookmarksList is not None:
            self.bookmarkCombo.addItems(sorted(bookmarksList))
        else:
            self.bookmarkButton.setHidden(True)
            self.bookmarkCombo.setHidden(True)
        
        if showNone:
            self.tipButton.setText(self.trUtf8("No revision selected"))
            self.tipButton.setToolTip(self.trUtf8(
                "Select to not specify a specific revision"))
    
    def __updateOK(self):
        """
        Private slot to update the OK button.
        """
        enabled = True
        if self.idButton.isChecked():
            enabled = self.idEdit.text() != ""
        elif self.tagButton.isChecked():
            enabled = self.tagCombo.currentText() != ""
        elif self.branchButton.isChecked():
            enabled = self.branchCombo.currentText() != ""
        elif self.bookmarkButton.isChecked():
            enabled = self.bookmarkCombo.currentText() != ""
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enabled)
    
    @pyqtSlot(bool)
    def on_idButton_toggled(self, checked):
        """
        Private slot to handle changes of the ID select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_tagButton_toggled(self, checked):
        """
        Private slot to handle changes of the Tag select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_branchButton_toggled(self, checked):
        """
        Private slot to handle changes of the Branch select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(bool)
    def on_bookmarkButton_toggled(self, checked):
        """
        Private slot to handle changes of the Bookmark select button.
        
        @param checked state of the button (boolean)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_idEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the ID edit.
        
        @param txt text of the edit (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_tagCombo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Tag combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_branchCombo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Branch combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    @pyqtSlot(str)
    def on_bookmarkCombo_editTextChanged(self, txt):
        """
        Private slot to handle changes of the Bookmark combo.
        
        @param txt text of the combo (string)
        """
        self.__updateOK()
    
    def getRevision(self):
        """
        Public method to retrieve the selected revision.
        
        @return selected revision (string)
        """
        if self.numberButton.isChecked():
            rev = "rev({0})".format(self.numberSpinBox.value())
        elif self.idButton.isChecked():
            rev = "id({0})".format(self.idEdit.text())
        elif self.tagButton.isChecked():
            rev = self.tagCombo.currentText()
        elif self.branchButton.isChecked():
            rev = self.branchCombo.currentText()
        elif self.bookmarkButton.isChecked():
            rev = self.bookmarkCombo.currentText()
        else:
            rev = ""
        
        return rev
