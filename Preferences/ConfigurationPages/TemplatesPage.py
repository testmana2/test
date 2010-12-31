# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Templates configuration page.
"""

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_TemplatesPage import Ui_TemplatesPage

import Preferences

class TemplatesPage(ConfigurationPageBase, Ui_TemplatesPage):
    """
    Class implementing the Templates configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("TemplatesPage")
        
        # set initial values
        self.templatesAutoOpenGroupsCheckBox.setChecked(
            Preferences.getTemplates("AutoOpenGroups"))
        self.templatesSeparatorCharEdit.setText(
            Preferences.getTemplates("SeparatorChar"))
        if Preferences.getTemplates("SingleDialog"):
            self.templatesSingleDialogButton.setChecked(True)
        else:
            self.templatesMultiDialogButton.setChecked(True)
        self.templatesToolTipCheckBox.setChecked(
            Preferences.getTemplates("ShowTooltip"))
        
    def save(self):
        """
        Public slot to save the Templates configuration.
        """
        Preferences.setTemplates("AutoOpenGroups",
            self.templatesAutoOpenGroupsCheckBox.isChecked())
        sepChar = self.templatesSeparatorCharEdit.text()
        if sepChar:
            Preferences.setTemplates("SeparatorChar", sepChar)
        Preferences.setTemplates("SingleDialog",
            self.templatesSingleDialogButton.isChecked())
        Preferences.setTemplates("ShowTooltip",
            self.templatesToolTipCheckBox.isChecked())
    
def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = TemplatesPage()
    return page