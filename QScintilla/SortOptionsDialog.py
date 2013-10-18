# -*- coding: utf-8 -*-

# Copyright (c) 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the sort options for a line sort.
"""

from PyQt4.QtGui import QDialog

from .Ui_SortOptionsDialog import Ui_SortOptionsDialog


class SortOptionsDialog(QDialog, Ui_SortOptionsDialog):
    """
    Class implementing a dialog to enter the sort options for a line sort.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
    
    def getData(self):
        """
        Public method to get the selected options.
        
        @return tuple of three flags indicating ascending order, alphanumeric
            sort and case sensitivity (tuple of three boolean)
        """
        return (
            self.ascendingButton.isChecked(),
            self.alnumButton.isChecked(),
            self.respectCaseButton.isChecked()
        )
