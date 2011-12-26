# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter options used to start a project in the VCS.
"""

from PyQt4.QtGui import QDialog

from .Ui_HgOptionsDialog import Ui_HgOptionsDialog


class HgOptionsDialog(QDialog, Ui_HgOptionsDialog):
    """
    Class implementing a dialog to enter options used to start a project in the
    repository.
    """
    def __init__(self, vcs, project, parent=None):
        """
        Constructor
        
        @param vcs reference to the version control object
        @param project reference to the project object
        @param parent parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
    
    def getData(self):
        """
        Public slot to retrieve the data entered into the dialog.
        
        @return a dictionary containing the data entered
        """
        vcsdatadict = {
            "message": self.vcsLogEdit.text(),
        }
        return vcsdatadict
