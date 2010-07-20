# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Network configuration page.
"""

import os

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QFileDialog

from E5Gui.E5Completers import E5DirCompleter

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_NetworkPage import Ui_NetworkPage

import Preferences
import Utilities

class NetworkPage(ConfigurationPageBase, Ui_NetworkPage):
    """
    Class implementing the Network configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("NetworkPage")
        
        self.downloadDirCompleter = E5DirCompleter(self.downloadDirEdit)
        
        # set initial values
        self.downloadDirEdit.setText(Preferences.getUI("DownloadPath"))
        self.requestFilenameCheckBox.setChecked(
            Preferences.getUI("RequestDownloadFilename"))
        
        self.proxyGroup.setChecked(\
            Preferences.getUI("UseProxy"))
        if Preferences.getUI("UseSystemProxy"):
            self.systemProxyButton.setChecked(True)
        else:
            self.manualProxyButton.setChecked(True)
        self.httpProxyForAllCheckBox.setChecked(
            Preferences.getUI("UseHttpProxyForAll"))
        self.httpProxyHostEdit.setText(\
            Preferences.getUI("ProxyHost/Http"))
        self.httpsProxyHostEdit.setText(\
            Preferences.getUI("ProxyHost/Https"))
        self.ftpProxyHostEdit.setText(\
            Preferences.getUI("ProxyHost/Ftp"))
        self.httpProxyPortSpin.setValue(\
            Preferences.getUI("ProxyPort/Http"))
        self.httpsProxyPortSpin.setValue(\
            Preferences.getUI("ProxyPort/Https"))
        self.ftpProxyPortSpin.setValue(\
            Preferences.getUI("ProxyPort/Ftp"))
        
    def save(self):
        """
        Public slot to save the Application configuration.
        """
        Preferences.setUI("DownloadPath", 
            self.downloadDirEdit.text())
        Preferences.setUI("RequestDownloadFilename", 
            self.requestFilenameCheckBox.isChecked())
        
        Preferences.setUI("UseProxy",
            self.proxyGroup.isChecked())
        Preferences.setUI("UseSystemProxy", 
            self.systemProxyButton.isChecked())
        Preferences.setUI("UseHttpProxyForAll", 
            self.httpProxyForAllCheckBox.isChecked())
        Preferences.setUI("ProxyHost/Http",
            self.httpProxyHostEdit.text())
        Preferences.setUI("ProxyHost/Https",
            self.httpsProxyHostEdit.text())
        Preferences.setUI("ProxyHost/Ftp",
            self.ftpProxyHostEdit.text())
        Preferences.setUI("ProxyPort/Http",
            self.httpProxyPortSpin.value())
        Preferences.setUI("ProxyPort/Https",
            self.httpsProxyPortSpin.value())
        Preferences.setUI("ProxyPort/Ftp",
            self.ftpProxyPortSpin.value())
    
    @pyqtSlot()
    def on_downloadDirButton_clicked(self):
        """
        Private slot to handle the directory selection via dialog.
        """
        directory = QFileDialog.getExistingDirectory(\
            self,
            self.trUtf8("Select download directory"),
            self.downloadDirEdit.text(),
            QFileDialog.Options(QFileDialog.ShowDirsOnly))
            
        if directory:
            dn = Utilities.toNativeSeparators(directory)
            while dn.endswith(os.sep):
                dn = dn[:-1]
            self.downloadDirEdit.setText(dn)
    
def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = NetworkPage()
    return page
