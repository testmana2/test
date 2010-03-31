# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Cooperation configuration page.
"""

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_CooperationPage import Ui_CooperationPage

import Preferences

class CooperationPage(ConfigurationPageBase, Ui_CooperationPage):
    """
    Class implementing the Cooperation configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("CooperationPage")
        
        # set initial values
        self.autostartCheckBox.setChecked(
            Preferences.getCooperation("AutoStartServer"))
        self.otherPortsCheckBox.setChecked(
            Preferences.getCooperation("TryOtherPorts"))
        self.serverPortSpin.setValue(
            Preferences.getCooperation("ServerPort"))
        self.portToTrySpin.setValue(
            Preferences.getCooperation("MaxPortsToTry"))
        self.autoAcceptCheckBox.setChecked(
            Preferences.getCooperation("AutoAcceptConnections"))
    
    def save(self):
        """
        Public slot to save the Cooperation configuration.
        """
        Preferences.setCooperation("AutoStartServer", 
            self.autostartCheckBox.isChecked())
        Preferences.setCooperation("TryOtherPorts", 
            self.otherPortsCheckBox.isChecked())
        Preferences.setCooperation("AutoAcceptConnections", 
            self.autoAcceptCheckBox.isChecked())
        Preferences.setCooperation("ServerPort", 
            self.serverPortSpin.value())
        Preferences.setCooperation("MaxPortsToTry", 
            self.portToTrySpin.value())
    
def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = CooperationPage()
    return page
