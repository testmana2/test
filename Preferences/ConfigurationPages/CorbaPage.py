# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2009 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Corba configuration page.
"""

from PyQt4.QtCore import QDir, pyqtSlot
from PyQt4.QtGui import QFileDialog

from E4Gui.E4Completers import E4FileCompleter

from ConfigurationPageBase import ConfigurationPageBase
from Ui_CorbaPage import Ui_CorbaPage

import Preferences
import Utilities

class CorbaPage(ConfigurationPageBase, Ui_CorbaPage):
    """
    Class implementing the Corba configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("CorbaPage")
        
        self.idlCompleter = E4FileCompleter(self.idlEdit)
        
        # set initial values
        self.idlEdit.setText(Preferences.getCorba("omniidl"))
        
    def save(self):
        """
        Public slot to save the Corba configuration.
        """
        Preferences.setCorba("omniidl", self.idlEdit.text())
        
    @pyqtSlot()
    def on_idlButton_clicked(self):
        """
        Private slot to handle the IDL compiler selection.
        """
        file = QFileDialog.getOpenFileName(\
            self,
            self.trUtf8("Select IDL compiler"),
            self.idlEdit.text(),
            "")
        
        if file:
            self.idlEdit.setText(Utilities.toNativeSeparators(file))
    
def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = CorbaPage()
    return page
