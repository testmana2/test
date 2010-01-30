# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a simple Python syntax checker.
"""

import sys
import os
import types

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
    warningRole = Qt.UserRole + 2
    
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
            self.trUtf8("Press to show all files containing a syntax error"))
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.resultList.headerItem().setText(self.resultList.columnCount(), "")
        self.resultList.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.noResults = True
        self.cancelled = False
        
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
        itm = QTreeWidgetItem(self.resultList, 
                              [os.path.basename(file), str(line), error, sourcecode])
        itm.setTextAlignment(1, Qt.AlignRight)
        if isWarning:
            itm.setIcon(0, UI.PixmapCache.getIcon("warning.png"))
        else:
            itm.setIcon(0, UI.PixmapCache.getIcon("syntaxError.png"))
        itm.setToolTip(0, file)
        itm.setData(0, self.filenameRole, file)
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
                files.extend(Utilities.direntries(fn, 1, '*%s' % ext, 0))
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
                
                if codestring:
                    source = codestring
                else:
                    try:
                        source = Utilities.readEncodedFile(file)[0]
                        # convert eols
                        source = Utilities.convertLineEnds(source, os.linesep)
                    except (UnicodeDecodeError, IOError):
                        continue    # just ignore it
                
                nok, fname, line, code, error = Utilities.compile(file, source)
                if nok:
                    self.noResults = False
                    self.__createResultItem(fname, line, error, code)
                else:
                    if Preferences.getFlakes("IncludeInSyntaxCheck"):
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
            self.__createResultItem(self.trUtf8('No syntax errors found.'), "", "", "")
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
            
        fn = Utilities.normabspath(itm.data(0, self.filenameRole))
        lineno = int(itm.text(1))
        error = itm.text(2)
        
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
        for index in range(self.resultList.topLevelItemCount()):
            itm = self.resultList.topLevelItem(index)
            self.on_resultList_itemActivated(itm, 0)
        
        # go through the list again to clear syntax error markers
        # for files, that are ok
        vm = e5App().getObject("ViewManager")
        openFiles = vm.getOpenFilenames()
        errorFiles = []
        for index in range(self.resultList.topLevelItemCount()):
            itm = self.resultList.topLevelItem(index)
            errorFiles.append(Utilities.normabspath(itm.text(0)))
        for file in openFiles:
            if not file in errorFiles:
                editor = vm.getOpenEditor(file)
                editor.clearSyntaxError()
        
    def __clearErrors(self):
        """
        Private method to clear all error markers of open editors.
        """
        vm = e5App().getObject("ViewManager")
        openFiles = vm.getOpenFilenames()
        for file in openFiles:
            editor = vm.getOpenEditor(file)
            editor.clearSyntaxError()
