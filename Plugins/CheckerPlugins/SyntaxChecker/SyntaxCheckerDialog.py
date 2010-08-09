# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a simple Python syntax checker.
"""

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from E5Gui.E5Application import e5App

from .Ui_SyntaxCheckerDialog import Ui_SyntaxCheckerDialog

import Utilities
from Utilities.py3flakes.checker import Checker
from Utilities.py3flakes.messages import ImportStarUsed
import Preferences
import UI.PixmapCache

class SyntaxCheckerDialog(QDialog, Ui_SyntaxCheckerDialog):
    """
    Class implementing a dialog to display the results of a syntax check run.
    """
    filenameRole = Qt.UserRole + 1
    lineRole     = Qt.UserRole + 2
    errorRole    = Qt.UserRole + 3
    warningRole  = Qt.UserRole + 4
    
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent The parent widget. (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.showButton = self.buttonBox.addButton(\
            self.trUtf8("Show"), QDialogButtonBox.ActionRole)
        self.showButton.setToolTip(\
            self.trUtf8("Press to show all files containing an issue"))
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.resultList.headerItem().setText(self.resultList.columnCount(), "")
        self.resultList.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.noResults = True
        self.cancelled = False
        self.__lastFileItem = None
        
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.resultList.sortItems(self.resultList.sortColumn(), 
                                  self.resultList.header().sortIndicatorOrder())
        
    def __createResultItem(self, file, line, error, sourcecode, isWarning = False):
        """
        Private method to create an entry in the result list.
        
        @param file filename of file (string)
        @param line linenumber of faulty source (integer or string)
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
        
        itm = QTreeWidgetItem(self.__lastFileItem, 
                              ["{0:6}".format(line), error, sourcecode])
        if isWarning:
            itm.setIcon(0, UI.PixmapCache.getIcon("warning.png"))
        else:
            itm.setIcon(0, UI.PixmapCache.getIcon("syntaxError.png"))
##        itm.setToolTip(0, file)
        itm.setData(0, self.filenameRole, file)
        itm.setData(0, self.lineRole, line)
        itm.setData(0, self.errorRole, error)
        itm.setData(0, self.warningRole, isWarning)
        
    def start(self, fn, codestring = ""):
        """
        Public slot to start the syntax check.
        
        @param fn file or list of files or directory to be checked
                (string or list of strings)
        @param codestring string containing the code to be checked (string).
            If this is given, file must be a single file name.
        """
        if isinstance(fn, list):
            files = fn
        elif os.path.isdir(fn):
            files = []
            for ext in Preferences.getPython("Python3Extensions"):
                files.extend(Utilities.direntries(fn, 1, '*{0}'.format(ext), 0))
        else:
            files = [fn]
        files = [f for f in files \
                    if f.endswith(tuple(Preferences.getPython("Python3Extensions")))]
        
        if (codestring and len(files) == 1) or \
           (not codestring and len(files) > 0):
            self.checkProgress.setMaximum(len(files))
            QApplication.processEvents()
            
            ignoreStarImportWarnings = Preferences.getFlakes("IgnoreStarImportWarnings")
            # now go through all the files
            progress = 0
            for file in files:
                if self.cancelled:
                    return
                
                self.__lastFileItem = None
                
                if codestring:
                    source = codestring
                else:
                    try:
                        source = Utilities.readEncodedFile(file)[0]
                        # convert eols
                        source = Utilities.convertLineEnds(source, "\n")
                    except (UnicodeDecodeError, IOError):
                        continue    # just ignore it
                
                nok, fname, line, code, error = Utilities.compile(file, source)
                if nok:
                    self.noResults = False
                    self.__createResultItem(fname, line, error, code)
                else:
                    if Preferences.getFlakes("IncludeInSyntaxCheck"):
                        try:
                            warnings = Checker(source, file)
                            warnings.messages.sort(key = lambda a: a.lineno)
                            for warning in warnings.messages:
                                if ignoreStarImportWarnings and \
                                   isinstance(warning, ImportStarUsed):
                                    continue
                                self.noResults = False
                                fname, lineno, message = warning.getMessageData()
                                self.__createResultItem(fname, lineno, message, "", 
                                                        isWarning = True)
                        except SyntaxError as err:
                            if err.text.strip():
                                msg = err.text.strip()
                            else:
                                msg = err.msg
                            self.__createResultItem(err.filename, err.lineno, msg, "")
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
        Private slot called when the syntax check finished or the user pressed the button.
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
            error = itm.data(0, self.errorRole)
            
            vm = e5App().getObject("ViewManager")
            vm.openSourceFile(fn, lineno)
            editor = vm.getOpenEditor(fn)
            
            if itm.data(0, self.warningRole):
                editor.toggleFlakesWarning(lineno, True, error)
            else:
                editor.toggleSyntaxError(lineno, True, error)
        
    @pyqtSlot()
    def on_showButton_clicked(self):
        """
        Private slot to handle the "Show" button press.
        """
        vm = e5App().getObject("ViewManager")
        
        for index in range(self.resultList.topLevelItemCount()):
            itm = self.resultList.topLevelItem(index)
            fn = Utilities.normabspath(itm.data(0, self.filenameRole))
            vm.openSourceFile(fn, 1)
        
        # go through the list again to clear syntax error and 
        # py3flakes warning markers for files, that are ok
        openFiles = vm.getOpenFilenames()
        errorFiles = []
        for index in range(self.resultList.topLevelItemCount()):
            itm = self.resultList.topLevelItem(index)
            errorFiles.append(Utilities.normabspath(itm.data(0, self.filenameRole)))
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
