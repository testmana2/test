# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Subversion Options Dialog for a new project from the
repository.
"""

import os

from PyQt4.QtCore import QDir, pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox

from E5Gui.E5Completers import E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_SvnNewProjectOptionsDialog import Ui_SvnNewProjectOptionsDialog
from .Config import ConfigSvnProtocols

import Utilities
import Preferences


class SvnNewProjectOptionsDialog(QDialog, Ui_SvnNewProjectOptionsDialog):
    """
    Class implementing the Options Dialog for a new project from the
    repository.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the version control object
        @param parent parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.vcsDirectoryCompleter = E5DirCompleter(self.vcsUrlEdit)
        self.vcsProjectDirCompleter = E5DirCompleter(self.vcsProjectDirEdit)
        
        self.protocolCombo.addItems(ConfigSvnProtocols)
        
        self.vcs = vcs
        
        hd = Utilities.toNativeSeparators(QDir.homePath())
        hd = os.path.join(hd, 'subversionroot')
        self.vcsUrlEdit.setText(hd)
        
        self.localPath = hd
        self.networkPath = "localhost/"
        self.localProtocol = True
        
        self.vcsProjectDirEdit.setText(Utilities.toNativeSeparators(
            Preferences.getMultiProject("Workspace") or
            Utilities.getHomeDir()))
        
    @pyqtSlot()
    def on_vcsUrlButton_clicked(self):
        """
        Private slot to display a selection dialog.
        """
        if self.protocolCombo.currentText() == "file://":
            directory = E5FileDialog.getExistingDirectory(
                self,
                self.trUtf8("Select Repository-Directory"),
                self.vcsUrlEdit.text(),
                E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
            
            if directory:
                self.vcsUrlEdit.setText(
                    Utilities.toNativeSeparators(directory))
        else:
            from .SvnRepoBrowserDialog import SvnRepoBrowserDialog
            dlg = SvnRepoBrowserDialog(self.vcs, mode="select", parent=self)
            dlg.start(
                self.protocolCombo.currentText() + self.vcsUrlEdit.text())
            if dlg.exec_() == QDialog.Accepted:
                url = dlg.getSelectedUrl()
                if url:
                    protocol = url.split("://")[0]
                    path = url.split("://")[1]
                    self.protocolCombo.setCurrentIndex(
                        self.protocolCombo.findText(protocol + "://"))
                    self.vcsUrlEdit.setText(path)
        
    @pyqtSlot()
    def on_projectDirButton_clicked(self):
        """
        Private slot to display a directory selection dialog.
        """
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.trUtf8("Select Project Directory"),
            self.vcsProjectDirEdit.text(),
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
        
        if directory:
            self.vcsProjectDirEdit.setText(
                Utilities.toNativeSeparators(directory))
        
    def on_layoutCheckBox_toggled(self, checked):
        """
        Private slot to handle the change of the layout checkbox.
        
        @param checked flag indicating the state of the checkbox (boolean)
        """
        self.vcsTagLabel.setEnabled(checked)
        self.vcsTagEdit.setEnabled(checked)
        if not checked:
            self.vcsTagEdit.clear()
        
    @pyqtSlot(str)
    def on_protocolCombo_activated(self, protocol):
        """
        Private slot to switch the status of the directory selection button.
        
        @param protocol selected protocol (string)
        """
        if protocol == "file://":
            self.networkPath = self.vcsUrlEdit.text()
            self.vcsUrlEdit.setText(self.localPath)
            self.vcsUrlLabel.setText(self.trUtf8("Pat&h:"))
            self.localProtocol = True
        else:
            if self.localProtocol:
                self.localPath = self.vcsUrlEdit.text()
                self.vcsUrlEdit.setText(self.networkPath)
                self.vcsUrlLabel.setText(self.trUtf8("&URL:"))
                self.localProtocol = False
    
    @pyqtSlot(str)
    def on_vcsUrlEdit_textChanged(self, txt):
        """
        Private slot to handle changes of the URL.
        
        @param txt current text of the line edit (string)
        """
        enable = "://" not in txt
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enable)
        
    def getData(self):
        """
        Public slot to retrieve the data entered into the dialog.
        
        @return a tuple of a string (project directory) and a dictionary
            containing the data entered.
        """
        scheme = self.protocolCombo.currentText()
        url = self.vcsUrlEdit.text()
        vcsdatadict = {
            "url": '{0}{1}'.format(scheme, url),
            "tag": self.vcsTagEdit.text(),
            "standardLayout": self.layoutCheckBox.isChecked(),
        }
        return (self.vcsProjectDirEdit.text(), vcsdatadict)
