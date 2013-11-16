# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to add files of a directory to the project.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog

from E5Gui.E5Completers import E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_AddDirectoryDialog import Ui_AddDirectoryDialog

import Utilities


class AddDirectoryDialog(QDialog, Ui_AddDirectoryDialog):
    """
    Class implementing a dialog to add files of a directory to the project.
    """
    def __init__(self, pro, filter='source', parent=None, name=None,
                 startdir=None):
        """
        Constructor
        
        @param pro reference to the project object
        @param filter file type filter (string)
        @param parent parent widget of this dialog (QWidget)
        @param name name of this dialog (string)
        @param startdir start directory for the selection dialog
        """
        super(AddDirectoryDialog, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.setupUi(self)
        
        self.sourceDirCompleter = E5DirCompleter(self.sourceDirEdit)
        self.targetDirCompleter = E5DirCompleter(self.targetDirEdit)
        
        self.ppath = pro.ppath
        self.targetDirEdit.setText(self.ppath)
        self.startdir = startdir
        self.on_filterComboBox_highlighted('(*.py)')
        # enable all dialog elements
        if filter == 'source':  # it is a source file
            self.filterComboBox.addItem(
                self.trUtf8("Source Files"), "SOURCES")
        elif filter == 'form':
            self.filterComboBox.addItem(
                self.trUtf8("Forms Files"), "FORMS")
        elif filter == 'resource':
            self.filterComboBox.addItem(
                self.trUtf8("Resource Files"), "RESOURCES")
        elif filter == 'interface':
            self.filterComboBox.addItem(
                self.trUtf8("Interface Files"), "INTERFACES")
        elif filter == 'others':
            self.filterComboBox.addItem(
                self.trUtf8("Other Files (*)"), "OTHERS")
            self.on_filterComboBox_highlighted('(*)')
        else:
            self.filterComboBox.addItem(
                self.trUtf8("Source Files"), "SOURCES")
            self.filterComboBox.addItem(
                self.trUtf8("Forms Files"), "FORMS")
            self.filterComboBox.addItem(
                self.trUtf8("Resource Files"), "RESOURCES")
            self.filterComboBox.addItem(
                self.trUtf8("Interface Files"), "INTERFACES")
            self.filterComboBox.addItem(
                self.trUtf8("Other Files (*)"), "OTHERS")
        self.filterComboBox.setCurrentIndex(0)
        
    @pyqtSlot(str)
    def on_filterComboBox_highlighted(self, fileType):
        """
        Private slot to handle the selection of a file type.
        
        @param fileType the selected file type (string)
        """
        if fileType.endswith('(*)'):
            self.targetDirLabel.setEnabled(False)
            self.targetDirEdit.setEnabled(False)
            self.targetDirButton.setEnabled(False)
            self.recursiveCheckBox.setEnabled(False)
        else:
            self.targetDirLabel.setEnabled(True)
            self.targetDirEdit.setEnabled(True)
            self.targetDirButton.setEnabled(True)
            self.recursiveCheckBox.setEnabled(True)
        
    def __dirDialog(self, textEdit):
        """
        Private slot to display a directory selection dialog.
        
        @param textEdit field for the display of the selected directory name
            (QLineEdit)
        """
        startdir = textEdit.text()
        if not startdir and self.startdir is not None:
            startdir = self.startdir
        
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.trUtf8("Select directory"),
            startdir)
        
        if directory:
            textEdit.setText(Utilities.toNativeSeparators(directory))
        
    @pyqtSlot()
    def on_sourceDirButton_clicked(self):
        """
        Private slot to handle the source dir button press.
        """
        self.__dirDialog(self.sourceDirEdit)
        
    @pyqtSlot()
    def on_targetDirButton_clicked(self):
        """
        Private slot to handle the target dir button press.
        """
        self.__dirDialog(self.targetDirEdit)
        
    @pyqtSlot(str)
    def on_sourceDirEdit_textChanged(self, dir):
        """
        Private slot to handle the source dir text changed.
        
        If the entered source directory is a subdirectory of the current
        projects main directory, the target directory path is synchronized.
        It is assumed, that the user wants to add a bunch of files to
        the project in place.
        
        @param dir the text of the source directory line edit (string)
        """
        if dir.startswith(self.ppath):
            self.targetDirEdit.setText(dir)
        
    def getData(self):
        """
        Public slot to retrieve the dialogs data.
        
        @return tuple of four values (string, string, string, boolean) giving
            the selected file type, the source and target directory and
            a flag indicating a recursive add
        """
        filetype = \
            self.filterComboBox.itemData(self.filterComboBox.currentIndex())
        return (
            filetype,
            Utilities.toNativeSeparators(self.sourceDirEdit.text()),
            Utilities.toNativeSeparators(self.targetDirEdit.text()),
            self.recursiveCheckBox.isChecked())
