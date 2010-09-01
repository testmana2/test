# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Mercurial Options Dialog for a new project from the repository.
"""

import os

from PyQt4.QtCore import pyqtSlot, QDir
from PyQt4.QtGui import QDialog, QFileDialog

from E5Gui.E5Completers import E5DirCompleter

from .Ui_HgNewProjectOptionsDialog import Ui_HgNewProjectOptionsDialog
from .Config import ConfigHgProtocols

import Utilities

class HgNewProjectOptionsDialog(QDialog, Ui_HgNewProjectOptionsDialog):
    """
    Class implementing the Options Dialog for a new project from the repository.
    """
    def __init__(self, vcs, parent = None):
        """
        Constructor
        
        @param vcs reference to the version control object
        @param parent parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.vcsDirectoryCompleter = E5DirCompleter(self.vcsUrlEdit)
        self.vcsProjectDirCompleter = E5DirCompleter(self.vcsProjectDirEdit)
        
        self.protocolCombo.addItems(ConfigHgProtocols)
        
        hd = Utilities.toNativeSeparators(QDir.homePath())
        hd = os.path.join(hd, 'hgroot')
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
            directory = QFileDialog.getExistingDirectory(\
                self,
                self.trUtf8("Select Repository-Directory"),
                self.vcsUrlEdit.text(),
                QFileDialog.Options(QFileDialog.ShowDirsOnly))
            
            if directory:
                self.vcsUrlEdit.setText(Utilities.toNativeSeparators(directory))
    
    @pyqtSlot()
    def on_projectDirButton_clicked(self):
        """
        Private slot to display a directory selection dialog.
        """
        directory = QFileDialog.getExistingDirectory(\
            self,
            self.trUtf8("Select Project Directory"),
            self.vcsProjectDirEdit.text(),
            QFileDialog.Options(QFileDialog.ShowDirsOnly))
        
        if directory:
            self.vcsProjectDirEdit.setText(Utilities.toNativeSeparators(directory))
    
    @pyqtSlot(str)
    def on_protocolCombo_activated(self, protocol):
        """
        Private slot to switch the status of the directory selection button.
        
        @param protocol name of the selected protocol (string)
        """
        self.vcsUrlButton.setEnabled(protocol == "file://")
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
        
        @return a tuple of a string (project directory) and a dictionary
            containing the data entered.
        """
        scheme = self.protocolCombo.currentText()
        url = self.vcsUrlEdit.text()
        if scheme == "file://" and url[0] not in ["\\", "/"]:
            url = "/{0}".format(url)
        vcsdatadict = {
            "url" : '{0}{1}'.format(scheme, url),
            "revision" : self.vcsRevisionEdit.text(), 
        }
        return (self.vcsProjectDirEdit.text(), vcsdatadict)
