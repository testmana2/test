# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Debugger Python3 configuration page.
"""

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QFileDialog

from E5Gui.E5Completers import E5FileCompleter

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_DebuggerPython3Page import Ui_DebuggerPython3Page

import Preferences
import Utilities

class DebuggerPython3Page(ConfigurationPageBase, Ui_DebuggerPython3Page):
    """
    Class implementing the Debugger Python3 configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("DebuggerPython3Page")
        
        self.interpreterCompleter = E5FileCompleter(self.interpreterEdit)
        self.debugClientCompleter = E5FileCompleter(self.debugClientEdit)
        
        # set initial values
        self.customPyCheckBox.setChecked(\
            Preferences.getDebugger("CustomPython3Interpreter"))
        self.interpreterEdit.setText(\
            Preferences.getDebugger("Python3Interpreter"))
        dct = Preferences.getDebugger("DebugClientType3")
        if dct == "standard":
            self.standardButton.setChecked(True)
        elif dct == "threaded":
            self.threadedButton.setChecked(True)
        else:
            self.customButton.setChecked(True)
        self.debugClientEdit.setText(
            Preferences.getDebugger("DebugClient3"))
        self.pyRedirectCheckBox.setChecked(
            Preferences.getDebugger("Python3Redirect"))
        self.pyNoEncodingCheckBox.setChecked(
            Preferences.getDebugger("Python3NoEncoding"))
        self.sourceExtensionsEdit.setText(
            Preferences.getDebugger("Python3Extensions"))
        
    def save(self):
        """
        Public slot to save the Debugger Python configuration.
        """
        Preferences.setDebugger("CustomPython3Interpreter", 
            self.customPyCheckBox.isChecked())
        Preferences.setDebugger("Python3Interpreter", 
            self.interpreterEdit.text())
        if self.standardButton.isChecked():
            dct = "standard"
        elif self.threadedButton.isChecked():
            dct = "threaded"
        else:
            dct = "custom"
        Preferences.setDebugger("DebugClientType3", dct)
        Preferences.setDebugger("DebugClient3", 
            self.debugClientEdit.text())
        Preferences.setDebugger("Python3Redirect", 
            self.pyRedirectCheckBox.isChecked())
        Preferences.setDebugger("Python3NoEncoding", 
            self.pyNoEncodingCheckBox.isChecked())
        Preferences.setDebugger("Python3Extensions", 
            self.sourceExtensionsEdit.text())
        
    @pyqtSlot()
    def on_interpreterButton_clicked(self):
        """
        Private slot to handle the Python interpreter selection.
        """
        file = QFileDialog.getOpenFileName(\
            self,
            self.trUtf8("Select Python interpreter for Debug Client"),
            self.interpreterEdit.text(),
            "")
            
        if file:
            self.interpreterEdit.setText(\
                Utilities.toNativeSeparators(file))
        
    @pyqtSlot()
    def on_debugClientButton_clicked(self):
        """
        Private slot to handle the Debug Client selection.
        """
        file = QFileDialog.getOpenFileName(\
            None,
            self.trUtf8("Select Debug Client"),
            self.debugClientEdit.text(),
            self.trUtf8("Python Files (*.py *.py3)"))
            
        if file:
            self.debugClientEdit.setText(\
                Utilities.toNativeSeparators(file))
    
def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = DebuggerPython3Page()
    return page
