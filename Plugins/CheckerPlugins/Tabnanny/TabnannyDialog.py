# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the output of the tabnanny command process.
"""

import os
import fnmatch

from PyQt4.QtCore import pyqtSlot, Qt, QProcess
from PyQt4.QtGui import QDialog, QDialogButtonBox, QTreeWidgetItem, QApplication, \
    QHeaderView

from E5Gui.E5Application import e5App

from .Ui_TabnannyDialog import Ui_TabnannyDialog

from . import Tabnanny
import Utilities
import Preferences

from eric5config import getConfig


class TabnannyDialog(QDialog, Ui_TabnannyDialog):
    """
    Class implementing a dialog to show the results of the tabnanny check run.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent The parent widget (QWidget).
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.resultList.headerItem().setText(self.resultList.columnCount(), "")
        self.resultList.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.noResults = True
        self.cancelled = False
        
        self.__fileList = []
        self.__project = None
        self.filterFrame.setVisible(False)
        
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.resultList.sortItems(self.resultList.sortColumn(),
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
        QApplication.processEvents()
        
        if isinstance(fn, list):
            files = fn
        elif os.path.isdir(fn):
            files = []
            for ext in Preferences.getPython("Python3Extensions"):
                files.extend(Utilities.direntries(fn, 1, '*{0}'.format(ext), 0))
            for ext in Preferences.getPython("PythonExtensions"):
                files.extend(Utilities.direntries(fn, 1, '*{0}'.format(ext), 0))
        else:
            files = [fn]
        py3files = [f for f in files \
                    if f.endswith(tuple(Preferences.getPython("Python3Extensions")))]
        py2files = [f for f in files \
                    if f.endswith(tuple(Preferences.getPython("PythonExtensions")))]
        
        if len(py3files) + len(py2files) > 0:
            self.checkProgress.setMaximum(len(py3files) + len(py2files))
            QApplication.processEvents()
            
            # now go through all the files
            progress = 0
            for file in py3files + py2files:
                self.checkProgress.setValue(progress)
                QApplication.processEvents()
                self.__resort()
                
                if self.cancelled:
                    return
                
                try:
                    source = Utilities.readEncodedFile(file)[0]
                    # convert eols
                    source = Utilities.convertLineEnds(source, "\n")
                except (UnicodeError, IOError) as msg:
                    self.noResults = False
                    self.__createResultItem(file, "1",
                        "Error: {0}".format(str(msg)).rstrip()[1:-1])
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
                    self.__project.getProjectLanguage() in ["Python", "Python2"]):
                    nok, fname, line, error = self.__py2check(file)
                else:
                    nok, fname, line, error = Tabnanny.check(file, source)
                if nok:
                    self.noResults = False
                    self.__createResultItem(fname, line, error.rstrip())
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
        Private slot called when the action or the user pressed the button.
        """
        self.cancelled = True
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        
        if self.noResults:
            self.__createResultItem(self.trUtf8('No indentation errors found.'), "", "")
            QApplication.processEvents()
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
    
    ############################################################################
    ## Python 2 interface below
    ############################################################################
    
    def __py2check(self, filename):
        """
        Private method to perform the indentation check for Python 2 files.
        
        @param filename name of the file to be checked (string)
        @return A tuple indicating status (True = an error was found), the
            filename, the linenumber and the error message
            (boolean, string, string, string). The values are only
            valid, if the status is True.
        """
        interpreter = Preferences.getDebugger("PythonInterpreter")
        if interpreter == "" or not Utilities.isExecutable(interpreter):
            return (True, filename, "1",
                self.trUtf8("Python2 interpreter not configured."))
        
        checker = os.path.join(getConfig('ericDir'),
                               "UtilitiesPython2", "TabnannyChecker.py")
        
        proc = QProcess()
        proc.setProcessChannelMode(QProcess.MergedChannels)
        proc.start(interpreter, [checker, filename])
        finished = proc.waitForFinished(15000)
        if finished:
            output = \
                str(proc.readAllStandardOutput(),
                        Preferences.getSystem("IOEncoding"),
                        'replace').splitlines()
            
            nok = output[0] == "ERROR"
            if nok:
                fn = output[1]
                line = output[2]
                error = output[3]
                return (True, fn, line, error)
            else:
                return (False, None, None, None)
        
        return (True, filename, "1",
            self.trUtf8("Python2 interpreter did not finish within 15s."))
