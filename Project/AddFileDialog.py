# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to add a file to the project.
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog

from E5Gui.E5Completers import E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_AddFileDialog import Ui_AddFileDialog

import Utilities


class AddFileDialog(QDialog, Ui_AddFileDialog):
    """
    Class implementing a dialog to add a file to the project.
    """
    def __init__(self, pro, parent=None, filter=None, name=None,
                 startdir=None):
        """
        Constructor
        
        @param pro reference to the project object
        @param parent parent widget of this dialog (QWidget)
        @param filter filter specification for the file to add (string)
        @param name name of this dialog (string)
        @param startdir start directory for the selection dialog
        """
        super(AddFileDialog, self).__init__(parent)
        if name:
            self.setObjectName(name)
        self.setupUi(self)
        
        self.targetDirCompleter = E5DirCompleter(self.targetDirEdit)
        
        self.targetDirEdit.setText(pro.ppath)
        self.filter = filter
        self.ppath = pro.ppath
        self.startdir = startdir
        self.filetypes = pro.pdata["FILETYPES"]
        # save a reference to the filetypes dict
        
        if self.filter is not None:
            self.sourcecodeCheckBox.hide()
        
    @pyqtSlot()
    def on_targetDirButton_clicked(self):
        """
        Private slot to display a directory selection dialog.
        """
        startdir = self.targetDirEdit.text()
        if not startdir and self.startdir is not None:
            startdir = self.startdir
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.trUtf8("Select target directory"),
            startdir)
            
        if directory:
            self.targetDirEdit.setText(Utilities.toNativeSeparators(directory))
        
    @pyqtSlot()
    def on_sourceFileButton_clicked(self):
        """
        Private slot to display a file selection dialog.
        """
        dir = self.sourceFileEdit.text().split(os.pathsep, 1)[0]
        if not dir:
            if self.startdir is not None:
                dir = self.startdir
            else:
                dir = self.targetDirEdit.text()
        if self.filter is None:
            patterns = {
                "SOURCES": [],
                "FORMS": [],
                "RESOURCES": [],
                "INTERFACES": [],
                "TRANSLATIONS": [],
            }
            for pattern, filetype in list(self.filetypes.items()):
                if filetype in patterns:
                    patterns[filetype].append(pattern)
            dfilter = self.trUtf8(
                "Source Files ({0});;"
                "Forms Files ({1});;"
                "Resource Files ({2});;"
                "Interface Files ({3});;"
                "Translation Files ({4});;"
                "All Files (*)")\
                .format(
                    " ".join(patterns["SOURCES"]),
                    " ".join(patterns["FORMS"]),
                    " ".join(patterns["RESOURCES"]),
                    " ".join(patterns["INTERFACES"]),
                    " ".join(patterns["TRANSLATIONS"]))
            caption = self.trUtf8("Select Files")
        elif self.filter == 'form':
            patterns = []
            for pattern, filetype in list(self.filetypes.items()):
                if filetype == "FORMS":
                    patterns.append(pattern)
            dfilter = self.trUtf8("Forms Files ({0})")\
                .format(" ".join(patterns))
            caption = self.trUtf8("Select user-interface files")
        elif self.filter == "resource":
            patterns = []
            for pattern, filetype in list(self.filetypes.items()):
                if filetype == "RESOURCES":
                    patterns.append(pattern)
            dfilter = self.trUtf8("Resource Files ({0})")\
                .format(" ".join(patterns))
            caption = self.trUtf8("Select resource files")
        elif self.filter == 'source':
            patterns = []
            for pattern, filetype in list(self.filetypes.items()):
                if filetype == "SOURCES":
                    patterns.append(pattern)
            dfilter = self.trUtf8("Source Files ({0});;All Files (*)")\
                .format(" ".join(patterns))
            caption = self.trUtf8("Select source files")
        elif self.filter == 'interface':
            patterns = []
            for pattern, filetype in list(self.filetypes.items()):
                if filetype == "INTERFACES":
                    patterns.append(pattern)
            dfilter = self.trUtf8("Interface Files ({0})")\
                .format(" ".join(patterns))
            caption = self.trUtf8("Select interface files")
        elif self.filter == 'translation':
            patterns = []
            for pattern, filetype in list(self.filetypes.items()):
                if filetype == "TRANSLATIONS":
                    patterns.append(pattern)
            dfilter = self.trUtf8("Translation Files ({0})")\
                .format(" ".join(patterns))
            caption = self.trUtf8("Select translation files")
        elif self.filter == 'others':
            dfilter = self.trUtf8("All Files (*)")
            caption = self.trUtf8("Select files")
        else:
            return
        
        fnames = E5FileDialog.getOpenFileNames(self, caption, dir, dfilter)
        
        if len(fnames):
            self.sourceFileEdit.setText(Utilities.toNativeSeparators(
                os.pathsep.join(fnames)))
        
    @pyqtSlot(str)
    def on_sourceFileEdit_textChanged(self, sfile):
        """
        Private slot to handle the source file text changed.
        
        If the entered source directory is a subdirectory of the current
        projects main directory, the target directory path is synchronized.
        It is assumed, that the user wants to add a bunch of files to
        the project in place.
        
        @param sfile the text of the source file line edit (string)
        """
        sfile = sfile.split(os.pathsep, 1)[0]
        if sfile.startswith(self.ppath):
            if os.path.isdir(sfile):
                dir = sfile
            else:
                dir = os.path.dirname(sfile)
            self.targetDirEdit.setText(dir)
        
    def getData(self):
        """
        Public slot to retrieve the dialogs data.
        
        @return tuple of three values (list of string, string, boolean)
            giving the source files, the target directory and a flag
            telling, whether the files shall be added as source code
        """
        return (
            [Utilities.toNativeSeparators(f) for f in
                self.sourceFileEdit.text().split(os.pathsep)],
            Utilities.toNativeSeparators(self.targetDirEdit.text()),
            self.sourcecodeCheckBox.isChecked())
