# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the file dialog wizard dialog.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

import os

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QDialogButtonBox, QFileDialog

from E5Gui.E5Completers import E5FileCompleter, E5DirCompleter

from .Ui_FileDialogWizardDialog import Ui_FileDialogWizardDialog

import Globals


class FileDialogWizardDialog(QDialog, Ui_FileDialogWizardDialog):
    """
    Class implementing the color dialog wizard dialog.
    
    It displays a dialog for entering the parameters
    for the QFileDialog code generator.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget (QWidget)
        """
        super(FileDialogWizardDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.eStartWithCompleter = E5FileCompleter(self.eStartWith)
        self.eWorkDirCompleter = E5DirCompleter(self.eWorkDir)
        
        self.rSaveFile.toggled[bool].connect(self.__toggleConfirmCheckBox)
        self.rfSaveFile.toggled[bool].connect(self.__toggleConfirmCheckBox)
        self.rDirectory.toggled[bool].connect(self.__toggleGroupsAndTest)
        self.cStartWith.toggled[bool].connect(self.__toggleGroupsAndTest)
        self.cWorkDir.toggled[bool].connect(self.__toggleGroupsAndTest)
        self.cFilters.toggled[bool].connect(self.__toggleGroupsAndTest)
        
        self.bTest = self.buttonBox.addButton(
            self.trUtf8("Test"), QDialogButtonBox.ActionRole)
        
    def __adjustOptions(self, options):
        """
        Private method to adjust the file dialog options.
        
        @param options file dialog options (QFileDialog.Options)
        @return modified options (QFileDialog.Options)
        """
        if Globals.isLinuxPlatform():
            options |= QFileDialog.DontUseNativeDialog
        return options
        
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.bTest:
            self.on_bTest_clicked()
    
    @pyqtSlot()
    def on_bTest_clicked(self):
        """
        Private method to test the selected options.
        """
        if self.rOpenFile.isChecked() or self.rfOpenFile.isChecked():
            if not self.cSymlinks.isChecked():
                options = QFileDialog.Options(QFileDialog.DontResolveSymlinks)
            else:
                options = QFileDialog.Options()
            options = self.__adjustOptions(options)
            QFileDialog.getOpenFileName(
                None,
                self.eCaption.text(),
                self.eStartWith.text(),
                self.eFilters.text(),
                options)
        elif self.rOpenFiles.isChecked() or self.rfOpenFiles.isChecked():
            if not self.cSymlinks.isChecked():
                options = QFileDialog.Options(QFileDialog.DontResolveSymlinks)
            else:
                options = QFileDialog.Options()
            options = self.__adjustOptions(options)
            QFileDialog.getOpenFileNames(
                None,
                self.eCaption.text(),
                self.eStartWith.text(),
                self.eFilters.text(),
                options)
        elif self.rSaveFile.isChecked() or self.rfSaveFile.isChecked():
            if not self.cSymlinks.isChecked():
                options = QFileDialog.Options(QFileDialog.DontResolveSymlinks)
            else:
                options = QFileDialog.Options()
            options = self.__adjustOptions(options)
            QFileDialog.getSaveFileName(
                None,
                self.eCaption.text(),
                self.eStartWith.text(),
                self.eFilters.text(),
                options)
        elif self.rDirectory.isChecked():
            options = QFileDialog.Options()
            if not self.cSymlinks.isChecked():
                options |= QFileDialog.Options(QFileDialog.DontResolveSymlinks)
            if self.cDirOnly.isChecked():
                options |= QFileDialog.Options(QFileDialog.ShowDirsOnly)
            else:
                options |= QFileDialog.Options(QFileDialog.Option(0))
            options = self.__adjustOptions(options)
            QFileDialog.getExistingDirectory(
                None,
                self.eCaption.text(),
                self.eWorkDir.text(),
                options)
        
    def __toggleConfirmCheckBox(self):
        """
        Private slot to enable/disable the confirmation check box.
        """
        self.cConfirmOverwrite.setEnabled(
            self.rSaveFile.isChecked() or self.rfSaveFile.isChecked())
        
    def __toggleGroupsAndTest(self):
        """
        Private slot to enable/disable certain groups and the test button.
        """
        if self.rDirectory.isChecked():
            self.filePropertiesGroup.setEnabled(False)
            self.dirPropertiesGroup.setEnabled(True)
            self.bTest.setDisabled(self.cWorkDir.isChecked())
        else:
            self.filePropertiesGroup.setEnabled(True)
            self.dirPropertiesGroup.setEnabled(False)
            self.bTest.setDisabled(
                self.cStartWith.isChecked() or self.cFilters.isChecked())
        
    def __getCode4(self, indLevel, indString):
        """
        Private method to get the source code for Qt4/Qt5.
        
        @param indLevel indentation level (int)
        @param indString string used for indentation (space or tab) (string)
        @return generated code (string)
        """
        # calculate our indentation level and the indentation string
        il = indLevel + 1
        istring = il * indString
        estring = os.linesep + indLevel * indString
        
        # now generate the code
        code = 'QFileDialog.'
        if self.rOpenFile.isChecked() or self.rfOpenFile.isChecked():
            if self.rOpenFile.isChecked():
                code += 'getOpenFileName({0}{1}'.format(os.linesep, istring)
            else:
                code += 'getOpenFileNameAndFilter({0}{1}'.format(
                    os.linesep, istring)
            code += 'None,{0}{1}'.format(os.linesep, istring)
            if not self.eCaption.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                code += 'self.trUtf8("{0}"),{1}{2}'.format(
                    self.eCaption.text(), os.linesep, istring)
            if not self.eStartWith.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                if self.cStartWith.isChecked():
                    fmt = '{0},{1}{2}'
                else:
                    fmt = 'self.trUtf8("{0}"),{1}{2}'
                code += fmt.format(self.eStartWith.text(), os.linesep, istring)
            if self.eFilters.text() == "":
                code += '""'
            else:
                if self.cFilters.isChecked():
                    fmt = '{0}'
                else:
                    fmt = 'self.trUtf8("{0}")'
                code += fmt.format(self.eFilters.text())
            if self.rfOpenFile.isChecked():
                code += ',{0}{1}None'.format(os.linesep, istring)
            if not self.cSymlinks.isChecked():
                code += \
                    ',{0}{1}QFileDialog.Options(' \
                    'QFileDialog.DontResolveSymlinks)' \
                    .format(os.linesep, istring)
            code += '){0}'.format(estring)
        elif self.rOpenFiles.isChecked() or self.rfOpenFiles.isChecked():
            if self.rOpenFiles.isChecked():
                code += 'getOpenFileNames({0}{1}'.format(os.linesep, istring)
            else:
                code += 'getOpenFileNamesAndFilter({0}{1}'.format(
                    os.linesep, istring)
            code += 'None,{0}{1}'.format(os.linesep, istring)
            if not self.eCaption.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                code += 'self.trUtf8("{0}"),{1}{2}'.format(
                    self.eCaption.text(), os.linesep, istring)
            if not self.eStartWith.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                if self.cStartWith.isChecked():
                    fmt = '{0},{1}{2}'
                else:
                    fmt = 'self.trUtf8("{0}"),{1}{2}'
                code += fmt.format(self.eStartWith.text(), os.linesep, istring)
            if not self.eFilters.text():
                code += '""'
            else:
                if self.cFilters.isChecked():
                    fmt = '{0}'
                else:
                    fmt = 'self.trUtf8("{0}")'
                code += fmt.format(self.eFilters.text())
            if self.rfOpenFiles.isChecked():
                code += ',{0}{1}None'.format(os.linesep, istring)
            if not self.cSymlinks.isChecked():
                code += \
                    ',{0}{1}QFileDialog.Options(' \
                    'QFileDialog.DontResolveSymlinks)' \
                    .format(os.linesep, istring)
            code += '){0}'.format(estring)
        elif self.rSaveFile.isChecked() or self.rfSaveFile.isChecked():
            if self.rSaveFile.isChecked():
                code += 'getSaveFileName({0}{1}'.format(os.linesep, istring)
            else:
                code += 'getSaveFileNameAndFilter({0}{1}'.format(
                    os.linesep, istring)
            code += 'None,{0}{1}'.format(os.linesep, istring)
            if not self.eCaption.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                code += 'self.trUtf8("{0}"),{1}{2}'.format(
                    self.eCaption.text(), os.linesep, istring)
            if not self.eStartWith.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                if self.cStartWith.isChecked():
                    fmt = '{0},{1}{2}'
                else:
                    fmt = 'self.trUtf8("{0}"),{1}{2}'
                code += fmt.format(self.eStartWith.text(), os.linesep, istring)
            if not self.eFilters.text():
                code += '""'
            else:
                if self.cFilters.isChecked():
                    fmt = '{0}'
                else:
                    fmt = 'self.trUtf8("{0}")'
                code += fmt.format(self.eFilters.text())
            if self.rfSaveFile.isChecked():
                code += ',{0}{1}None'.format(os.linesep, istring)
            if (not self.cSymlinks.isChecked()) or \
               (not self.cConfirmOverwrite.isChecked()):
                code += ',{0}{1}QFileDialog.Options('.format(
                    os.linesep, istring)
                if not self.cSymlinks.isChecked():
                    code += 'QFileDialog.DontResolveSymlinks'
                if (not self.cSymlinks.isChecked()) and \
                   (not self.cConfirmOverwrite.isChecked()):
                    code += ' | '
                if not self.cConfirmOverwrite.isChecked():
                    code += 'QFileDialog.DontConfirmOverwrite'
                code += ')'
            code += '){0}'.format(estring)
        elif self.rDirectory.isChecked():
            code += 'getExistingDirectory({0}{1}'.format(os.linesep, istring)
            code += 'None,{0}{1}'.format(os.linesep, istring)
            if not self.eCaption.text():
                code += '"",{0}{1}'.format(os.linesep, istring)
            else:
                code += 'self.trUtf8("{0}"),{1}{2}'.format(
                    self.eCaption.text(), os.linesep, istring)
            if not self.eWorkDir.text():
                code += '""'
            else:
                if self.cWorkDir.isChecked():
                    fmt = '{0}'
                else:
                    fmt = 'self.trUtf8("{0}")'
                code += fmt.format(self.eWorkDir.text())
            code += ',{0}{1}QFileDialog.Options('.format(os.linesep, istring)
            if not self.cSymlinks.isChecked():
                code += 'QFileDialog.DontResolveSymlinks | '
            if self.cDirOnly.isChecked():
                code += 'QFileDialog.ShowDirsOnly'
            else:
                code += 'QFileDialog.Option(0)'
            code += ')){0}'.format(estring)
            
        return code
        
    def getCode(self, indLevel, indString):
        """
        Public method to get the source code.
        
        @param indLevel indentation level (int)
        @param indString string used for indentation (space or tab) (string)
        @return generated code (string)
        """
        return self.__getCode4(indLevel, indString)
