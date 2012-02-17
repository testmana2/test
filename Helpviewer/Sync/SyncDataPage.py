# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the synchronization data wizard page.
"""

from PyQt4.QtGui import QWizardPage

from . import SyncGlobals

from .Ui_SyncDataPage import Ui_SyncDataPage

import Preferences


class SyncDataPage(QWizardPage, Ui_SyncDataPage):
    """
    Class implementing the synchronization data wizard page.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.bookmarksCheckBox.setChecked(Preferences.getHelp("SyncBookmarks"))
        self.historyCheckBox.setChecked(Preferences.getHelp("SyncHistory"))
        self.passwordsCheckBox.setChecked(Preferences.getHelp("SyncPasswords"))
        self.userAgentsCheckBox.setChecked(Preferences.getHelp("SyncUserAgents"))
        
        self.activeCheckBox.setChecked(Preferences.getHelp("SyncEnabled"))
    
    def nextId(self):
        """
        Public method returning the ID of the next wizard page.
        
        @return next wizard page ID (integer)
        """
        # save the settings
        Preferences.setHelp("SyncEnabled", self.activeCheckBox.isChecked())
        
        Preferences.setHelp("SyncBookmarks", self.bookmarksCheckBox.isChecked())
        Preferences.setHelp("SyncHistory", self.historyCheckBox.isChecked())
        Preferences.setHelp("SyncPasswords", self.passwordsCheckBox.isChecked())
        Preferences.setHelp("SyncUserAgents", self.userAgentsCheckBox.isChecked())
        
        if self.activeCheckBox.isChecked():
            return SyncGlobals.PageType
        else:
            return SyncGlobals.PageCheck
