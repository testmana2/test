# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing combobox classes using the eric5 line edits.
"""

from PyQt4.QtGui import QComboBox

from .E5LineEdit import E5LineEdit, E5ClearableLineEdit


class E5ComboBox(QComboBox):
    """
    Class implementing a combobox using the eric5 line edit.
    """
    def __init__(self, parent=None, inactiveText=""):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @param inactiveText text to be shown on inactivity (string)
        """
        super().__init__(parent)
        
        self.setMinimumHeight(24)
        
        self.__lineedit = E5LineEdit(self, inactiveText)
        self.setLineEdit(self.__lineedit)
        
        self.setMinimumHeight(self.__lineedit.minimumHeight() + 3)
    
    def inactiveText(self):
        """
        Public method to get the inactive text.
        
        return inactive text (string)
        """
        return self.__lineedit.inactiveText()
    
    def setInactiveText(self, inactiveText):
        """
        Public method to set the inactive text.
        
        @param inactiveText text to be shown on inactivity (string)
        """
        self.__lineedit.setInactiveText()


class E5ClearableComboBox(E5ComboBox):
    """
    Class implementing a combobox using the eric5 line edit.
    """
    def __init__(self, parent=None, inactiveText=""):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @param inactiveText text to be shown on inactivity (string)
        """
        super().__init__(parent, inactiveText)
        
        self.__lineedit = E5ClearableLineEdit(self, inactiveText)
        self.setLineEdit(self.__lineedit)
