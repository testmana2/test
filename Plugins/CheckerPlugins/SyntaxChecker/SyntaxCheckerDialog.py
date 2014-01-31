# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a simple Python syntax checker.
"""

from __future__ import unicode_literals

import os
import fnmatch

from PyQt4.QtCore import pyqtSlot, Qt
from PyQt4.QtGui import QDialog, QDialogButtonBox, QTreeWidgetItem, \
    QApplication, QHeaderView

from E5Gui.E5Application import e5App

from .Ui_SyntaxCheckerDialog import Ui_SyntaxCheckerDialog

import Utilities
import UI.PixmapCache


class SyntaxCheckerDialog(QDialog, Ui_SyntaxCheckerDialog):
    """
    Class implementing a dialog to display the results of a syntax check run.
    """
    filenameRole = Qt.UserRole + 1
    lineRole = Qt.UserRole + 2
    indexRole = Qt.UserRole + 3
    errorRole = Qt.UserRole + 4
    warningRole = Qt.UserRole + 5
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent The parent widget. (QWidget)
        """
        super(SyntaxCheckerDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.showButton = self.buttonBox.addButton(
            self.trUtf8("Show"), QDialogButtonBox.ActionRole)
        self.showButton.setToolTip(
            self.trUtf8("Press to show all files containing an issue"))
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.resultList.headerItem().setText(self.resultList.columnCount(), "")
        self.resultList.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.noResults = True
        self.cancelled = False
        self.__lastFileItem = None
        
        self.__fileList = []
        self.__project = None
        self.filterFrame.setVisible(False)
        
        self.checkProgress.setVisible(False)
        self.checkProgressLabel.setVisible(False)
        self.checkProgressLabel.setMaximumWidth(600)
        
        self.syntaxCheckService = e5App().getObject('SyntaxCheckService')
        self.syntaxCheckService.syntaxChecked.connect(self.__processResult)
        
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.resultList.sortItems(self.resultList.sortColumn(),
                                  self.resultList.header().sortIndicatorOrder()
                                  )
        
    def __createResultItem(self, file, line, index, error, sourcecode,
                           isWarning=False):
        """
        Private method to create an entry in the result list.
        
        @param file file name of file (string)
        @param line line number of faulty source (integer or string)
        @param index index number of fault (integer)
        @param error error text (string)
        @param sourcecode faulty line of code (string)
        @param isWarning flag indicating a warning message (boolean)
        """
        if self.__lastFileItem is None:
            # It's a new file
            self.__lastFileItem = QTreeWidgetItem(self.resultList, [file])
            self.__lastFileItem.setFirstColumnSpanned(True)
            self.__lastFileItem.setExpanded(True)
            self.__lastFileItem.setData(0, self.filenameRole, file)
        
        itm = QTreeWidgetItem(self.__lastFileItem)
        if isWarning:
            itm.setIcon(0, UI.PixmapCache.getIcon("warning.png"))
        else:
            itm.setIcon(0, UI.PixmapCache.getIcon("syntaxError.png"))
        itm.setData(0, Qt.DisplayRole, line)
        itm.setData(1, Qt.DisplayRole, error)
        itm.setData(2, Qt.DisplayRole, sourcecode)
        itm.setData(0, self.filenameRole, file)
        itm.setData(0, self.lineRole, int(line))
        itm.setData(0, self.indexRole, index)
        itm.setData(0, self.errorRole, error)
        itm.setData(0, self.warningRole, isWarning)
        
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
        
        self.__data = self.__project.getData("CHECKERSPARMS", "SyntaxChecker")
        if self.__data is None or "ExcludeFiles" not in self.__data:
            self.__data = {"ExcludeFiles": ""}
        self.excludeFilesEdit.setText(self.__data["ExcludeFiles"])
        
    def start(self, fn, codestring=""):
        """
        Public slot to start the syntax check.
        
        @param fn file or list of files or directory to be checked
                (string or list of strings)
        @param codestring string containing the code to be checked (string).
            If this is given, fn must be a single file name.
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
            for ext in self.syntaxCheckService.getExtensions():
                self.files.extend(
                    Utilities.direntries(fn, True, '*{0}'.format(ext), 0))
        else:
            self.files = [fn]
        
        # Reset marker for every file which is open and getting checked
        vm = e5App().getObject("ViewManager")
        openFiles = vm.getOpenFilenames()
        for openFile in openFiles:
            if openFile in self.files:
                editor = vm.getOpenEditor(openFile)
                editor.clearSyntaxError()
                editor.clearFlakesWarnings()
        
        if codestring or len(self.files) > 0:
            self.checkProgress.setMaximum(max(1, len(self.files)))
            self.checkProgress.setVisible(len(self.files) > 1)
            self.checkProgressLabel.setVisible(len(self.files) > 1)
            QApplication.processEvents()

            # now go through all the files
            self.progress = 0
            self.check(codestring)
    
    def check(self, codestring=''):
        """
        Start a check for one file.
        
        The results are reported to the __processResult slot.
        @keyparam codestring optional sourcestring (str)
        """
        self.filename = self.files.pop(0)
        self.checkProgress.setValue(self.progress)
        self.checkProgressLabel.setPath(self.filename)
        QApplication.processEvents()
        self.__resort()
        
        if self.cancelled:
            return
        
        self.__lastFileItem = None
        
        if codestring:
            self.source = codestring
        else:
            try:
                self.source = Utilities.readEncodedFile(self.filename)[0]
                self.source = Utilities.normalizeCode(self.source)
            except (UnicodeError, IOError) as msg:
                self.noResults = False
                self.__createResultItem(
                    self.filename, 1, 0,
                    self.trUtf8("Error: {0}").format(str(msg))
                    .rstrip()[1:-1], "")
                self.progress += 1
                # Continue with next file
                self.check()
                return
        
        self.syntaxCheckService.syntaxCheck(None, self.filename, self.source)

    def __processResult(
            self, fn, nok, line, index, code, error, warnings):
        """
        Slot to display the reported messages.
        
        If checkFlakes is True, warnings contains a list of strings containing
        the warnings (marker, file name, line number, message)
        The values are only valid, if nok is False.
        
        @param fn filename of the checked file (str)
        @param nok flag if an error in the source was found (boolean)
        @param line number where the error occured (int)
        @param index the column where the error occured (int)
        @param code the part of the code where the error occured (str)
        @param error the name of the error (str)
        @param warnings a list of strings containing the warnings
            (marker, file name, line number, col, message)
        """
        # Check if it's the requested file, otherwise ignore signal
        if fn != self.filename:
            return
        
        if nok:
            self.noResults = False
            self.__createResultItem(
                fn, line, index, error, code.strip(), False)
        else:
            source = self.source.splitlines()
            for marker, _fn, lineno, col, msg in warnings:
                self.noResults = False
                scr_line = source[lineno - 1].strip()
                self.__createResultItem(_fn, lineno, col, msg, scr_line, True)
        self.progress += 1
        self.checkProgress.setValue(self.progress)
        QApplication.processEvents()
        self.__resort()

        if self.files:
            self.check()
        else:
            self.checkProgressLabel.setPath("")
            self.checkProgress.setMaximum(1)
            self.checkProgress.setValue(1)
            self.__finish()
        
    def __finish(self):
        """
        Private slot called when the syntax check finished or the user
        pressed the button.
        """
        self.cancelled = True
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        if self.noResults:
            QTreeWidgetItem(self.resultList, [self.trUtf8('No issues found.')])
            QApplication.processEvents()
            self.showButton.setEnabled(False)
        else:
            self.showButton.setEnabled(True)
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
        elif button == self.showButton:
            self.on_showButton_clicked()
        
    @pyqtSlot()
    def on_startButton_clicked(self):
        """
        Private slot to start a syntax check run.
        """
        fileList = self.__fileList[:]
        
        filterString = self.excludeFilesEdit.text()
        if "ExcludeFiles" not in self.__data or \
           filterString != self.__data["ExcludeFiles"]:
            self.__data["ExcludeFiles"] = filterString
            self.__project.setData("CHECKERSPARMS", "SyntaxChecker",
                                   self.__data)
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
        
        if itm.parent():
            fn = Utilities.normabspath(itm.data(0, self.filenameRole))
            lineno = itm.data(0, self.lineRole)
            index = itm.data(0, self.indexRole)
            error = itm.data(0, self.errorRole)
            
            vm = e5App().getObject("ViewManager")
            vm.openSourceFile(fn, lineno)
            editor = vm.getOpenEditor(fn)
            
            if itm.data(0, self.warningRole):
                editor.toggleWarning(lineno, True, error)
            else:
                editor.toggleSyntaxError(lineno, index, True, error, show=True)
        else:
            fn = Utilities.normabspath(itm.data(0, self.filenameRole))
            vm = e5App().getObject("ViewManager")
            vm.openSourceFile(fn)
            editor = vm.getOpenEditor(fn)
            for index in range(itm.childCount()):
                citm = itm.child(index)
                lineno = citm.data(0, self.lineRole)
                index = citm.data(0, self.indexRole)
                error = citm.data(0, self.errorRole)
                if citm.data(0, self.warningRole):
                    editor.toggleWarning(lineno, True, error)
                else:
                    editor.toggleSyntaxError(
                        lineno, index, True, error, show=True)
        
    @pyqtSlot()
    def on_showButton_clicked(self):
        """
        Private slot to handle the "Show" button press.
        """
        vm = e5App().getObject("ViewManager")
        
        selectedIndexes = []
        for index in range(self.resultList.topLevelItemCount()):
            if self.resultList.topLevelItem(index).isSelected():
                selectedIndexes.append(index)
        if len(selectedIndexes) == 0:
            selectedIndexes = list(range(self.resultList.topLevelItemCount()))
        for index in selectedIndexes:
            itm = self.resultList.topLevelItem(index)
            fn = Utilities.normabspath(itm.data(0, self.filenameRole))
            vm.openSourceFile(fn, 1)
            editor = vm.getOpenEditor(fn)
            editor.clearSyntaxError()
            editor.clearFlakesWarnings()
            for cindex in range(itm.childCount()):
                citm = itm.child(cindex)
                lineno = citm.data(0, self.lineRole)
                index = citm.data(0, self.indexRole)
                error = citm.data(0, self.errorRole)
                if citm.data(0, self.warningRole):
                    editor.toggleWarning(lineno, True, error)
                else:
                    editor.toggleSyntaxError(
                        lineno, index, True, error, show=True)
        
        # go through the list again to clear syntax error and
        # flakes warning markers for files, that are ok
        openFiles = vm.getOpenFilenames()
        errorFiles = []
        for index in range(self.resultList.topLevelItemCount()):
            itm = self.resultList.topLevelItem(index)
            errorFiles.append(
                Utilities.normabspath(itm.data(0, self.filenameRole)))
        for file in openFiles:
            if not file in errorFiles:
                editor = vm.getOpenEditor(file)
                editor.clearSyntaxError()
                editor.clearFlakesWarnings()
        
    def __clearErrors(self):
        """
        Private method to clear all error markers of open editors.
        """
        vm = e5App().getObject("ViewManager")
        openFiles = vm.getOpenFilenames()
        for file in openFiles:
            editor = vm.getOpenEditor(file)
            editor.clearSyntaxError()
            editor.clearFlakesWarnings()
