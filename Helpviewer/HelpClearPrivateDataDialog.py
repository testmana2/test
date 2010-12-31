# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select which private data to clear.
"""

from PyQt4.QtGui import QDialog

from .Ui_HelpClearPrivateDataDialog import Ui_HelpClearPrivateDataDialog

class HelpClearPrivateDataDialog(QDialog, Ui_HelpClearPrivateDataDialog):
    """
    Class implementing a dialog to select which private data to clear.
    """
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
    
    def getData(self):
        """
        Public method to get the data from the dialog.
        
        @return tuple of flags indicating which data to clear (browsing history,
            search history, favicons, disk cache, cookies, passwords, web 
            databases, downloads) (list of boolean)
        """
        return (self.historyCheckBox.isChecked(), 
                self.searchCheckBox.isChecked(), 
                self.iconsCheckBox.isChecked(), 
                self.cacheCheckBox.isChecked(), 
                self.cookiesCheckBox.isChecked(), 
                self.passwordsCheckBox.isChecked(), 
                self.databasesCheckBox.isChecked(), 
                self.downloadsCheckBox.isChecked())
