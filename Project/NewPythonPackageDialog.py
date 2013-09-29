# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to add a new Python package.
"""

from PyQt4.QtGui import QDialog, QDialogButtonBox
from PyQt4.QtCore import pyqtSlot

from .Ui_NewPythonPackageDialog import Ui_NewPythonPackageDialog


class NewPythonPackageDialog(QDialog, Ui_NewPythonPackageDialog):
    """
    Class implementing a dialog to add a new Python package.
    """
    def __init__(self, relPath, parent=None):
        """
        Constructor
        
        @param relPath initial package path relative to the project root
            (string)
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.setEnabled(False)
        
        rp = relPath.replace("/", ".").replace("\\", ".")
        self.packageEdit.setText(rp)
    
    @pyqtSlot(str)
    def on_packageEdit_textChanged(self, txt):
        """
        Private slot called, when the package name is changed.
        
        @param txt new text of the package name edit (string)
        """
        self.okButton.setEnabled(txt != "")
    
    def getData(self):
        """
        Public method to retrieve the data entered into the dialog.
        
        @return package name (string)
        """
        return self.packageEdit.text()
