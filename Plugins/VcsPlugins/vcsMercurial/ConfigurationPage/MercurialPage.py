# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Mercurial configuration page.
"""

from PyQt4.QtCore import pyqtSlot

from QScintilla.MiniEditor import MiniEditor

from Preferences.ConfigurationPages.ConfigurationPageBase import ConfigurationPageBase
from .Ui_MercurialPage import Ui_MercurialPage

class MercurialPage(ConfigurationPageBase, Ui_MercurialPage):
    """
    Class implementing the Mercurial configuration page.
    """
    def __init__(self, plugin):
        """
        Constructor
        
        @param plugin reference to the plugin object
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("MercurialPage")
        
        self.__plugin = plugin
        
        # set initial values
        self.logSpinBox.setValue(self.__plugin.getPreferences("LogLimit"))
        self.commitSpinBox.setValue(self.__plugin.getPreferences("CommitMessages"))
    
    def save(self):
        """
        Public slot to save the Mercurial configuration.
        """
        self.__plugin.setPreferences("LogLimit", self.logSpinBox.value())
        self.__plugin.setPreferences("CommitMessages", self.commitSpinBox.value())
    
    @pyqtSlot()
    def on_configButton_clicked(self):
        """
        Private slot to edit the (per user) Mercurial config file.
        """
        cfgFile = self.__plugin.getConfigPath()
        editor = MiniEditor(cfgFile, "Properties", self)
        editor.show()
