# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter options used to start a project in the VCS.
"""

import os

from PyQt4.QtCore import QDir, pyqtSlot
from PyQt4.QtGui import QDialog

from E5Gui.E5Completers import E5DirCompleter
from E5Gui import E5FileDialog

from .SvnRepoBrowserDialog import SvnRepoBrowserDialog
from .Ui_SvnOptionsDialog import Ui_SvnOptionsDialog
from .Config import ConfigSvnProtocols

import Utilities


class SvnOptionsDialog(QDialog, Ui_SvnOptionsDialog):
    """
    Class implementing a dialog to enter options used to start a project in the
    repository.
    """
    def __init__(self, vcs, project, parent=None):
        """
        Constructor
        
        @param vcs reference to the version control object
        @param project reference to the project object
        @param parent parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.vcsDirectoryCompleter = E5DirCompleter(self.vcsUrlEdit)
        
        self.project = project
        
        self.protocolCombo.addItems(ConfigSvnProtocols)
        
        hd = Utilities.toNativeSeparators(QDir.homePath())
        hd = os.path.join(hd, 'subversionroot')
        self.vcsUrlEdit.setText(hd)
        
        self.vcs = vcs
        
        self.localPath = hd
        self.networkPath = "localhost/"
        self.localProtocol = True
        
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
                self.vcsUrlEdit.setText(Utilities.toNativeSeparators(directory))
        else:
            dlg = SvnRepoBrowserDialog(self.vcs, mode="select", parent=self)
            dlg.start(self.protocolCombo.currentText() + self.vcsUrlEdit.text())
            if dlg.exec_() == QDialog.Accepted:
                url = dlg.getSelectedUrl()
                if url:
                    protocol = url.split("://")[0]
                    path = url.split("://")[1]
                    self.protocolCombo.setCurrentIndex(
                        self.protocolCombo.findText(protocol + "://"))
                    self.vcsUrlEdit.setText(path)
        
    @pyqtSlot(str)
    def on_protocolCombo_activated(self, protocol):
        """
        Private slot to switch the status of the directory selection button.
        """
        if protocol == "file://":
            self.networkPath = self.vcsUrlEdit.text()
            self.vcsUrlEdit.setText(self.localPath)
            self.localProtocol = True
        else:
            if self.localProtocol:
                self.localPath = self.vcsUrlEdit.text()
                self.vcsUrlEdit.setText(self.networkPath)
                self.localProtocol = False
        
    def getData(self):
        """
        Public slot to retrieve the data entered into the dialog.
        
        @return a dictionary containing the data entered
        """
        scheme = self.protocolCombo.currentText()
        url = self.vcsUrlEdit.text()
        if scheme == "file://" and url[0] not in ["\\", "/"]:
            url = "/{0}".format(url)
        vcsdatadict = {
            "url": '{0}{1}'.format(scheme, url),
            "message": self.vcsLogEdit.text(),
            "standardLayout": self.layoutCheckBox.isChecked(),
        }
        return vcsdatadict
