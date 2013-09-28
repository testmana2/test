# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the results of the PEP 8 check.
"""

import os
import fnmatch

from PyQt4.QtCore import pyqtSlot, Qt
from PyQt4.QtGui import QDialog, QTreeWidgetItem, QAbstractButton, \
    QDialogButtonBox, QApplication, QHeaderView, QIcon

from E5Gui.E5Application import e5App

from .Ui_Pep8Dialog import Ui_Pep8Dialog

import UI.PixmapCache
import Preferences
import Utilities

from . import pep8
from .Pep8NamingChecker import Pep8NamingChecker

# register the name checker
pep8.register_check(Pep8NamingChecker, Pep8NamingChecker.Codes)

from .Pep257Checker import Pep257Checker


class Pep8Report(pep8.BaseReport):
    """
    Class implementing a special report to be used with our dialog.
    """
    def __init__(self, options):
        """
        Constructor
        
        @param options options for the report (optparse.Values)
        """
        super().__init__(options)
        
        self.__repeat = options.repeat
        self.errors = []
    
    def error_args(self, line_number, offset, code, check, *args):
        """
        Public method to collect the error messages.
        
        @param line_number line number of the issue (integer)
        @param offset position within line of the issue (integer)
        @param code message code (string)
        @param check reference to the checker function (function)
        @param args arguments for the message (list)
        """
        code = super().error_args(line_number, offset, code, check, *args)
        if code and (self.counters[code] == 1 or self.__repeat):
            if code in Pep8NamingChecker.Codes:
                text = Pep8NamingChecker.getMessage(code, *args)
            else:
                text = pep8.getMessage(code, *args)
            self.errors.append(
                (self.filename, line_number, offset, text)
            )
        return code


class Pep8Dialog(QDialog, Ui_Pep8Dialog):
    """
    Class implementing a dialog to show the results of the PEP 8 check.
    """
    filenameRole = Qt.UserRole + 1
    lineRole = Qt.UserRole + 2
    positionRole = Qt.UserRole + 3
    messageRole = Qt.UserRole + 4
    fixableRole = Qt.UserRole + 5
    codeRole = Qt.UserRole + 6
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.docTypeComboBox.addItem(self.trUtf8("PEP-257"), "pep257")
        self.docTypeComboBox.addItem(self.trUtf8("Eric"), "eric")
        
        self.statisticsButton = self.buttonBox.addButton(
            self.trUtf8("Statistics..."), QDialogButtonBox.ActionRole)
        self.statisticsButton.setToolTip(
            self.trUtf8("Press to show some statistics for the last run"))
        self.statisticsButton.setEnabled(False)
        self.showButton = self.buttonBox.addButton(
            self.trUtf8("Show"), QDialogButtonBox.ActionRole)
        self.showButton.setToolTip(
            self.trUtf8("Press to show all files containing an issue"))
        self.showButton.setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.resultList.headerItem().setText(self.resultList.columnCount(), "")
        self.resultList.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.checkProgress.setVisible(False)
        self.checkProgressLabel.setVisible(False)
        self.checkProgressLabel.setMaximumWidth(600)
        
        self.noResults = True
        self.cancelled = False
        self.__lastFileItem = None
        
        self.__fileOrFileList = ""
        self.__project = None
        self.__forProject = False
        self.__data = {}
        self.__statistics = {}
        
        self.on_loadDefaultButton_clicked()
    
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.resultList.sortItems(self.resultList.sortColumn(),
                                  self.resultList.header().sortIndicatorOrder()
                                 )
    
    def __createResultItem(self, file, line, pos, message, fixed, autofixing):
        """
        Private method to create an entry in the result list.
        
        @param file file name of the file (string)
        @param line line number of issue (integer or string)
        @param pos character position of issue (integer or string)
        @param message message text (string)
        @param fixed flag indicating a fixed issue (boolean)
        @param autofixing flag indicating, that we are fixing issues
            automatically (boolean)
        @return reference to the created item (QTreeWidgetItem)
        """
        from .Pep8Fixer import Pep8FixableIssues
        
        if self.__lastFileItem is None:
            # It's a new file
            self.__lastFileItem = QTreeWidgetItem(self.resultList, [file])
            self.__lastFileItem.setFirstColumnSpanned(True)
            self.__lastFileItem.setExpanded(True)
            self.__lastFileItem.setData(0, self.filenameRole, file)
        
        fixable = False
        code, message = message.split(None, 1)
        itm = QTreeWidgetItem(self.__lastFileItem,
            ["{0:6}".format(line), code, message])
        if code.startswith("W"):
            itm.setIcon(1, UI.PixmapCache.getIcon("warning.png"))
        elif code.startswith("N"):
            itm.setIcon(1, UI.PixmapCache.getIcon("namingError.png"))
        elif code.startswith("D"):
            itm.setIcon(1, UI.PixmapCache.getIcon("docstringError.png"))
        else:
            itm.setIcon(1, UI.PixmapCache.getIcon("syntaxError.png"))
        if fixed:
            itm.setIcon(0, UI.PixmapCache.getIcon("issueFixed.png"))
        elif code in Pep8FixableIssues and not autofixing:
            itm.setIcon(0, UI.PixmapCache.getIcon("issueFixable.png"))
            fixable = True
        
        itm.setTextAlignment(0, Qt.AlignRight)
        itm.setTextAlignment(1, Qt.AlignHCenter)
        
        itm.setTextAlignment(0, Qt.AlignVCenter)
        itm.setTextAlignment(1, Qt.AlignVCenter)
        itm.setTextAlignment(2, Qt.AlignVCenter)
        
        itm.setData(0, self.filenameRole, file)
        itm.setData(0, self.lineRole, int(line))
        itm.setData(0, self.positionRole, int(pos))
        itm.setData(0, self.messageRole, message)
        itm.setData(0, self.fixableRole, fixable)
        itm.setData(0, self.codeRole, code)
        
        return itm
    
    def __modifyFixedResultItem(self, itm, text, fixed):
        """
        Private method to modify a result list entry to show its
        positive fixed state.
        
        @param itm reference to the item to modify (QTreeWidgetItem)
        @param text text to be appended (string)
        @param fixed flag indicating a fixed issue (boolean)
        """
        if fixed:
            message = itm.data(0, self.messageRole) + text
            itm.setText(2, message)
            itm.setIcon(0, UI.PixmapCache.getIcon("issueFixed.png"))
            
            itm.setData(0, self.messageRole, message)
        else:
            itm.setIcon(0, QIcon())
        itm.setData(0, self.fixableRole, False)
    
    def __updateStatistics(self, statistics, fixer):
        """
        Private method to update the collected statistics.
        
        @param statistics dictionary of statistical data with
            message code as key and message count as value
        @param fixer reference to the PEP 8 fixer (Pep8Fixer)
        """
        self.__statistics["_FilesCount"] += 1
        stats = {v: k for v, k in statistics.items() if v[0].isupper()}
        if stats:
            self.__statistics["_FilesIssues"] += 1
            for key in statistics:
                if key in self.__statistics:
                    self.__statistics[key] += statistics[key]
                else:
                    self.__statistics[key] = statistics[key]
        if fixer:
            self.__statistics["_IssuesFixed"] += fixer.fixed
    
    def __updateFixerStatistics(self, fixer):
        """
        Private method to update the collected fixer related statistics.
        
        @param fixer reference to the PEP 8 fixer (Pep8Fixer)
        """
        self.__statistics["_IssuesFixed"] += fixer.fixed
    
    def __resetStatistics(self):
        """
        Private slot to reset the statistics data.
        """
        self.__statistics = {}
        self.__statistics["_FilesCount"] = 0
        self.__statistics["_FilesIssues"] = 0
        self.__statistics["_IssuesFixed"] = 0
    
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
        if self.__data is None or \
           len(self.__data) < 6:
            # initialize the data structure
            self.__data = {
                "ExcludeFiles": "",
                "ExcludeMessages": pep8.DEFAULT_IGNORE,
                "IncludeMessages": "",
                "RepeatMessages": False,
                "FixCodes": "",
                "FixIssues": False,
            }
        if "MaxLineLength" not in self.__data:
            self.__data["MaxLineLength"] = pep8.MAX_LINE_LENGTH
        if "HangClosing" not in self.__data:
            self.__data["HangClosing"] = False
        if "NoFixCodes" not in self.__data:
            self.__data["NoFixCodes"] = "E501"
        if "DocstringType" not in self.__data:
            self.__data["DocstringType"] = "pep257"
        
        self.excludeFilesEdit.setText(self.__data["ExcludeFiles"])
        self.excludeMessagesEdit.setText(self.__data["ExcludeMessages"])
        self.includeMessagesEdit.setText(self.__data["IncludeMessages"])
        self.repeatCheckBox.setChecked(self.__data["RepeatMessages"])
        self.fixIssuesEdit.setText(self.__data["FixCodes"])
        self.noFixIssuesEdit.setText(self.__data["NoFixCodes"])
        self.fixIssuesCheckBox.setChecked(self.__data["FixIssues"])
        self.lineLengthSpinBox.setValue(self.__data["MaxLineLength"])
        self.hangClosingCheckBox.setChecked(self.__data["HangClosing"])
        self.docTypeComboBox.setCurrentIndex(
            self.docTypeComboBox.findData(self.__data["DocstringType"]))
    
    def start(self, fn, save=False, repeat=None):
        """
        Public slot to start the PEP 8 check.
        
        @param fn file or list of files or directory to be checked
                (string or list of strings)
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
        self.statisticsButton.setEnabled(False)
        self.showButton.setEnabled(False)
        self.fixButton.setEnabled(False)
        self.startButton.setEnabled(False)
        if repeat is not None:
            self.repeatCheckBox.setChecked(repeat)
        self.checkProgress.setVisible(True)
        QApplication.processEvents()
        
        self.__resetStatistics()
        
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
        
        if len(py3files) + len(py2files) > 0:
            self.checkProgress.setMaximum(len(py3files) + len(py2files))
            self.checkProgressLabel.setVisible(
                len(py3files) + len(py2files) > 1)
            QApplication.processEvents()
            
            # extract the configuration values
            excludeMessages = self.excludeMessagesEdit.text()
            includeMessages = self.includeMessagesEdit.text()
            repeatMessages = self.repeatCheckBox.isChecked()
            fixCodes = self.fixIssuesEdit.text()
            noFixCodes = self.noFixIssuesEdit.text()
            fixIssues = self.fixIssuesCheckBox.isChecked() and repeatMessages
            maxLineLength = self.lineLengthSpinBox.value()
            hangClosing = self.hangClosingCheckBox.isChecked()
            docType = self.docTypeComboBox.itemData(
                self.docTypeComboBox.currentIndex())
            
            try:
                # disable updates of the list for speed
                self.resultList.setUpdatesEnabled(False)
                self.resultList.setSortingEnabled(False)
                
                # now go through all the files
                progress = 0
                for file in sorted(py3files + py2files):
                    self.checkProgress.setValue(progress)
                    self.checkProgressLabel.setPath(file)
                    QApplication.processEvents()
                    
                    if self.cancelled:
                        self.__resort()
                        return
                    
                    self.__lastFileItem = None
                    
                    try:
                        source, encoding = Utilities.readEncodedFile(file)
                        source = source.splitlines(True)
                    except (UnicodeError, IOError) as msg:
                        self.noResults = False
                        self.__createResultItem(file, "1", "1",
                            self.trUtf8("Error: {0}").format(str(msg))\
                                .rstrip()[1:-1], False, False)
                        progress += 1
                        continue
                    
                    stats = {}
                    flags = Utilities.extractFlags(source)
                    ext = os.path.splitext(file)[1]
                    if fixIssues:
                        from .Pep8Fixer import Pep8Fixer
                        fixer = Pep8Fixer(self.__project, file, source,
                                          fixCodes, noFixCodes, maxLineLength,
                                          True)  # always fix in place
                    else:
                        fixer = None
                    if ("FileType" in flags and
                        flags["FileType"] in ["Python", "Python2"]) or \
                       file in py2files or \
                       (ext in [".py", ".pyw"] and \
                        Preferences.getProject("DeterminePyFromProject") and \
                        self.__project.isOpen() and \
                        self.__project.isProjectFile(file) and \
                        self.__project.getProjectLanguage() in ["Python",
                                                                "Python2"]):
                        from .Pep8Checker import Pep8Py2Checker
                        report = Pep8Py2Checker(file, [],
                            repeat=repeatMessages,
                            select=includeMessages,
                            ignore=excludeMessages,
                            max_line_length=maxLineLength,
                            hang_closing=hangClosing,
                            docType=docType,
                        )
                        errors = report.errors[:]
                        stats.update(report.counters)
                    else:
                        if includeMessages:
                            select = [s.strip() for s in includeMessages.split(',')
                                      if s.strip()]
                        else:
                            select = []
                        if excludeMessages:
                            ignore = [i.strip() for i in excludeMessages.split(',')
                                      if i.strip()]
                        else:
                            ignore = []
                        
                        # check PEP-8
                        styleGuide = pep8.StyleGuide(
                            reporter=Pep8Report,
                            repeat=repeatMessages,
                            select=select,
                            ignore=ignore,
                            max_line_length=maxLineLength,
                            hang_closing=hangClosing,
                        )
                        report = styleGuide.check_files([file])
                        stats.update(report.counters)
                        
                        # check PEP-257
                        pep257Checker = Pep257Checker(
                            source, file, select, ignore, [], repeatMessages,
                            maxLineLength=maxLineLength, docType=docType)
                        pep257Checker.run()
                        stats.update(pep257Checker.counters)
                        
                        errors = report.errors + pep257Checker.errors
                    
                    deferredFixes = {}
                    for error in errors:
                        fname, lineno, position, text = error
                        if lineno > len(source):
                            lineno = len(source)
                        if "__IGNORE_WARNING__" not in Utilities.extractLineFlags(
                                source[lineno - 1].strip()):
                            self.noResults = False
                            if fixer:
                                res, msg, id_ = fixer.fixIssue(lineno, position, text)
                                if res == 1:
                                    text += "\n" + \
                                            self.trUtf8("Fix: {0}").format(msg)
                                    self.__createResultItem(
                                        fname, lineno, position, text, True, True)
                                elif res == 0:
                                    self.__createResultItem(
                                        fname, lineno, position, text, False, True)
                                else:
                                    itm = self.__createResultItem(
                                        fname, lineno, position,
                                        text, False, False)
                                    deferredFixes[id_] = itm
                            else:
                                self.__createResultItem(
                                    fname, lineno, position, text, False, False)
                    if fixer:
                        deferredResults = fixer.finalize()
                        for id_ in deferredResults:
                            fixed, msg = deferredResults[id_]
                            itm = deferredFixes[id_]
                            if fixed == 1:
                                text = "\n" + self.trUtf8("Fix: {0}").format(msg)
                                self.__modifyFixedResultItem(itm, text, True)
                            else:
                                self.__modifyFixedResultItem(itm, "", False)
                        fixer.saveFile(encoding)
                    self.__updateStatistics(stats, fixer)
                    progress += 1
            finally:
                # reenable updates of the list
                self.resultList.setSortingEnabled(True)
                self.resultList.setUpdatesEnabled(True)
            self.checkProgress.setValue(progress)
            self.checkProgressLabel.setPath("")
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
        self.statisticsButton.setEnabled(True)
        self.showButton.setEnabled(True)
        self.startButton.setEnabled(True)
        
        if self.noResults:
            QTreeWidgetItem(self.resultList, [self.trUtf8('No issues found.')])
            QApplication.processEvents()
            self.statisticsButton.setEnabled(False)
            self.showButton.setEnabled(False)
            self.__clearErrors()
        else:
            self.statisticsButton.setEnabled(True)
            self.showButton.setEnabled(True)
        self.resultList.header().resizeSections(QHeaderView.ResizeToContents)
        self.resultList.header().setStretchLastSection(True)
        
        self.checkProgress.setVisible(False)
        self.checkProgressLabel.setVisible(False)
    
    @pyqtSlot()
    def on_startButton_clicked(self):
        """
        Private slot to start a PEP 8 check run.
        """
        if self.__forProject:
            data = {
                "ExcludeFiles": self.excludeFilesEdit.text(),
                "ExcludeMessages": self.excludeMessagesEdit.text(),
                "IncludeMessages": self.includeMessagesEdit.text(),
                "RepeatMessages": self.repeatCheckBox.isChecked(),
                "FixCodes": self.fixIssuesEdit.text(),
                "NoFixCodes": self.noFixIssuesEdit.text(),
                "FixIssues": self.fixIssuesCheckBox.isChecked(),
                "MaxLineLength": self.lineLengthSpinBox.value(),
                "HangClosing": self.hangClosingCheckBox.isChecked(),
                "DocstringType": self.docTypeComboBox.itemData(
                    self.docTypeComboBox.currentIndex()),
            }
            if data != self.__data:
                self.__data = data
                self.__project.setData("CHECKERSPARMS", "Pep8Checker",
                                       self.__data)
        
        self.resultList.clear()
        self.noResults = True
        self.cancelled = False
        self.start(self.__fileOrFileList)
    
    def __selectCodes(self, edit, showFixCodes):
        """
        Private method to select message codes via a selection dialog.
        
        @param edit reference of the line edit to be populated (QLineEdit)
        @param showFixCodes flag indicating to show a list of fixable
            issues (boolean)
        """
        from .Pep8CodeSelectionDialog import Pep8CodeSelectionDialog
        dlg = Pep8CodeSelectionDialog(edit.text(), showFixCodes, self)
        if dlg.exec_() == QDialog.Accepted:
            edit.setText(dlg.getSelectedCodes())
    
    @pyqtSlot()
    def on_excludeMessagesSelectButton_clicked(self):
        """
        Private slot to select the message codes to be excluded via a
        selection dialog.
        """
        self.__selectCodes(self.excludeMessagesEdit, False)
    
    @pyqtSlot()
    def on_includeMessagesSelectButton_clicked(self):
        """
        Private slot to select the message codes to be included via a
        selection dialog.
        """
        self.__selectCodes(self.includeMessagesEdit, False)
    
    @pyqtSlot()
    def on_fixIssuesSelectButton_clicked(self):
        """
        Private slot to select the issue codes to be fixed via a
        selection dialog.
        """
        self.__selectCodes(self.fixIssuesEdit, True)
    
    @pyqtSlot()
    def on_noFixIssuesSelectButton_clicked(self):
        """
        Private slot to select the issue codes not to be fixed via a
        selection dialog.
        """
        self.__selectCodes(self.noFixIssuesEdit, True)
    
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
            code = item.data(0, self.codeRole)
            
            vm = e5App().getObject("ViewManager")
            vm.openSourceFile(fn, lineno=lineno, pos=position + 1)
            editor = vm.getOpenEditor(fn)
            
            if code == "E901":
                editor.toggleSyntaxError(lineno, 0, True, message, True)
            else:
                editor.toggleFlakesWarning(
                    lineno, True, message, warningType=editor.WarningStyle)
    
    @pyqtSlot()
    def on_resultList_itemSelectionChanged(self):
        """
        Private slot to change the dialog state depending on the selection.
        """
        self.fixButton.setEnabled(len(self.__getSelectedFixableItems()) > 0)
    
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
    def on_statisticsButton_clicked(self):
        """
        Private slot to show the statistics dialog.
        """
        from .Pep8StatisticsDialog import Pep8StatisticsDialog
        dlg = Pep8StatisticsDialog(self.__statistics, self)
        dlg.exec_()
    
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
        self.repeatCheckBox.setChecked(Preferences.toBool(
            Preferences.Prefs.settings.value("PEP8/RepeatMessages")))
        self.fixIssuesEdit.setText(Preferences.Prefs.settings.value(
            "PEP8/FixCodes"))
        self.noFixIssuesEdit.setText(Preferences.Prefs.settings.value(
            "PEP8/NoFixCodes", "E501"))
        self.fixIssuesCheckBox.setChecked(Preferences.toBool(
            Preferences.Prefs.settings.value("PEP8/FixIssues")))
        self.lineLengthSpinBox.setValue(int(Preferences.Prefs.settings.value(
            "PEP8/MaxLineLength", pep8.MAX_LINE_LENGTH)))
        self.hangClosingCheckBox.setChecked(Preferences.toBool(
            Preferences.Prefs.settings.value("PEP8/HangClosing")))
        self.docTypeComboBox.setCurrentIndex(self.docTypeComboBox.findData(
            Preferences.Prefs.settings.value("PEP8/DocstringType", "pep257")))
    
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
        Preferences.Prefs.settings.setValue("PEP8/RepeatMessages",
            self.repeatCheckBox.isChecked())
        Preferences.Prefs.settings.setValue("PEP8/FixCodes",
            self.fixIssuesEdit.text())
        Preferences.Prefs.settings.setValue("PEP8/NoFixCodes",
            self.noFixIssuesEdit.text())
        Preferences.Prefs.settings.setValue("PEP8/FixIssues",
            self.fixIssuesCheckBox.isChecked())
        Preferences.Prefs.settings.setValue("PEP8/MaxLineLength",
            self.lineLengthSpinBox.value())
        Preferences.Prefs.settings.setValue("PEP8/HangClosing",
            self.hangClosingCheckBox.isChecked())
        Preferences.Prefs.settings.setValue("PEP8/DocstringType",
            self.docTypeComboBox.itemData(
                self.docTypeComboBox.currentIndex()))
    
    @pyqtSlot()
    def on_resetDefaultButton_clicked(self):
        """
        Private slot to reset the configuration values to their default values.
        """
        Preferences.Prefs.settings.setValue("PEP8/ExcludeFilePatterns", "")
        Preferences.Prefs.settings.setValue("PEP8/ExcludeMessages",
            pep8.DEFAULT_IGNORE)
        Preferences.Prefs.settings.setValue("PEP8/IncludeMessages", "")
        Preferences.Prefs.settings.setValue("PEP8/RepeatMessages", False)
        Preferences.Prefs.settings.setValue("PEP8/FixCodes", "")
        Preferences.Prefs.settings.setValue("PEP8/NoFixCodes", "E501")
        Preferences.Prefs.settings.setValue("PEP8/FixIssues", False)
        Preferences.Prefs.settings.setValue("PEP8/MaxLineLength",
            pep8.MAX_LINE_LENGTH)
        Preferences.Prefs.settings.setValue("PEP8/HangClosing", False)
        Preferences.Prefs.settings.setValue("PEP8/DocstringType", "pep257")
    
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
        elif button == self.statisticsButton:
            self.on_statisticsButton_clicked()
    
    def __clearErrors(self):
        """
        Private method to clear all warning markers of open editors.
        """
        vm = e5App().getObject("ViewManager")
        openFiles = vm.getOpenFilenames()
        for file in openFiles:
            editor = vm.getOpenEditor(file)
            editor.clearFlakesWarnings()
    
    @pyqtSlot()
    def on_fixButton_clicked(self):
        """
        Private slot to fix selected issues.
        """
        from .Pep8Fixer import Pep8Fixer
        
        # build a dictionary of issues to fix
        fixableItems = self.__getSelectedFixableItems()
        fixesDict = {}      # dictionary of lists of tuples containing
                            # the issue and the item
        for itm in fixableItems:
            filename = itm.data(0, self.filenameRole)
            if filename not in fixesDict:
                fixesDict[filename] = []
            fixesDict[filename].append((
                (itm.data(0, self.lineRole),
                 itm.data(0, self.positionRole),
                 "{0} {1}".format(itm.data(0, self.codeRole), 
                                  itm.data(0, self.messageRole))),
                itm
            ))
        
        # extract the configuration values
        fixCodes = self.fixIssuesEdit.text()
        noFixCodes = self.noFixIssuesEdit.text()
        maxLineLength = self.lineLengthSpinBox.value()
        
        # now go through all the files
        if fixesDict:
            self.checkProgress.setMaximum(len(fixesDict))
            progress = 0
            for file in fixesDict:
                self.checkProgress.setValue(progress)
                QApplication.processEvents()
                
                try:
                    source, encoding = Utilities.readEncodedFile(file)
                    source = source.splitlines(True)
                except (UnicodeError, IOError) as msg:
                    # skip silently because that should not happen
                    progress += 1
                    continue
                
                deferredFixes = {}
                # TODO: add docstring type
                fixer = Pep8Fixer(self.__project, file, source,
                                  fixCodes, noFixCodes, maxLineLength,
                                  True)  # always fix in place
                errors = fixesDict[file]
                errors.sort(key=lambda a: a[0][0])
                for error in errors:
                    (lineno, position, text), itm = error
                    if lineno > len(source):
                        lineno = len(source)
                    fixed, msg, id_ = fixer.fixIssue(lineno, position, text)
                    if fixed == 1:
                        text = "\n" + self.trUtf8("Fix: {0}").format(msg)
                        self.__modifyFixedResultItem(itm, text, True)
                    elif fixed == 0:
                        self.__modifyFixedResultItem(itm, "", False)
                    else:
                        # remember item for the deferred fix
                        deferredFixes[id_] = itm
                deferredResults = fixer.finalize()
                for id_ in deferredResults:
                    fixed, msg = deferredResults[id_]
                    itm = deferredFixes[id_]
                    if fixed == 1:
                        text = "\n" + self.trUtf8("Fix: {0}").format(msg)
                        self.__modifyFixedResultItem(itm, text, True)
                    else:
                        self.__modifyFixedResultItem(itm, "", False)
                fixer.saveFile(encoding)
                
                self.__updateFixerStatistics(fixer)
                progress += 1
            
            self.checkProgress.setValue(progress)
            QApplication.processEvents()

    def __getSelectedFixableItems(self):
        """
        Private method to extract all selected items for fixable issues.
        
        @return selected items for fixable issues (list of QTreeWidgetItem)
        """
        fixableItems = []
        for itm in self.resultList.selectedItems():
            if itm.childCount() > 0:
                for index in range(itm.childCount()):
                    citm = itm.child(index)
                    if self.__itemFixable(citm) and not citm in fixableItems:
                        fixableItems.append(citm)
            elif self.__itemFixable(itm) and not itm in fixableItems:
                fixableItems.append(itm)
        
        return fixableItems
    
    def __itemFixable(self, itm):
        """
        Private method to check, if an item has a fixable issue.
        
        @param itm item to be checked (QTreeWidgetItem)
        @return flag indicating a fixable issue (boolean)
        """
        return itm.data(0, self.fixableRole)
