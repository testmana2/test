# -*- coding: utf-8 -*-

# Copyright (c) 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a shelve operation.
"""

from PyQt4.QtCore import QDateTime
from PyQt4.QtGui import QDialog

from .Ui_HgShelveDataDialog import Ui_HgShelveDataDialog


class HgShelveDataDialog(QDialog, Ui_HgShelveDataDialog):
    """
    Class implementing a dialog to enter the data for a shelve operation.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.dateTimeEdit.setDateTime(QDateTime.currentDateTime())
    
    def getData(self):
        """
        Public method to get the user data.
        
        @return tuple containing the name (string), date (QDateTime),
            message (string) and a flag indicating to add/remove
            new/missing files (boolean)
        """
        return (
            self.nameEdit.text(),
            self.dateTimeEdit.dateTime(),
            self.messageEdit.toPlainText(),
            self.addRemoveCheckBox.isChecked(),
        )
