# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the add project dialog.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox

from E5Gui.E5Completers import E5FileCompleter
from E5Gui import E5FileDialog

from .Ui_AddProjectDialog import Ui_AddProjectDialog

import Utilities
import UI.PixmapCache


class AddProjectDialog(QDialog, Ui_AddProjectDialog):
    """
    Class implementing the add project dialog.
    """
    def __init__(self, parent=None, startdir=None, project=None,
                 categories=None):
        """
        Constructor
        
        @param parent parent widget of this dialog (QWidget)
        @param startdir start directory for the selection dialog (string)
        @param project dictionary containing project data
        @param categories list of already used categories (list of string)
        """
        super(AddProjectDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.fileButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        
        self.fileCompleter = E5FileCompleter(self.filenameEdit)
        
        if categories:
            self.categoryComboBox.addItem("")
            self.categoryComboBox.addItems(sorted(categories))
        
        self.startdir = startdir
        
        self.__okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.__okButton.setEnabled(False)
        
        if project is not None:
            self.setWindowTitle(self.tr("Project Properties"))
            
            self.filenameEdit.setReadOnly(True)
            self.fileButton.setEnabled(False)
            
            self.nameEdit.setText(project['name'])
            self.filenameEdit.setText(project['file'])
            self.descriptionEdit.setPlainText(project['description'])
            self.masterCheckBox.setChecked(project['master'])
            index = self.categoryComboBox.findText(project['category'])
            if index == -1:
                index = 0
            self.categoryComboBox.setCurrentIndex(index)
    
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
                self.tr("Add Project"),
                startdir,
                self.tr("Project Files (*.e4p)"))
            
            if projectFile:
                self.filenameEdit.setText(
                    Utilities.toNativeSeparators(projectFile))
    
    def getData(self):
        """
        Public slot to retrieve the dialogs data.
        
        @return tuple of five values (string, string, boolean, string, string)
            giving the project name, the name of the project file, a flag
            telling whether the project shall be the main project, a short
            description for the project and the project category
        """
        return (self.nameEdit.text(),
                self.filenameEdit.text(),
                self.masterCheckBox.isChecked(),
                self.descriptionEdit.toPlainText(),
                self.categoryComboBox.currentText())
    
    @pyqtSlot(str)
    def on_nameEdit_textChanged(self, txt):
        """
        Private slot called when the project name has changed.
        
        @param txt text of the edit (string)
        """
        self.__updateUi()
    
    @pyqtSlot(str)
    def on_filenameEdit_textChanged(self, txt):
        """
        Private slot called when the project filename has changed.
        
        @param txt text of the edit (string)
        """
        self.__updateUi()
    
    def __updateUi(self):
        """
        Private method to update the dialog.
        """
        self.__okButton.setEnabled(self.nameEdit.text() != "" and
                                   self.filenameEdit.text() != "")
