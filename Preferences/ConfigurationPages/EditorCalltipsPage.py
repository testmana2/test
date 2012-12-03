# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor Calltips configuration page.
"""

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorCalltipsPage import Ui_EditorCalltipsPage

import Preferences


class EditorCalltipsPage(ConfigurationPageBase, Ui_EditorCalltipsPage):
    """
    Class implementing the Editor Calltips configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.setObjectName("EditorCalltipsPage")
        
        # set initial values
        self.ctEnabledCheckBox.setChecked(
            Preferences.getEditor("CallTipsEnabled"))
        
        self.ctVisibleSlider.setValue(
            Preferences.getEditor("CallTipsVisible"))
        self.initColour("CallTipsBackground", self.calltipsBackgroundButton,
            Preferences.getEditorColour)
        
        self.ctScintillaCheckBox.setChecked(
            Preferences.getEditor("CallTipsScintillaOnFail"))
        
    def save(self):
        """
        Public slot to save the EditorCalltips configuration.
        """
        Preferences.setEditor("CallTipsEnabled",
            self.ctEnabledCheckBox.isChecked())
        
        Preferences.setEditor("CallTipsVisible",
            self.ctVisibleSlider.value())
        self.saveColours(Preferences.setEditorColour)
        
        Preferences.setEditor("CallTipsScintillaOnFail",
            self.ctScintillaCheckBox.isChecked())


def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = EditorCalltipsPage()
    return page
