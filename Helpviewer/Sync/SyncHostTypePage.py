# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the synchronization host type wizard page.
"""

from PyQt4.QtGui import QWizardPage

from . import SyncGlobals

from .Ui_SyncHostTypePage import Ui_SyncHostTypePage

import Preferences


class SyncHostTypePage(QWizardPage, Ui_SyncHostTypePage):
    """
    Class implementing the synchronization host type wizard page.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        if Preferences.getHelp("SyncType") == 0:
            self.ftpRadioButton.setChecked(True)
        else:
            self.noneRadioButton.setChecked(True)
    
    def nextId(self):
        """
        Public method returning the ID of the next wizard page.
        
        @return next wizard page ID (integer)
        """
        # save the settings
        if self.ftpRadioButton.isChecked():
            Preferences.setHelp("SyncType", 0)
            return SyncGlobals.PageFTPSettings
        else:
            Preferences.setHelp("SyncType", -1)
            return SyncGlobals.PageCheck
