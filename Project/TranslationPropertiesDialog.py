# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Translations Properties dialog.
"""

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from E5Gui.E5Completers import E5FileCompleter, E5DirCompleter

from .Ui_TranslationPropertiesDialog import Ui_TranslationPropertiesDialog

import Utilities

class TranslationPropertiesDialog(QDialog, Ui_TranslationPropertiesDialog):
    """
    Class implementing the Translations Properties dialog.
    """
    def __init__(self, project, new, parent):
        """
        Constructor
        
        @param project reference to the project object
        @param new flag indicating the generation of a new project
        @param parent parent widget of this dialog (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.project = project
        self.parent = parent
        
        self.transPatternCompleter = E5FileCompleter(self.transPatternEdit)
        self.transBinPathCompleter = E5DirCompleter(self.transBinPathEdit)
        self.exceptionCompleter = E5FileCompleter(self.exceptionEdit)
        
        self.initFilters()
        if not new:
            self.initDialog()
        
    def initFilters(self):
        """
        Public method to initialize the filters.
        """
        patterns = {
            "SOURCES"    : [], 
            "FORMS"      : [], 
        }
        for pattern, filetype in list(self.project.pdata["FILETYPES"].items()):
            if filetype in patterns:
                patterns[filetype].append(pattern)
        self.filters = self.trUtf8("Source Files ({0});;")\
            .format(" ".join(patterns["SOURCES"]))
        if self.parent.getProjectType() in ["Qt4", "E4Plugin", "PySide"]:
            self.filters += self.trUtf8("Forms Files ({0});;")\
                .format(" ".join(patterns["FORMS"]))
        self.filters += self.trUtf8("All Files (*)")
        
    def initDialog(self):
        """
        Public method to initialize the dialogs data.
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        try:
            self.transPatternEdit.setText(os.path.join(\
                self.project.ppath, self.project.pdata["TRANSLATIONPATTERN"][0]))
        except IndexError:
            pass
        try:
            self.transBinPathEdit.setText(os.path.join(\
                self.project.ppath, self.project.pdata["TRANSLATIONSBINPATH"][0]))
        except IndexError:
            pass
        self.exceptionsList.clear()
        for texcept in self.project.pdata["TRANSLATIONEXCEPTIONS"]:
            if texcept:
                self.exceptionsList.addItem(texcept)
        
    @pyqtSlot()
    def on_transPatternButton_clicked(self):
        """
        Private slot to display a file selection dialog.
        """
        tp = self.transPatternEdit.text()
        if "%language%" in tp:
            tp = tp.split("%language%")[0]
        tsfile = QFileDialog.getOpenFileName(\
            self,
            self.trUtf8("Select translation file"),
            tp,
            "")
        
        if tsfile:
            self.transPatternEdit.setText(Utilities.toNativeSeparators(tsfile))
        
    @pyqtSlot(str)
    def on_transPatternEdit_textChanged(self, txt):
        """
        Private slot to check the translation pattern for correctness.
        
        @param txt text of the transPatternEdit lineedit (string)
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            "%language%" in txt)
        
    @pyqtSlot()
    def on_transBinPathButton_clicked(self):
        """
        Private slot to display a directory selection dialog.
        """
        directory = QFileDialog.getExistingDirectory(\
            self,
            self.trUtf8("Select directory for binary translations"),
            self.transBinPathEdit.text(),
            QFileDialog.Options(QFileDialog.Option(0)))
        
        if directory:
            self.transBinPathEdit.setText(Utilities.toNativeSeparators(directory))
        
    @pyqtSlot()
    def on_deleteExceptionButton_clicked(self):
        """
        Private slot to delete the currently selected entry of the listwidget.
        """
        row = self.exceptionsList.currentRow()
        itm = self.exceptionsList.takeItem(row)
        del itm
        row = self.exceptionsList.currentRow()
        self.on_exceptionsList_currentRowChanged(row)
        
    @pyqtSlot()
    def on_addExceptionButton_clicked(self):
        """
        Private slot to add the shown exception to the listwidget.
        """
        if self.project.ppath == '':
            ppath = self.parent.getPPath()
        else:
            ppath = self.project.ppath
        texcept = self.exceptionEdit.text()
        texcept = texcept.replace(ppath + os.sep, "")
        if texcept.endswith(os.sep):
            texcept = texcept[:-1]
        if texcept:
            QListWidgetItem(texcept, self.exceptionsList)
            self.exceptionEdit.clear()
        row = self.exceptionsList.currentRow()
        self.on_exceptionsList_currentRowChanged(row)
        
    @pyqtSlot()
    def on_exceptFileButton_clicked(self):
        """
        Private slot to select a file to exempt from translation.
        """
        texcept = QFileDialog.getOpenFileName(\
            self,
            self.trUtf8("Exempt file from translation"),
            self.project.ppath,
            self.filters)
        if texcept:
            self.exceptionEdit.setText(Utilities.toNativeSeparators(texcept))
        
    @pyqtSlot()
    def on_exceptDirButton_clicked(self):
        """
        Private slot to select a file to exempt from translation.
        """
        texcept = QFileDialog.getExistingDirectory(\
            self,
            self.trUtf8("Exempt directory from translation"),
            self.project.ppath,
            QFileDialog.Options(QFileDialog.ShowDirsOnly))
        if texcept:
            self.exceptionEdit.setText(Utilities.toNativeSeparators(texcept))
        
    def on_exceptionsList_currentRowChanged(self, row):
        """
        Private slot to handle the currentRowChanged signal of the exceptions list.
        
        @param row the current row (integer)
        """
        if row == -1:
            self.deleteExceptionButton.setEnabled(False)
        else:
            self.deleteExceptionButton.setEnabled(True)
        
    def on_exceptionEdit_textChanged(self, txt):
        """
        Private slot to handle the textChanged signal of the exception edit.
        
        @param txt the text of the exception edit (string)
        """
        self.addExceptionButton.setEnabled(txt != "")
        
    def storeData(self):
        """
        Public method to store the entered/modified data.
        """
        tp = Utilities.toNativeSeparators(self.transPatternEdit.text())
        if tp:
            tp = tp.replace(self.project.ppath + os.sep, "")
            self.project.pdata["TRANSLATIONPATTERN"] = [tp]
            self.project.translationsRoot = tp.split("%language%")[0]
        else:
            self.project.pdata["TRANSLATIONPATTERN"] = []
        tp = Utilities.toNativeSeparators(self.transBinPathEdit.text())
        if tp:
            tp = tp.replace(self.project.ppath + os.sep, "")
            self.project.pdata["TRANSLATIONSBINPATH"] = [tp]
        else:
            self.project.pdata["TRANSLATIONSBINPATH"] = []
        exceptList = []
        for i in range(self.exceptionsList.count()):
            exceptList.append(self.exceptionsList.item(i).text())
        self.project.pdata["TRANSLATIONEXCEPTIONS"] = exceptList[:]