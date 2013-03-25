# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the add project dialog.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog

from .Ui_AddProjectDialog import Ui_AddProjectDialog

import Utilities


class AddProjectDialog(QDialog, Ui_AddProjectDialog):
    """
    Class implementing the add project dialog.
    """
    def __init__(self, parent=None, startdir=None, project=None):
        """
        Constructor
        
        @param parent parent widget of this dialog (QWidget)
        @param startdir start directory for the selection dialog (string)
        @param project dictionary containing project data
        """
        super(AddProjectDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.fileCompleter = E5FileCompleter(self.filenameEdit)
        
        self.startdir = startdir
        
        self.__okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.__okButton.setEnabled(False)
        
        if project is not None:
            self.setWindowTitle(self.trUtf8("Project Properties"))
            
            self.filenameEdit.setReadOnly(True)
            self.fileButton.setEnabled(False)
            
            self.nameEdit.setText(project['name'])
            self.filenameEdit.setText(project['file'])
            self.descriptionEdit.setPlainText(project['description'])
            self.masterCheckBox.setChecked(project['master'])
    
    @pyqtSlot()
    def on_fileButton_clicked(self):
        """
        Private slot to display a file selection dialog.
        """
        startdir = self.filenameEdit.text()
        if not startdir and self.startdir is not None:
            startdir = self.startdir
            projectFile = E5FileDialog.getOpenFileName(
                self,
                self.trUtf8("Add Project"),
                startdir,
                self.trUtf8("Project Files (*.e4p)"))
        
        if projectFile:
            self.filenameEdit.setText(Utilities.toNativeSeparators(projectFile))
    
    def getData(self):
        """
        Public slot to retrieve the dialogs data.
        
        @return tuple of four values (string, string, boolean, string) giving the
            project name, the name of the project file, a flag telling, whether
            the project shall be the master project and a short description
            for the project
        """
        return (self.nameEdit.text(), self.filenameEdit.text(),
                self.masterCheckBox.isChecked(),
                self.descriptionEdit.toPlainText())
    
    @pyqtSlot(str)
    def on_nameEdit_textChanged(self, p0):
        """
        Private slot called when the project name has changed.
        """
        self.__updateUi()
    
    @pyqtSlot(str)
    def on_filenameEdit_textChanged(self, p0):
        """
        Private slot called when the project filename has changed.
        """
        self.__updateUi()
    
    def __updateUi(self):
        """
        Private method to update the dialog.
        """
        self.__okButton.setEnabled(self.nameEdit.text() != "" and \
                                   self.filenameEdit.text() != "")
