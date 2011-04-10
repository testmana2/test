# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing HelpVirusTotalPage.
"""

from PyQt4.QtCore import pyqtSlot

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_HelpVirusTotalPage import Ui_HelpVirusTotalPage

from Helpviewer.VirusTotalApi import VirusTotalAPI

import Preferences


class HelpVirusTotalPage(ConfigurationPageBase, Ui_HelpVirusTotalPage):
    """
    Class documentation goes here.
    """
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("HelpVirusTotalPage")
        
        self.testResultLabel.setHidden(True)
        
        # set initial values
        self.vtEnabledCheckBox.setChecked(
            Preferences.getHelp("VirusTotalEnabled"))
        self.vtSecureCheckBox.setChecked(
            Preferences.getHelp("VirusTotalSecure"))
        self.vtServiceKeyEdit.setText(
            Preferences.getHelp("VirusTotalServiceKey"))
        
    
    def save(self):
        """
        Public slot to save the VirusTotal configuration.
        """
        Preferences.setHelp("VirusTotalEnabled", 
            self.vtEnabledCheckBox.isChecked())
        Preferences.setHelp("VirusTotalSecure", 
            self.vtSecureCheckBox.isChecked())
        Preferences.setHelp("VirusTotalServiceKey", 
            self.vtServiceKeyEdit.text())
    
    @pyqtSlot(str)
    def on_vtServiceKeyEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the service key.
        
        @param txt entered service key (string)
        """
        self.testButton.setEnabled(txt != "")
    
    @pyqtSlot()
    def on_testButton_clicked(self):
        """
        Private slot to test the entered service key.
        """
        self.testResultLabel.setHidden(False)
        self.testResultLabel.setText(
            self.trUtf8("Checking validity of the service key..."))
        vt = VirusTotalAPI(self)
        if self.vtSecureCheckBox.isChecked():
            protocol = "https"
        else:
            protocol = "http"
        result, msg = vt.checkServiceKeyValidity(self.vtServiceKeyEdit.text(), protocol)
        if result:
            self.testResultLabel.setText(self.trUtf8("The service key is valid."))
        else:
            if msg == "":
                self.testResultLabel.setText(self.trUtf8(
                    '<font color="#FF0000">The service key is not valid.</font>'))
            else:
                self.testResultLabel.setText(self.trUtf8(
                    '<font color="#FF0000"><b>Error:</b> {0}</font>').format(msg))
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = HelpVirusTotalPage(dlg)
    return page
