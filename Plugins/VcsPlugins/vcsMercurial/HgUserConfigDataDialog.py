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
        
        @param version Mercurial version info (tuple of two integers)
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
        
        @return tuple with user's first name, last name, email address,
            list of activated extensions and dictionary with extension data
            (tuple of three strings, a list of strings and a dictionary with
             extension name as key)
        """
        extensions = []
        extensionsData = {}
        
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
        if self.shelveCheckBox.isChecked():
            extensions.append("shelve")
        if self.transplantCheckBox.isChecked():
            extensions.append("transplant")
        if self.largefilesCheckBox.isChecked():
            extensions.append("largefiles")
            largefilesDataDict = {}
            lfFileSize = self.lfFileSizeSpinBox.value()
            if lfFileSize != 10:        # default value is 10 MB
                largefilesDataDict["minsize"] = lfFileSize
            lfFilePatterns = self.lfFilePatternsEdit.text()
            if lfFilePatterns:
                largefilesDataDict["patterns"] = lfFilePatterns.split()
            if largefilesDataDict:
                extensionsData["largefiles"] = largefilesDataDict
        
        return (
            self.firstNameEdit.text(),
            self.lastNameEdit.text(),
            self.emailEdit.text(),
            extensions,
            extensionsData,
        )
