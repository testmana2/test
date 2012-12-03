# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to configure the various view profiles.
"""

from PyQt4.QtGui import QDialog

from .Ui_ViewProfileToolboxesDialog import Ui_ViewProfileToolboxesDialog
from .Ui_ViewProfileSidebarsDialog import Ui_ViewProfileSidebarsDialog


class ViewProfileDialog(QDialog):
    """
    Class implementing a dialog to configure the various view profiles.
    """
    def __init__(self, layout, profiles, separateShell, separateBrowser, parent=None):
        """
        Constructor
        
        @param layout type of the window layout (string)
        @param profiles dictionary of tuples containing the visibility
            of the windows for the various profiles
        @param separateShell flag indicating that the Python shell
            is a separate window (boolean)
        @param separateBrowser flag indicating that the file browser
            is a separate window (boolean)
        @param parent parent widget of this dialog (QWidget)
        """
        super().__init__(parent)
        
        self.__layout = layout
        if self.__layout == "Toolboxes":
            self.ui = Ui_ViewProfileToolboxesDialog()
        elif self.__layout == "Sidebars":
            self.ui = Ui_ViewProfileSidebarsDialog()
        else:
            raise ValueError("Illegal layout given ({0}).".format(self.__layout))
        self.ui.setupUi(self)
        
        self.profiles = profiles
        
        if self.__layout in ["Toolboxes", "Sidebars"]:
            # set the edit profile
            profile = self.profiles["edit"][5]
            self.ui.epltCheckBox.setChecked(profile[0])
            self.ui.ephtCheckBox.setChecked(profile[1])
            self.ui.eprtCheckBox.setChecked(profile[2])
        
            # set the debug profile
            profile = self.profiles["debug"][5]
            self.ui.dpltCheckBox.setChecked(profile[0])
            self.ui.dphtCheckBox.setChecked(profile[1])
            self.ui.dprtCheckBox.setChecked(profile[2])
    
    def getProfiles(self):
        """
        Public method to retrieve the configured profiles.
        
        @return dictionary of tuples containing the visibility
            of the windows for the various profiles
        """
        if self.__layout in ["Toolboxes", "Sidebars"]:
            # get the edit profile
            self.profiles["edit"][5] = [
                self.ui.epltCheckBox.isChecked(),
                self.ui.ephtCheckBox.isChecked(),
                self.ui.eprtCheckBox.isChecked(),
            ]
            # get the debug profile
            self.profiles["debug"][5] = [
                self.ui.dpltCheckBox.isChecked(),
                self.ui.dphtCheckBox.isChecked(),
                self.ui.dprtCheckBox.isChecked(),
            ]
        
        return self.profiles
