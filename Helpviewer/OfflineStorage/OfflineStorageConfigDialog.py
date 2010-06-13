# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to configure the offline storage.
"""

from PyQt4.QtGui import QDialog

from .Ui_OfflineStorageConfigDialog import Ui_OfflineStorageConfigDialog

import Preferences

class OfflineStorageConfigDialog(QDialog, Ui_OfflineStorageConfigDialog):
    """
    Class implementing a dialog to configure the offline storage.
    """
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.databaseEnabledCheckBox.setChecked(
            Preferences.getHelp("OfflineStorageDatabaseEnabled"))
        self.databaseQuotaSpinBox.setValue(
            Preferences.getHelp("OfflineStorageDatabaseQuota"))
    
    def storeData(self):
        """
        Public slot to store the configuration data.
        """
        Preferences.setHelp("OfflineStorageDatabaseEnabled", 
            self.databaseEnabledCheckBox.isChecked())
        Preferences.setHelp("OfflineStorageDatabaseQuota", 
            self.databaseQuotaSpinBox.value())
