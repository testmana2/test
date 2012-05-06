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
        
        # set the editor profile
        profile = self.profiles["edit"][0]
        self.ui.epdbCheckBox.setChecked(profile[2])
        self.ui.epcoCheckBox.setChecked(profile[9])
        if self.__layout in ["Toolboxes", "Sidebars"]:
            profile = self.profiles["edit"][5]
            self.ui.epvtCheckBox.setChecked(profile[0])
            self.ui.ephtCheckBox.setChecked(profile[1])
        
        # set the debug profile
        profile = self.profiles["debug"][0]
        self.ui.dpdbCheckBox.setChecked(profile[2])
        self.ui.dpcoCheckBox.setChecked(profile[9])
        if self.__layout in ["Toolboxes", "Sidebars"]:
            profile = self.profiles["edit"][5]
            self.ui.dpvtCheckBox.setChecked(profile[0])
            self.ui.dphtCheckBox.setChecked(profile[1])
    
    def getProfiles(self):
        """
        Public method to retrieve the configured profiles.
        
        @return dictionary of tuples containing the visibility
            of the windows for the various profiles
        """
        if self.__layout in ["Toolboxes", "Sidebars"]:
            # get the edit profile
            self.profiles["edit"][0][2] = self.ui.epdbCheckBox.isChecked()
            self.profiles["edit"][0][9] = self.ui.epcoCheckBox.isChecked()
            self.profiles["edit"][5] = [
                self.ui.epvtCheckBox.isChecked(),
                self.ui.ephtCheckBox.isChecked(),
            ]
            # get the debug profile
            self.profiles["debug"][0][2] = self.ui.dpdbCheckBox.isChecked()
            self.profiles["debug"][0][9] = self.ui.dpcoCheckBox.isChecked()
            self.profiles["debug"][5] = [
                self.ui.dpvtCheckBox.isChecked(),
                self.ui.dphtCheckBox.isChecked(),
            ]
        
        return self.profiles
