# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the results of the PEP 8 check.
"""

import os
import fnmatch

from PyQt4.QtCore import pyqtSlot, Qt
from PyQt4.QtGui import QDialog, QTreeWidgetItem, QAbstractButton, \
    QDialogButtonBox, QApplication, QHeaderView

from . import pep8

from E5Gui.E5Application import e5App

from .Pep8Checker import Pep8Checker, Pep8Py2Checker
from .Pep8CodeSelectionDialog import Pep8CodeSelectionDialog

from .Ui_Pep8Dialog import Ui_Pep8Dialog

import UI.PixmapCache
import Preferences
import Utilities

class Pep8Dialog(QDialog, Ui_Pep8Dialog):
    """
    Class implementing a dialog to show the results of the PEP 8 check.
    """
    filenameRole = Qt.UserRole + 1
    lineRole     = Qt.UserRole + 2
    positionRole = Qt.UserRole + 3
    messageRole  = Qt.UserRole + 4
    
    settingsKey = "PEP8/"
    
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
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
        
        self.__fileOrFileList = ""
        self.__project = None
        self.__forProject = False
        self.__data = {}
        
        self.clearButton.setIcon(
            UI.PixmapCache.getIcon("clearLeft.png"))
        self.clearButtonExcludeMessages.setIcon(
            UI.PixmapCache.getIcon("clearLeft.png"))
        self.clearButtonIncludeMessages.setIcon(
            UI.PixmapCache.getIcon("clearLeft.png"))
        self.on_loadDefaultButton_clicked()
    
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.resultList.sortItems(self.resultList.sortColumn(), 
                                  self.resultList.header().sortIndicatorOrder()
                                 )
    
    def __createResultItem(self, file, line, pos, message):
        """
        Private method to create an entry in the result list.
        
        @param file file name of the file (string)
        @param line line number of issue (integer or string)
        @param pos character position of issue (integer or string)
        @param message message text (string)
        """
        if self.__lastFileItem is None:
            # It's a new file
            self.__lastFileItem = QTreeWidgetItem(self.resultList, [file])
            self.__lastFileItem.setFirstColumnSpanned(True)
            self.__lastFileItem.setExpanded(True)
            self.__lastFileItem.setData(0, self.filenameRole, file)
        
        code, message = message.split(None, 1)
        itm = QTreeWidgetItem(self.__lastFileItem, 
            ["{0:6}".format(line), code, message])
        if code.startswith("W"):
            itm.setIcon(0, UI.PixmapCache.getIcon("warning.png"))
        else:
            itm.setIcon(0, UI.PixmapCache.getIcon("syntaxError.png"))
        itm.setData(0, self.filenameRole, file)
        itm.setData(0, self.lineRole, int(line))
        itm.setData(0, self.positionRole, int(pos))
        itm.setData(0, self.messageRole, message)
    
    def prepare(self, fileList, project):
        """
        Public method to prepare the dialog with a list of filenames.
        
        @param fileList list of filenames (list of strings)
        @param project reference to the project object (Project)
        """
        self.__fileOrFileList = fileList[:]
        self.__project = project
        self.__forProject = True
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        self.__data = self.__project.getData("CHECKERSPARMS", "Pep8Checker")
        if self.__data is None or "ExcludeFiles" not in self.__data:
            # initialize the data structure
            self.__data = {
                "ExcludeFiles" : "", 
                "ExcludeMessages" : pep8.DEFAULT_IGNORE, 
                "IncludeMessages" : "", 
                "RepeatMessages" : False, 
            }
        self.excludeFilesEdit.setText(self.__data["ExcludeFiles"])
        self.excludeMessagesEdit.setText(self.__data["ExcludeMessages"])
        self.includeMessagesEdit.setText(self.__data["IncludeMessages"])
        self.repeatCheckBox.setChecked(self.__data["RepeatMessages"])
    
    def start(self, fn, codestring = "", save = False, repeat = None):
        """
        Public slot to start the PEP 8 check.
        
        @param fn file or list of files or directory to be checked
                (string or list of strings)
        @keyparam codestring string containing the code to be checked (string).
            If this is given, file must be a single file name.
        @keyparam save flag indicating to save the given 
            file/file list/directory (boolean)
        @keyparam repeat state of the repeat check box if it is not None
            (None or boolean)
        """
        if self.__project is None:
            self.__project = e5App().getObject("Project")
        
        self.cancelled = False
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        if repeat is not None:
            self.repeatCheckBox.setChecked(repeat)
        QApplication.processEvents()
        
        if save:
            self.__fileOrFileList = fn
        
        if isinstance(fn, list):
            files = fn[:]
        elif os.path.isdir(fn):
            files = []
            for ext in Preferences.getPython("Python3Extensions"):
                files.extend(
                    Utilities.direntries(fn, 1, '*{0}'.format(ext), 0))
            for ext in Preferences.getPython("PythonExtensions"):
                files.extend(
                    Utilities.direntries(fn, 1, '*{0}'.format(ext), 0))
        else:
            files = [fn]
        
        # filter the list depending on the filter string
        if files:
            filterString = self.excludeFilesEdit.text()
            filterList = [f.strip() for f in filterString.split(",") 
                          if f.strip()]
            for filter in filterList:
                files = \
                    [f for f in files 
                     if not fnmatch.fnmatch(f, filter.strip())]
        
        py3files = [f for f in files \
                    if f.endswith(
                        tuple(Preferences.getPython("Python3Extensions")))]
        py2files = [f for f in files \
                    if f.endswith(
                        tuple(Preferences.getPython("PythonExtensions")))]
        
        if (codestring and len(py3files) == 1) or \
           (codestring and len(py2files) == 1) or \
           (not codestring and len(py3files) + len(py2files) > 0):
            self.checkProgress.setMaximum(len(py3files) + len(py2files))
            QApplication.processEvents()
            
            # extract the configuration values
            excludeMessages = self.excludeMessagesEdit.text()
            includeMessages = self.includeMessagesEdit.text()
            repeatMessages = self.repeatCheckBox.isChecked()
            
            # now go through all the files
            progress = 0
            for file in py3files + py2files:
                self.checkProgress.setValue(progress)
                QApplication.processEvents()
                self.__resort()
                
                if self.cancelled:
                    return
                
                self.__lastFileItem = None
                
                if codestring:
                    source = codestring.splitlines(True)
                else:
                    try:
                        source = Utilities.readEncodedFile(file)[0]
                        # convert eols
                        source = Utilities.convertLineEnds(source, "\n")
                        source = source.splitlines(True)
                    except (UnicodeError, IOError) as msg:
                        self.noResults = False
                        self.__createResultItem(file, "1", "1", 
                            self.trUtf8("Error: {0}").format(str(msg))\
                                .rstrip()[1:-1])
                        progress += 1
                        continue
                
                flags = Utilities.extractFlags(source)
                ext = os.path.splitext(file)[1]
                if ("FileType" in flags and 
                    flags["FileType"] in ["Python", "Python2"]) or \
                   file in py2files or \
                   (ext in [".py", ".pyw"] and \
                    Preferences.getProject("DeterminePyFromProject") and \
                    self.__project.isOpen() and \
                    self.__project.isProjectFile(file) and \
                    self.__project.getProjectLanguage() in ["Python", 
                                                            "Python2"]):
                    checker = Pep8Py2Checker(file, [], 
                        repeat = repeatMessages, 
                        select = includeMessages,
                        ignore = excludeMessages)
                    checker.messages.sort(key = lambda a: a[1])
                    for message in checker.messages:
                        fname, lineno, position, text = message
                        if not source[lineno - 1].strip()\
                           .endswith("__IGNORE_WARNING__"):
                            self.noResults = False
                            self.__createResultItem(
                                fname, lineno, position, text)
                else:
                    checker = Pep8Checker(file, source, 
                        repeat = repeatMessages, 
                        select = includeMessages,
                        ignore = excludeMessages)
                    checker.check_all()
                    checker.messages.sort(key = lambda a: a[1])
                    for message in checker.messages:
                        fname, lineno, position, text = message
                        if not source[lineno - 1].strip()\
                           .endswith("__IGNORE_WARNING__"):
                            self.noResults = False
                            self.__createResultItem(
                                fname, lineno, position, text)
                progress += 1
            self.checkProgress.setValue(progress)
            QApplication.processEvents()
            self.__resort()
        else:
            self.checkProgress.setMaximum(1)
            self.checkProgress.setValue(1)
        self.__finish()
    
    def __finish(self):
        """
        Private slot called when the PEP 8 check finished or the user
        pressed the cancel button.
        """
        self.cancelled = True
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        if self.noResults:
            QTreeWidgetItem(self.resultList, [self.trUtf8('No issues found.')])
            QApplication.processEvents()
            self.showButton.setEnabled(False)
            self.__clearErrors()
        else:
            self.showButton.setEnabled(True)
        self.resultList.header().resizeSections(QHeaderView.ResizeToContents)
        self.resultList.header().setStretchLastSection(True)
    
    @pyqtSlot()
    def on_startButton_clicked(self):
        """
        Private slot to start a PEP 8 check run.
        """
        if self.__forProject:
            data = {
                "ExcludeFiles" : self.excludeFilesEdit.text(), 
                "ExcludeMessages" : self.excludeMessagesEdit.text(), 
                "IncludeMessages" : self.includeMessagesEdit.text(), 
                "RepeatMessages" : self.repeatCheckBox.isChecked(),
            }
            if data != self.__data:
                self.__data = data
                self.__project.setData("CHECKERSPARMS", "Pep8Checker", 
                                       self.__data)
        
        self.resultList.clear()
        self.noResults = True
        self.cancelled = False
        self.start(self.__fileOrFileList)
    
    @pyqtSlot()
    def on_excludeMessagesSelectButton_clicked(self):
        """
        Private slot to select the message codes to be excluded via a
        selection dialog.
        """
        dlg = Pep8CodeSelectionDialog(self.excludeMessagesEdit.text(), self)
        if dlg.exec_() == QDialog.Accepted:
            self.excludeMessagesEdit.setText(dlg.getSelectedCodes())
    
    @pyqtSlot()
    def on_includeMessagesSelectButton_clicked(self):
        """
        Private slot to select the message codes to be included via a
        selection dialog.
        """
        dlg = Pep8CodeSelectionDialog(self.includeMessagesEdit.text(), self)
        if dlg.exec_() == QDialog.Accepted:
            self.includeMessagesEdit.setText(dlg.getSelectedCodes())
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_resultList_itemActivated(self, item, column):
        """
        Private slot to handle the activation of an item. 
        
        @param item reference to the activated item (QTreeWidgetItem)
        @param column column the item was activated in (integer)
        """
        if self.noResults:
            return
        
        if item.parent():
            fn = Utilities.normabspath(item.data(0, self.filenameRole))
            lineno = item.data(0, self.lineRole)
            position = item.data(0, self.positionRole)
            message = item.data(0, self.messageRole)
            
            vm = e5App().getObject("ViewManager")
            vm.openSourceFile(fn, lineno = lineno, pos = position)
            editor = vm.getOpenEditor(fn)
            
            editor.toggleFlakesWarning(lineno, True, message)
    
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
            editor.clearFlakesWarnings()
            for cindex in range(itm.childCount()):
                citm = itm.child(cindex)
                lineno = citm.data(0, self.lineRole)
                message = citm.data(0, self.messageRole)
                editor.toggleFlakesWarning(lineno, True, message)
        
        # go through the list again to clear warning markers for files,
        # that are ok
        openFiles = vm.getOpenFilenames()
        errorFiles = []
        for index in range(self.resultList.topLevelItemCount()):
            itm = self.resultList.topLevelItem(index)
            errorFiles.append(
                Utilities.normabspath(itm.data(0, self.filenameRole)))
        for file in openFiles:
            if not file in errorFiles:
                editor = vm.getOpenEditor(file)
                editor.clearFlakesWarnings()
    
    @pyqtSlot()
    def on_loadDefaultButton_clicked(self):
        """
        Private slot to load the default configuration values.
        """
        self.excludeFilesEdit.setText(Preferences.Prefs.settings.value(
            "PEP8/ExcludeFilePatterns"))
        self.excludeMessagesEdit.setText(Preferences.Prefs.settings.value(
            "PEP8/ExcludeMessages", pep8.DEFAULT_IGNORE))
        self.includeMessagesEdit.setText(Preferences.Prefs.settings.value(
            "PEP8/IncludeMessages"))
##        self.repeatCheckBox.setChecked(Preferences.toBool(
##            Preferences.Prefs.settings.value("PEP8/RepeatMessages")))
    
    @pyqtSlot()
    def on_storeDefaultButton_clicked(self):
        """
        Private slot to store the current configuration values as
        default values.
        """
        Preferences.Prefs.settings.setValue("PEP8/ExcludeFilePatterns",
            self.excludeFilesEdit.text())
        Preferences.Prefs.settings.setValue("PEP8/ExcludeMessages",
            self.excludeMessagesEdit.text())
        Preferences.Prefs.settings.setValue("PEP8/IncludeMessages",
            self.includeMessagesEdit.text())
##        Preferences.Prefs.settings.setValue("PEP8/RepeatMessages",
##            self.repeatCheckBox.isChecked())
    
    @pyqtSlot(QAbstractButton)
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
    
    def __clearErrors(self):
        """
        Private method to clear all warning markers of open editors.
        """
        vm = e5App().getObject("ViewManager")
        openFiles = vm.getOpenFilenames()
        for file in openFiles:
            editor = vm.getOpenEditor(file)
            editor.clearFlakesWarnings()
