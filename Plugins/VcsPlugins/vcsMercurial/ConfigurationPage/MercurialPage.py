# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Mercurial configuration page.
"""

import os

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog

from Preferences.ConfigurationPages.ConfigurationPageBase import \
    ConfigurationPageBase
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
        super().__init__()
        self.setupUi(self)
        self.setObjectName("MercurialPage")
        
        self.__plugin = plugin
        
        # set initial values
        self.logSpinBox.setValue(
            self.__plugin.getPreferences("LogLimit"))
        self.commitSpinBox.setValue(
            self.__plugin.getPreferences("CommitMessages"))
        self.logBrowserCheckBox.setChecked(
            self.__plugin.getPreferences("UseLogBrowser"))
        self.pullUpdateCheckBox.setChecked(
            self.__plugin.getPreferences("PullUpdate"))
        self.preferUnbundleCheckBox.setChecked(
            self.__plugin.getPreferences("PreferUnbundle"))
        self.cleanupPatternEdit.setText(
            self.__plugin.getPreferences("CleanupPatterns"))
        self.backupCheckBox.setChecked(
            self.__plugin.getPreferences("CreateBackup"))
    
    def save(self):
        """
        Public slot to save the Mercurial configuration.
        """
        self.__plugin.setPreferences(
            "LogLimit", self.logSpinBox.value())
        self.__plugin.setPreferences(
            "CommitMessages", self.commitSpinBox.value())
        self.__plugin.setPreferences(
            "UseLogBrowser", self.logBrowserCheckBox.isChecked())
        self.__plugin.setPreferences(
            "PullUpdate", self.pullUpdateCheckBox.isChecked())
        self.__plugin.setPreferences(
            "PreferUnbundle", self.preferUnbundleCheckBox.isChecked())
        self.__plugin.setPreferences(
            "CleanupPatterns", self.cleanupPatternEdit.text())
        self.__plugin.setPreferences(
            "CreateBackup", self.backupCheckBox.isChecked())
    
    @pyqtSlot()
    def on_configButton_clicked(self):
        """
        Private slot to edit the (per user) Mercurial configuration file.
        """
        from QScintilla.MiniEditor import MiniEditor
        cfgFile = self.__plugin.getConfigPath()
        if not os.path.exists(cfgFile):
            from ..HgUserConfigDataDialog import HgUserConfigDataDialog
            dlg = HgUserConfigDataDialog()
            if dlg.exec_() == QDialog.Accepted:
                firstName, lastName, email, extensions = dlg.getData()
            else:
                firstName, lastName, email, extensions = (
                    "Firstname", "Lastname", "email_address", [])
            try:
                f = open(cfgFile, "w")
                f.write("[ui]\n")
                f.write("username = {0} {1} <{2}>\n".format(
                    firstName, lastName, email))
                if extensions:
                    f.write("\n[extensions]\n")
                    f.write(" =\n".join(extensions))
                    f.write(" =\n")     # complete the last line
                f.close()
            except (IOError, OSError):
                # ignore these
                pass
        editor = MiniEditor(cfgFile, "Properties", self)
        editor.show()
