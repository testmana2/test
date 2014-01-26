# -*- coding: utf-8 -*-

"""
Module implementing a dialog to enter some user data.
"""

from PyQt4.QtGui import QDialog

from .Ui_HgUserConfigDataDialog import Ui_HgUserConfigDataDialog


class HgUserConfigDataDialog(QDialog, Ui_HgUserConfigDataDialog):
    """
    Class implementing a dialog to enter some user data.
    """
    def __init__(self, version=(0, 0), parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        if version >= (1, 8):
            self.bookmarksCheckBox.setEnabled(False)
        if version >= (2, 3):
            self.transplantCheckBox.setEnabled(False)
        
        self.resize(self.width(), self.minimumSizeHint().height())
    
    def getData(self):
        """
        Public method to retrieve the entered data.
        
        @return tuple with user's first name, last name, email address and
            list of activated extensions (tuple of three strings and a list
            of strings)
        """
        extensions = []
        
        if self.bookmarksCheckBox.isChecked():
            extensions.append("bookmarks")
        if self.fetchCheckBox.isChecked():
            extensions.append("fetch")
        if self.gpgCheckBox.isChecked():
            extensions.append("gpg")
        if self.purgeCheckBox.isChecked():
            extensions.append("purge")
        if self.queuesCheckBox.isChecked():
            extensions.append("mq")
        if self.rebaseCheckBox.isChecked():
            extensions.append("rebase")
        if self.transplantCheckBox.isChecked():
            extensions.append("transplant")
        
        return (
            self.firstNameEdit.text(),
            self.lastNameEdit.text(),
            self.emailEdit.text(),
            extensions,
        )
