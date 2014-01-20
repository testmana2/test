# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the user data for a minimal hgrc file.
"""

from PyQt4.QtGui import QDialog

from .Ui_MercurialUserDataDialog import Ui_MercurialUserDataDialog


class MercurialUserDataDialog(QDialog, Ui_MercurialUserDataDialog):
    """
    Class implementing a dialog to enter the user data for a minimal hgrc file.
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
        Public method to retrieve the data.
        
        @return tuple containing the user name and the user email address
            (string, string)
        """
        return self.usernameEdit.text(), self.emailEdit.text()
