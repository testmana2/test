# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show the results of the code style check.
"""

from __future__ import unicode_literals

import os
import fnmatch

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem, QAbstractButton, \
    QDialogButtonBox, QApplication, QHeaderView

from E5Gui.E5Application import e5App

from .Ui_CodeStyleCheckerDialog import Ui_CodeStyleCheckerDialog

import UI.PixmapCache
import Preferences
import Utilities

from . import pep8


class CodeStyleCheckerDialog(QDialog, Ui_CodeStyleCheckerDialog):
    """
    Class implementing a dialog to show the results of the code style check.
    """
    filenameRole = Qt.UserRole + 1
    lineRole = Qt.UserRole + 2
    positionRole = Qt.UserRole + 3
    messageRole = Qt.UserRole + 4
    fixableRole = Qt.UserRole + 5
    codeRole = Qt.UserRole + 6
    ignoredRole = Qt.UserRole + 7
    
    def __init__(self, styleCheckService, parent=None):
        """
        Constructor
        
        @param styleCheckService reference to the service
            (CodeStyleCheckService)
        @param parent reference to the parent widget (QWidget)
        """
        super(CodeStyleCheckerDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.excludeMessagesSelectButton.setIcon(
            UI.PixmapCache.getIcon("select.png"))
        self.includeMessagesSelectButton.setIcon(
            UI.PixmapCache.getIcon("select.png"))
        self.fixIssuesSelectButton.setIcon(
            UI.PixmapCache.getIcon("select.png"))
        self.noFixIssuesSelectButton.setIcon(
            UI.PixmapCache.getIcon("select.png"))
        
        self.docTypeComboBox.addItem(self.tr("PEP-257"), "pep257")
        self.docTypeComboBox.addItem(self.tr("Eric"), "eric")
        
        self.statisticsButton = self.buttonBox.addButton(
            self.tr("Statistics..."), QDialogButtonBox.ActionRole)
        self.statisticsButton.setToolTip(
            self.tr("Press to show some statistics for the last run"))
        self.statisticsButton.setEnabled(False)
        self.showButton = self.buttonBox.addButton(
            self.tr("Show"), QDialogButtonBox.ActionRole)
        self.showButton.setToolTip(
            self.tr("Press to show all files containing an issue"))
        self.showButton.setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)
        
        self.resultList.headerItem().setText(self.resultList.columnCount(), "")
        self.resultList.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.checkProgress.setVisible(False)
        self.checkProgressLabel.setVisible(False)
        self.checkProgressLabel.setMaximumWidth(600)
        
        self.styleCheckService = styleCheckService
        self.styleCheckService.styleChecked.connect(self.__processResult)
        self.filename = None
        
        self.noResults = True
        self.cancelled = False
        self.__lastFileItem = None
        
        self.__fileOrFileList = ""
        self.__project = None
        self.__forProject = False
        self.__data = {}
        self.__statistics = {}
        self.__onlyFixes = {}
        
        self.on_loadDefaultButton_clicked()
    
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.resultList.sortItems(self.resultList.sortColumn(),
                                  self.resultList.header().sortIndicatorOrder()
                                  )
    
    def __createResultItem(self, file, line, pos, message, fixed, autofixing,
                           ignored):
        """
        Private method to create an entry in the result list.
        
        @param file file name of the file (string)
        @param line line number of issue (integer or string)
        @param pos character position of issue (integer or string)
        @param message message text (string)
        @param fixed flag indicating a fixed issue (boolean)
        @param autofixing flag indicating, that we are fixing issues
            automatically (boolean)
        @param ignored flag indicating an ignored issue (boolean)
        @return reference to the created item (QTreeWidgetItem)
        """
        from .CodeStyleFixer import FixableCodeStyleIssues
        
        if self.__lastFileItem is None:
            # It's a new file
            self.__lastFileItem = QTreeWidgetItem(self.resultList, [file])
            self.__lastFileItem.setFirstColumnSpanned(True)
            self.__lastFileItem.setExpanded(True)
            self.__lastFileItem.setData(0, self.filenameRole, file)
        
        fixable = False
        code, message = message.split(None, 1)
        itm = QTreeWidgetItem(
            self.__lastFileItem,
            ["{0:6}".format(line), code, message])
        if code.startswith(("W", "-")):
            itm.setIcon(1, UI.PixmapCache.getIcon("warning.png"))
        elif code.startswith("N"):
            itm.setIcon(1, UI.PixmapCache.getIcon("namingError.png"))
        elif code.startswith("D"):
            itm.setIcon(1, UI.PixmapCache.getIcon("docstringError.png"))
        else:
            itm.setIcon(1, UI.PixmapCache.getIcon("syntaxError.png"))
        if fixed:
            itm.setIcon(0, UI.PixmapCache.getIcon("issueFixed.png"))
        elif code in FixableCodeStyleIssues and not autofixing:
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
        itm.setData(0, self.ignoredRole, ignored)
        
        if ignored:
            font = itm.font(0)
            font.setItalic(True)
            for col in range(itm.columnCount()):
                itm.setFont(col, font)
        
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
            code, message = text.split(None, 1)
            itm.setText(2, message)
            itm.setIcon(0, UI.PixmapCache.getIcon("issueFixed.png"))
            
            itm.setData(0, self.messageRole, message)
        else:
            itm.setIcon(0, QIcon())
        itm.setData(0, self.fixableRole, False)
    
    def __updateStatistics(self, statistics, fixer, ignoredErrors):
        """
        Private method to update the collected statistics.
        
        @param statistics dictionary of statistical data with
            message code as key and message count as value
        @param fixer reference to the code style fixer (CodeStyleFixer)
        @param ignoredErrors number of ignored errors (integer)
        """
        self.__statistics["_FilesCount"] += 1
        stats = [k for k in statistics.keys() if k[0].isupper()]
        if stats:
            self.__statistics["_FilesIssues"] += 1
            for key in statistics:
                if key in self.__statistics:
                    self.__statistics[key] += statistics[key]
                else:
                    self.__statistics[key] = statistics[key]
        self.__statistics["_IssuesFixed"] += fixer
        self.__statistics["_IgnoredErrors"] += ignoredErrors
    
    def __updateFixerStatistics(self, fixer):
        """
        Private method to update the collected fixer related statistics.
        
        @param fixer reference to the code style fixer (CodeStyleFixer)
        """
        self.__statistics["_IssuesFixed"] += fixer
    
    def __resetStatistics(self):
        """
        Private slot to reset the statistics data.
        """
        self.__statistics = {}
        self.__statistics["_FilesCount"] = 0
        self.__statistics["_FilesIssues"] = 0
        self.__statistics["_IssuesFixed"] = 0
        self.__statistics["_IgnoredErrors"] = 0
    
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
        if "ShowIgnored" not in self.__data:
            self.__data["ShowIgnored"] = False
        
        self.excludeFilesEdit.setText(self.__data["ExcludeFiles"])
        self.excludeMessagesEdit.setText(self.__data["ExcludeMessages"])
        self.includeMessagesEdit.setText(self.__data["IncludeMessages"])
        self.repeatCheckBox.setChecked(self.__data["RepeatMessages"])
        self.fixIssuesEdit.setText(self.__data["FixCodes"])
        self.noFixIssuesEdit.setText(self.__data["NoFixCodes"])
        self.fixIssuesCheckBox.setChecked(self.__data["FixIssues"])
        self.ignoredCheckBox.setChecked(self.__data["ShowIgnored"])
        self.lineLengthSpinBox.setValue(self.__data["MaxLineLength"])
        self.hangClosingCheckBox.setChecked(self.__data["HangClosing"])
        self.docTypeComboBox.setCurrentIndex(
            self.docTypeComboBox.findData(self.__data["DocstringType"]))
    
    def start(self, fn, save=False, repeat=None):
        """
        Public slot to start the code style check.
        
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
        
        if save:
            self.__fileOrFileList = fn
        
        if isinstance(fn, list):
            self.files = fn[:]
        elif os.path.isdir(fn):
            self.files = []
            extensions = set(Preferences.getPython("PythonExtensions") +
                             Preferences.getPython("Python3Extensions"))
            for ext in extensions:
                self.files.extend(Utilities.direntries(
                    fn, True, '*{0}'.format(ext), 0))
        else:
            self.files = [fn]

        # filter the list depending on the filter string
        if self.files:
            filterString = self.excludeFilesEdit.text()
            filterList = [f.strip() for f in filterString.split(",")
                          if f.strip()]
            for filter in filterList:
                self.files = \
                    [f for f in self.files
                     if not fnmatch.fnmatch(f, filter.strip())]

        self.__resetStatistics()
        self.__clearErrors(self.files)
        
        if len(self.files) > 0:
            self.checkProgress.setMaximum(len(self.files))
            self.checkProgressLabel.setVisible(len(self.files) > 1)
            self.checkProgress.setVisible(len(self.files) > 1)
            QApplication.processEvents()
            
            # extract the configuration values
            excludeMessages = self.excludeMessagesEdit.text()
            includeMessages = self.includeMessagesEdit.text()
            repeatMessages = self.repeatCheckBox.isChecked()
            fixCodes = self.fixIssuesEdit.text()
            noFixCodes = self.noFixIssuesEdit.text()
            fixIssues = self.fixIssuesCheckBox.isChecked() and repeatMessages
            self.showIgnored = self.ignoredCheckBox.isChecked() and \
                repeatMessages
            maxLineLength = self.lineLengthSpinBox.value()
            hangClosing = self.hangClosingCheckBox.isChecked()
            docType = self.docTypeComboBox.itemData(
                self.docTypeComboBox.currentIndex())
            
            self.__options = [excludeMessages, includeMessages, repeatMessages,
                              fixCodes, noFixCodes, fixIssues, maxLineLength,
                              hangClosing, docType]
            
            # now go through all the files
            self.progress = 0
            self.files.sort()
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

        if self.cancelled:
            self.__resort()
            return
        
        self.__lastFileItem = None
        
        if codestring:
            self.source = codestring
        else:
            try:
                self.source, encoding = Utilities.readEncodedFile(
                    self.filename)
                if encoding.endswith(
                        ('-selected', '-default', '-guessed', '-ignore')):
                    encoding = encoding.rsplit('-', 1)[0]
                
                self.source = self.source.splitlines(True)
            except (UnicodeError, IOError) as msg:
                self.noResults = False
                self.__createResultItem(
                    self.filename, 1, 1,
                    self.tr("Error: {0}").format(str(msg))
                        .rstrip(), False, False, False)
                self.progress += 1
                # Continue with next file
                self.check()
                return
        
        errors = []
        self.__itms = []
        for error, itm in self.__onlyFixes.pop(self.filename, []):
            errors.append(error)
            self.__itms.append(itm)
        
        eol = self.__getEol(self.filename)
        args = self.__options + [
            errors, eol, encoding, Preferences.getEditor("CreateBackupFile")
        ]
        self.styleCheckService.styleCheck(
            None, self.filename, self.source, args)

    def __processResult(self, fn, codeStyleCheckerStats, fixes, results):
        """
        Private slot called after perfoming a style check on one file.
        
        @param fn filename of the just checked file (str)
        @param codeStyleCheckerStats stats of style and name check (dict)
        @param fixes number of applied fixes (int)
        @param results tuple for each found violation of style (tuple of
            lineno (int), position (int), text (str), ignored (bool),
            fixed (bool), autofixing (bool))
        """
        # Check if it's the requested file, otherwise ignore signal
        if fn != self.filename:
            return
        
        # disable updates of the list for speed
        self.resultList.setUpdatesEnabled(False)
        self.resultList.setSortingEnabled(False)
        
        fixed = None
        ignoredErrors = 0
        if self.__itms:
            for itm, (lineno, position, text, ignored, fixed, autofixing) in \
                    zip(self.__itms, results):
                self.__modifyFixedResultItem(itm, text, fixed)
            self.__updateFixerStatistics(fixes)
        else:
            for lineno, position, text, ignored, fixed, autofixing in results:
                if ignored:
                    ignoredErrors += 1
                    if self.showIgnored:
                        text = self.tr("{0} (ignored)").format(text)
                    else:
                        continue
                self.noResults = False
                self.__createResultItem(
                    fn, lineno, position, text, fixed, autofixing, ignored)

            self.__updateStatistics(
                codeStyleCheckerStats, fixes, ignoredErrors)
        
        if fixed:
            vm = e5App().getObject("ViewManager")
            editor = vm.getOpenEditor(fn)
            if editor:
                editor.refresh()
        
        self.progress += 1
        
        self.__resort()
        # reenable updates of the list
        self.resultList.setSortingEnabled(True)
        self.resultList.setUpdatesEnabled(True)
        
        self.checkProgress.setValue(self.progress)
        QApplication.processEvents()
        
        self.check()
    
    def __finish(self):
        """
        Private slot called when the code style check finished or the user
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
            QTreeWidgetItem(self.resultList, [self.tr('No issues found.')])
            QApplication.processEvents()
            self.statisticsButton.setEnabled(False)
            self.showButton.setEnabled(False)
        else:
            self.statisticsButton.setEnabled(True)
            self.showButton.setEnabled(True)
        self.resultList.header().resizeSections(QHeaderView.ResizeToContents)
        self.resultList.header().setStretchLastSection(True)
        
        self.checkProgress.setVisible(False)
        self.checkProgressLabel.setVisible(False)
    
    def __getEol(self, fn):
        """
        Private method to get the applicable eol string.
        
        @param fn filename where to determine the line ending (str)
        @return eol string (string)
        """
        if self.__project.isOpen() and self.__project.isProjectFile(fn):
            eol = self.__project.getEolString()
        else:
            eol = Utilities.linesep()
        return eol
    
    @pyqtSlot()
    def on_startButton_clicked(self):
        """
        Private slot to start a code style check run.
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
                "ShowIgnored": self.ignoredCheckBox.isChecked(),
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
        from .CodeStyleCodeSelectionDialog import CodeStyleCodeSelectionDialog
        dlg = CodeStyleCodeSelectionDialog(edit.text(), showFixCodes, self)
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
            
            if code in ["E901", "E902"]:
                editor.toggleSyntaxError(lineno, 0, True, message, True)
            else:
                editor.toggleWarning(
                    lineno, 0, True, message, warningType=editor.WarningStyle)
    
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
            editor.clearStyleWarnings()
            for cindex in range(itm.childCount()):
                citm = itm.child(cindex)
                lineno = citm.data(0, self.lineRole)
                message = citm.data(0, self.messageRole)
                editor.toggleWarning(
                    lineno, 0, True, message, warningType=editor.WarningStyle)
        
        # go through the list again to clear warning markers for files,
        # that are ok
        openFiles = vm.getOpenFilenames()
        errorFiles = []
        for index in range(self.resultList.topLevelItemCount()):
            itm = self.resultList.topLevelItem(index)
            errorFiles.append(
                Utilities.normabspath(itm.data(0, self.filenameRole)))
        for file in openFiles:
            if file not in errorFiles:
                editor = vm.getOpenEditor(file)
                editor.clearStyleWarnings()
    
    @pyqtSlot()
    def on_statisticsButton_clicked(self):
        """
        Private slot to show the statistics dialog.
        """
        from .CodeStyleStatisticsDialog import CodeStyleStatisticsDialog
        dlg = CodeStyleStatisticsDialog(self.__statistics, self)
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
        self.ignoredCheckBox.setChecked(Preferences.toBool(
            Preferences.Prefs.settings.value("PEP8/ShowIgnored")))
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
        Preferences.Prefs.settings.setValue(
            "PEP8/ExcludeFilePatterns", self.excludeFilesEdit.text())
        Preferences.Prefs.settings.setValue(
            "PEP8/ExcludeMessages", self.excludeMessagesEdit.text())
        Preferences.Prefs.settings.setValue(
            "PEP8/IncludeMessages", self.includeMessagesEdit.text())
        Preferences.Prefs.settings.setValue(
            "PEP8/RepeatMessages", self.repeatCheckBox.isChecked())
        Preferences.Prefs.settings.setValue(
            "PEP8/FixCodes", self.fixIssuesEdit.text())
        Preferences.Prefs.settings.setValue(
            "PEP8/NoFixCodes", self.noFixIssuesEdit.text())
        Preferences.Prefs.settings.setValue(
            "PEP8/FixIssues", self.fixIssuesCheckBox.isChecked())
        Preferences.Prefs.settings.setValue(
            "PEP8/ShowIgnored", self.ignoredCheckBox.isChecked())
        Preferences.Prefs.settings.setValue(
            "PEP8/MaxLineLength", self.lineLengthSpinBox.value())
        Preferences.Prefs.settings.setValue(
            "PEP8/HangClosing", self.hangClosingCheckBox.isChecked())
        Preferences.Prefs.settings.setValue(
            "PEP8/DocstringType", self.docTypeComboBox.itemData(
                self.docTypeComboBox.currentIndex()))
    
    @pyqtSlot()
    def on_resetDefaultButton_clicked(self):
        """
        Private slot to reset the configuration values to their default values.
        """
        Preferences.Prefs.settings.setValue("PEP8/ExcludeFilePatterns", "")
        Preferences.Prefs.settings.setValue(
            "PEP8/ExcludeMessages", pep8.DEFAULT_IGNORE)
        Preferences.Prefs.settings.setValue("PEP8/IncludeMessages", "")
        Preferences.Prefs.settings.setValue("PEP8/RepeatMessages", False)
        Preferences.Prefs.settings.setValue("PEP8/FixCodes", "")
        Preferences.Prefs.settings.setValue("PEP8/NoFixCodes", "E501")
        Preferences.Prefs.settings.setValue("PEP8/FixIssues", False)
        Preferences.Prefs.settings.setValue("PEP8/ShowIgnored", False)
        Preferences.Prefs.settings.setValue(
            "PEP8/MaxLineLength", pep8.MAX_LINE_LENGTH)
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
    
    def __clearErrors(self, files):
        """
        Private method to clear all warning markers of open editors to be
        checked.
        
        @param files list of files to be checked (list of string)
        """
        vm = e5App().getObject("ViewManager")
        openFiles = vm.getOpenFilenames()
        for file in [f for f in openFiles if f in files]:
            editor = vm.getOpenEditor(file)
            editor.clearStyleWarnings()
    
    @pyqtSlot()
    def on_fixButton_clicked(self):
        """
        Private slot to fix selected issues.
        
        Build a dictionary of issues to fix. Update the initialized __options.
            Then call check with the dict as keyparam to fix selected issues.
        """
        fixableItems = self.__getSelectedFixableItems()
        # dictionary of lists of tuples containing the issue and the item
        fixesDict = {}
        for itm in fixableItems:
            filename = itm.data(0, self.filenameRole)
            if filename not in fixesDict:
                fixesDict[filename] = []
            fixesDict[filename].append((
                (filename, itm.data(0, self.lineRole),
                 itm.data(0, self.positionRole),
                 "{0} {1}".format(itm.data(0, self.codeRole),
                                  itm.data(0, self.messageRole))),
                itm
            ))
    
        # update the configuration values (3: fixCodes, 4: noFixCodes,
        # 5: fixIssues, 6: maxLineLength)
        self.__options[3] = self.fixIssuesEdit.text()
        self.__options[4] = self.noFixIssuesEdit.text()
        self.__options[5] = True
        self.__options[6] = self.lineLengthSpinBox.value()
        
        self.files = list(fixesDict.keys())
        # now go through all the files
        self.progress = 0
        self.files.sort()
        self.cancelled = False
        self.__onlyFixes = fixesDict
        self.check()
    
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
                    if self.__itemFixable(citm) and citm not in fixableItems:
                        fixableItems.append(citm)
            elif self.__itemFixable(itm) and itm not in fixableItems:
                fixableItems.append(itm)
        
        return fixableItems
    
    def __itemFixable(self, itm):
        """
        Private method to check, if an item has a fixable issue.
        
        @param itm item to be checked (QTreeWidgetItem)
        @return flag indicating a fixable issue (boolean)
        """
        return (itm.data(0, self.fixableRole) and
                not itm.data(0, self.ignoredRole))
