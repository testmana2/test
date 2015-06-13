# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the tabnanny command
process.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import os
import fnmatch

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QTreeWidgetItem, \
    QApplication, QHeaderView

from E5Gui.E5Application import e5App

from .Ui_TabnannyDialog import Ui_TabnannyDialog

import Utilities
import Preferences


class TabnannyDialog(QDialog, Ui_TabnannyDialog):
    """
    Class implementing a dialog to show the results of the tabnanny check run.
    """
    def __init__(self, indentCheckService, parent=None):
        """
        Constructor
        
        @param indentCheckService reference to the service (IndentCheckService)
        @param parent The parent widget (QWidget).
        """
        super(TabnannyDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.resultList.headerItem().setText(self.resultList.columnCount(), "")
        self.resultList.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.indentCheckService = indentCheckService
        self.indentCheckService.indentChecked.connect(self.__processResult)
        self.filename = None
        
        self.noResults = True
        self.cancelled = False
        
        self.__fileList = []
        self.__project = None
        self.filterFrame.setVisible(False)
        
        self.checkProgress.setVisible(False)
        self.checkProgressLabel.setVisible(False)
        self.checkProgressLabel.setMaximumWidth(600)
        
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.resultList.sortItems(
            self.resultList.sortColumn(),
            self.resultList.header().sortIndicatorOrder())
        
    def __createResultItem(self, file, line, sourcecode):
        """
        Private method to create an entry in the result list.
        
        @param file filename of file (string)
        @param line linenumber of faulty source (integer or string)
        @param sourcecode faulty line of code (string)
        """
        itm = QTreeWidgetItem(self.resultList)
        itm.setData(0, Qt.DisplayRole, file)
        itm.setData(1, Qt.DisplayRole, line)
        itm.setData(2, Qt.DisplayRole, sourcecode)
        itm.setTextAlignment(1, Qt.AlignRight)
        
    def prepare(self, fileList, project):
        """
        Public method to prepare the dialog with a list of filenames.
        
        @param fileList list of filenames (list of strings)
        @param project reference to the project object (Project)
        """
        self.__fileList = fileList[:]
        self.__project = project
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.filterFrame.setVisible(True)
        
        self.__data = self.__project.getData("CHECKERSPARMS", "Tabnanny")
        if self.__data is None or "ExcludeFiles" not in self.__data:
            self.__data = {"ExcludeFiles": ""}
        self.excludeFilesEdit.setText(self.__data["ExcludeFiles"])
        
    def start(self, fn):
        """
        Public slot to start the tabnanny check.
        
        @param fn File or list of files or directory to be checked
                (string or list of strings)
        """
        if self.__project is None:
            self.__project = e5App().getObject("Project")
        
        self.cancelled = False
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        self.checkProgress.setVisible(True)
        QApplication.processEvents()
        
        if isinstance(fn, list):
            self.files = fn
        elif os.path.isdir(fn):
            self.files = []
            extensions = set(Preferences.getPython("PythonExtensions") +
                             Preferences.getPython("Python3Extensions"))
            for ext in extensions:
                self.files.extend(
                    Utilities.direntries(fn, True, '*{0}'.format(ext), 0))
        else:
            self.files = [fn]
        
        if len(self.files) > 0:
            self.checkProgress.setMaximum(len(self.files))
            self.checkProgress.setVisible(len(self.files) > 1)
            self.checkProgressLabel.setVisible(len(self.files) > 1)
            QApplication.processEvents()
        
        # now go through all the files
        self.progress = 0
        self.check()

    def check(self, codestring=''):
        """
        Public method to start a style check for one file.
        
        The results are reported to the __processResult slot.
        @keyparam codestring optional sourcestring (str)
        """
        if not self.files:
            self.checkProgressLabel.setPath("")
            self.checkProgress.setMaximum(1)
            self.checkProgress.setValue(1)
            self.__finish()
            return
        
        self.filename = self.files.pop(0)
        self.checkProgress.setValue(self.progress)
        self.checkProgressLabel.setPath(self.filename)
        QApplication.processEvents()
        self.__resort()
        
        if self.cancelled:
            return
        
        try:
            self.source = Utilities.readEncodedFile(self.filename)[0]
            self.source = Utilities.normalizeCode(self.source)
        except (UnicodeError, IOError) as msg:
            self.noResults = False
            self.__createResultItem(
                self.filename, 1,
                "Error: {0}".format(str(msg)).rstrip())
            self.progress += 1
            # Continue with next file
            self.check()
            return

        self.indentCheckService.indentCheck(
            None, self.filename, self.source)

    def __processResult(self, fn, nok, line, error):
        """
        Private slot called after perfoming a style check on one file.
        
        @param fn filename of the just checked file (str)
        @param nok flag if a problem was found (bool)
        @param line line number (str)
        @param error text of the problem (str)
        """
        # Check if it's the requested file, otherwise ignore signal
        if fn != self.filename:
            return
        
        if nok:
            self.noResults = False
            self.__createResultItem(fn, line, error.rstrip())
        self.progress += 1
        
        self.checkProgress.setValue(self.progress)
        self.checkProgressLabel.setPath("")
        QApplication.processEvents()
        self.__resort()
        
        self.check()

    def __finish(self):
        """
        Private slot called when the action or the user pressed the button.
        """
        self.cancelled = True
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        if self.noResults:
            self.__createResultItem(
                self.tr('No indentation errors found.'), "", "")
            QApplication.processEvents()
        self.resultList.header().resizeSections(QHeaderView.ResizeToContents)
        self.resultList.header().setStretchLastSection(True)
        
        self.checkProgress.setVisible(False)
        self.checkProgressLabel.setVisible(False)
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.buttonBox.button(QDialogButtonBox.Close):
            self.close()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.__finish()
        
    @pyqtSlot()
    def on_startButton_clicked(self):
        """
        Private slot to start a code metrics run.
        """
        fileList = self.__fileList[:]
        
        filterString = self.excludeFilesEdit.text()
        if "ExcludeFiles" not in self.__data or \
           filterString != self.__data["ExcludeFiles"]:
            self.__data["ExcludeFiles"] = filterString
            self.__project.setData("CHECKERSPARMS", "Tabnanny", self.__data)
        filterList = [f.strip() for f in filterString.split(",")
                      if f.strip()]
        if filterList:
            for filter in filterList:
                fileList = \
                    [f for f in fileList if not fnmatch.fnmatch(f, filter)]
        
        self.resultList.clear()
        self.noResults = True
        self.cancelled = False
        self.start(fileList)
        
    def on_resultList_itemActivated(self, itm, col):
        """
        Private slot to handle the activation of an item.
        
        @param itm reference to the activated item (QTreeWidgetItem)
        @param col column the item was activated in (integer)
        """
        if self.noResults:
            return
        
        fn = Utilities.normabspath(itm.text(0))
        lineno = int(itm.text(1))
        
        e5App().getObject("ViewManager").openSourceFile(fn, lineno)
