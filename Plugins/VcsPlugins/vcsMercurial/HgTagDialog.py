# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a tagging operation.
"""

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox

from .Ui_HgTagDialog import Ui_HgTagDialog

import UI.PixmapCache


class HgTagDialog(QDialog, Ui_HgTagDialog):
    """
    Class implementing a dialog to enter the data for a tagging operation.
    """
    CreateGlobalTag = 1
    CreateLocalTag = 2
    DeleteGlobalTag = 3
    DeleteLocalTag = 4
    
    def __init__(self, taglist, revision=None, tagName=None, parent=None):
        """
        Constructor
        
        @param taglist list of previously entered tags (list of strings)
        @param revision revision to set tag for (string)
        @param tagName name of the tag (string)
        @param parent parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
       
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.setEnabled(False)
        
        self.tagCombo.clear()
        self.tagCombo.addItem("", False)
        for tag, isLocal in sorted(taglist):
            if isLocal:
                icon = UI.PixmapCache.getIcon("vcsTagLocal.png")
            else:
                icon = UI.PixmapCache.getIcon("vcsTagGlobal.png")
            self.tagCombo.addItem(icon, tag, isLocal)
        
        if revision:
            self.revisionEdit.setText(revision)
        
        if tagName:
            index = self.tagCombo.findText(tagName)
            if index > -1:
                self.tagCombo.setCurrentIndex(index)
                # suggest the most relevant tag action
                self.deleteTagButton.setChecked(True)
            else:
                self.tagCombo.setEditText(tagName)
    
    @pyqtSlot(str)
    def on_tagCombo_editTextChanged(self, text):
        """
        Private method used to enable/disable the OK-button.
        
        @param text tag name entered in the combo (string)
        """
        self.okButton.setDisabled(text == "")
    
    @pyqtSlot(int)
    def on_tagCombo_currentIndexChanged(self, index):
        """
        Private slot setting the local status of the selected entry.
        """
        isLocal = self.tagCombo.itemData(index)
        if isLocal:
            self.localTagButton.setChecked(True)
        else:
            self.globalTagButton.setChecked(True)
    
    def getParameters(self):
        """
        Public method to retrieve the tag data.
        
        @return tuple of two strings and int (tag, revision, tag operation)
        """
        tag = self.tagCombo.currentText()
        tagOp = 0
        if self.createTagButton.isChecked():
            if self.globalTagButton.isChecked():
                tagOp = HgTagDialog.CreateGlobalTag
            else:
                tagOp = HgTagDialog.CreateLocalTag
        else:
            if self.globalTagButton.isChecked():
                tagOp = HgTagDialog.DeleteGlobalTag
            else:
                tagOp = HgTagDialog.DeleteLocalTag
        return (tag, self.revisionEdit.text(), tagOp)
