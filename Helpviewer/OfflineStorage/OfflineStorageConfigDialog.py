# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to configure the offline storage.
"""

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog
from PyQt4.QtWebKit import QWebSettings

from .WebDatabasesDialog import WebDatabasesDialog
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
        
        if hasattr(QWebSettings, "OfflineWebApplicationCacheEnabled"):
            self.applicationCacheEnabledCheckBox.setChecked(
                Preferences.getHelp("OfflineWebApplicationCacheEnabled"))
            self.applicationCacheQuotaSpinBox.setValue(
                Preferences.getHelp("OfflineWebApplicationCacheQuota"))
        else:
            self.applicationCacheGroup.setEnabled(False)
        
        if hasattr(QWebSettings, "LocalStorageEnabled"):
            self.localStorageEnabledCheckBox.setChecked(
                Preferences.getHelp("LocalStorageEnabled"))
        else:
            self.localStorageGroup.setEnabled(False)
    
    def storeData(self):
        """
        Public slot to store the configuration data.
        """
        Preferences.setHelp("OfflineStorageDatabaseEnabled", 
            self.databaseEnabledCheckBox.isChecked())
        Preferences.setHelp("OfflineStorageDatabaseQuota", 
            self.databaseQuotaSpinBox.value())
        
        if self.applicationCacheGroup.isEnabled():
            Preferences.setHelp("OfflineWebApplicationCacheEnabled", 
                self.applicationCacheEnabledCheckBox.isChecked())
            Preferences.setHelp("OfflineWebApplicationCacheQuota", 
                self.applicationCacheQuotaSpinBox.value())
        
        if self.localStorageGroup.isEnabled():
            Preferences.setHelp("LocalStorageEnabled", 
                self.localStorageEnabledCheckBox.isChecked())
    
    @pyqtSlot()
    def on_showDatabasesButton_clicked(self):
        """
        Private slot to show a dialog with all databases.
        """
        dlg = WebDatabasesDialog(self)
        dlg.exec_()