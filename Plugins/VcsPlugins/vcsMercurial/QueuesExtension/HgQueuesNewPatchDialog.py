# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to get the data for a new patch.
"""

from PyQt4.QtCore import pyqtSlot, QDate
from PyQt4.QtGui import QDialog, QDialogButtonBox

from .Ui_HgQueuesNewPatchDialog import Ui_HgQueuesNewPatchDialog


class HgQueuesNewPatchDialog(QDialog, Ui_HgQueuesNewPatchDialog):
    """
    Class implementing a dialog to get the data for a new patch.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.dateEdit.setDate(QDate.currentDate())
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
    
    def __updateUI(self):
        """
        Private slot to update the UI.
        """
        enable = self.nameEdit.text() != "" and \
                 self.messageEdit.toPlainText() != ""
        if self.userGroup.isChecked():
            enable = enable and \
                (self.currentUserCheckBox.isChecked() or \
                 self.userEdit.text() != "")
        
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enable)
    
    @pyqtSlot(str)
    def on_nameEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the patch name.
        
        @param txt text of the edit (string)
        """
        self.__updateUI()
    
    @pyqtSlot()
    def on_messageEdit_textChanged(self):
        """
        Private slot to handle changes of the patch message.
        
        @param txt text of the edit (string)
        """
        self.__updateUI()
    
    def getData(self):
        """
        Public method to retrieve the entered data.
        
        @return tuple giving the patch name and message, a tuple giving a
            flag indicating to set the user, a flag indicating to use the
            current user and the user name and another tuple giving a flag
            indicating to set the date, a flag indicating to use the
            current date and the date (string, string, (boolean, boolean, string),
            (boolean, boolean, string))
        """
        userData = (self.userGroup.isChecked(),
                    self.currentUserCheckBox.isChecked(), 
                    self.userEdit.text())
        dateData = (self.dateGroup.isChecked(), 
                    self.currentDateCheckBox.isChecked(), 
                    self.dateEdit.date().toString("yyyy-MM-dd"))
        return (self.nameEdit.text(), self.messageEdit.toPlainText(), 
            userData, dateData)
