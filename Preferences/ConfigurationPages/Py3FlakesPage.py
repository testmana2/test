# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Py3Flakes configuration page.
"""

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_Py3FlakesPage import Ui_Py3FlakesPage

import Preferences

class Py3FlakesPage(ConfigurationPageBase, Ui_Py3FlakesPage):
    """
    Class implementing the Python configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("Py3FlakesPage")
        
        # set initial values
        self.includeCheckBox.setChecked(
            Preferences.getFlakes("IncludeInSyntaxCheck"))
        self.ignoreStarImportCheckBox.setChecked(
            Preferences.getFlakes("IgnoreStarImportWarnings"))
    
    def save(self):
        """
        Public slot to save the Python configuration.
        """
        Preferences.setFlakes("IncludeInSyntaxCheck", 
            self.includeCheckBox.isChecked())
        Preferences.setFlakes("IgnoreStarImportWarnings", 
            self.ignoreStarImportCheckBox.isChecked())
    
def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = Py3FlakesPage()
    return page
