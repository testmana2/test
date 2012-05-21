# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the project properties dialog.
"""

import os

from PyQt4.QtCore import QDir, pyqtSlot
from PyQt4.QtGui import QDialog

from E5Gui.E5Application import e5App
from E5Gui.E5Completers import E5FileCompleter, E5DirCompleter
from E5Gui import E5FileDialog

from .Ui_PropertiesDialog import Ui_PropertiesDialog
from .TranslationPropertiesDialog import TranslationPropertiesDialog
from .SpellingPropertiesDialog import SpellingPropertiesDialog

from VCS.RepositoryInfoDialog import VcsRepositoryInfoDialog

import Utilities


class PropertiesDialog(QDialog, Ui_PropertiesDialog):
    """
    Class implementing the project properties dialog.
    """
    def __init__(self, project, new=True, parent=None, name=None):
        """
        Constructor
        
        @param project reference to the project object
        @param new flag indicating the generation of a new project
        @param parent parent widget of this dialog (QWidget)
        @param name name of this dialog (string)
        """
        # TODO: add a checkbox to select if project should be version controlled
        #       only show the checkbox, if new is true
        #       disable checkbox, if no VCS is available
        super().__init__(parent)
        if name:
            self.setObjectName(name)
        self.setupUi(self)
        
        self.project = project
        self.newProject = new
        self.transPropertiesDlg = None
        self.spellPropertiesDlg = None
        
        self.dirCompleter = E5DirCompleter(self.dirEdit)
        self.mainscriptCompleter = E5FileCompleter(self.mainscriptEdit)
        
        projectLanguages = sorted(
            e5App().getObject("DebugServer").getSupportedLanguages())
        self.languageComboBox.addItems(projectLanguages)
        
        projectTypes = project.getProjectTypes()
        for projectTypeKey in sorted(projectTypes.keys()):
            self.projectTypeComboBox.addItem(projectTypes[projectTypeKey], projectTypeKey)
        
        if not new:
            name = os.path.splitext(self.project.pfile)[0]
            self.nameEdit.setText(os.path.basename(name))
            self.languageComboBox.setCurrentIndex(
                self.languageComboBox.findText(self.project.pdata["PROGLANGUAGE"][0]))
            self.mixedLanguageCheckBox.setChecked(self.project.pdata["MIXEDLANGUAGE"][0])
            try:
                curIndex = \
                    self.projectTypeComboBox.findText(
                        projectTypes[self.project.pdata["PROJECTTYPE"][0]])
            except KeyError:
                curIndex = -1
            if curIndex == -1:
                curIndex = self.projectTypeComboBox.findText(projectTypes["Qt4"])
            self.projectTypeComboBox.setCurrentIndex(curIndex)
            self.dirEdit.setText(self.project.ppath)
            try:
                self.versionEdit.setText(self.project.pdata["VERSION"][0])
            except IndexError:
                pass
            try:
                self.mainscriptEdit.setText(self.project.pdata["MAINSCRIPT"][0])
            except IndexError:
                pass
            try:
                self.authorEdit.setText(self.project.pdata["AUTHOR"][0])
            except IndexError:
                pass
            try:
                self.emailEdit.setText(self.project.pdata["EMAIL"][0])
            except IndexError:
                pass
            try:
                self.descriptionEdit.setPlainText(self.project.pdata["DESCRIPTION"][0])
            except LookupError:
                pass
            try:
                self.eolComboBox.setCurrentIndex(self.project.pdata["EOL"][0])
            except IndexError:
                pass
            self.vcsLabel.show()
            if self.project.vcs is not None:
                vcsSystemsDict = e5App().getObject("PluginManager")\
                    .getPluginDisplayStrings("version_control")
                try:
                    vcsSystemDisplay = vcsSystemsDict[self.project.pdata["VCS"][0]]
                except KeyError:
                    vcsSystemDisplay = "None"
                self.vcsLabel.setText(
                    self.trUtf8("The project is version controlled by <b>{0}</b>.")
                    .format(vcsSystemDisplay))
                self.vcsInfoButton.show()
            else:
                self.vcsLabel.setText(
                    self.trUtf8("The project is not version controlled."))
                self.vcsInfoButton.hide()
        else:
            self.languageComboBox.setCurrentIndex(
                self.languageComboBox.findText("Python3"))
            self.projectTypeComboBox.setCurrentIndex(
                self.projectTypeComboBox.findText(projectTypes["Qt4"]))
            hp = os.getcwd()
            hp = hp + os.sep
            self.dirEdit.setText(hp)
            self.versionEdit.setText('0.1')
            self.vcsLabel.hide()
            self.vcsInfoButton.hide()
        
    @pyqtSlot()
    def on_dirButton_clicked(self):
        """
        Private slot to display a directory selection dialog.
        """
        directory = E5FileDialog.getExistingDirectory(
            self,
            self.trUtf8("Select project directory"),
            self.dirEdit.text(),
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
        
        if directory:
            self.dirEdit.setText(Utilities.toNativeSeparators(directory))
        
    @pyqtSlot()
    def on_spellPropertiesButton_clicked(self):
        """
        Private slot to display the spelling properties dialog.
        """
        if self.spellPropertiesDlg is None:
            self.spellPropertiesDlg = \
                SpellingPropertiesDialog(self.project, self.newProject, self)
        res = self.spellPropertiesDlg.exec_()
        if res == QDialog.Rejected:
            self.spellPropertiesDlg.initDialog()  # reset the dialogs contents
        
    @pyqtSlot()
    def on_transPropertiesButton_clicked(self):
        """
        Private slot to display the translations properties dialog.
        """
        if self.transPropertiesDlg is None:
            self.transPropertiesDlg = \
                TranslationPropertiesDialog(self.project, self.newProject, self)
        else:
            self.transPropertiesDlg.initFilters()
        res = self.transPropertiesDlg.exec_()
        if res == QDialog.Rejected:
            self.transPropertiesDlg.initDialog()  # reset the dialogs contents
        
    @pyqtSlot()
    def on_mainscriptButton_clicked(self):
        """
        Private slot to display a file selection dialog.
        """
        dir = self.dirEdit.text()
        if not dir:
            dir = QDir.currentPath()
        patterns = []
        for pattern, filetype in list(self.project.pdata["FILETYPES"].items()):
            if filetype == "SOURCES":
                patterns.append(pattern)
        filters = self.trUtf8("Source Files ({0});;All Files (*)")\
            .format(" ".join(patterns))
        fn = E5FileDialog.getOpenFileName(
            self,
            self.trUtf8("Select main script file"),
            dir,
            filters)
        
        if fn:
            ppath = self.dirEdit.text()
            if ppath:
                ppath = QDir(ppath).absolutePath() + QDir.separator()
                fn = fn.replace(ppath, "")
            self.mainscriptEdit.setText(Utilities.toNativeSeparators(fn))
        
    @pyqtSlot()
    def on_vcsInfoButton_clicked(self):
        """
        Private slot to display a vcs information dialog.
        """
        if self.project.vcs is None:
            return
            
        info = self.project.vcs.vcsRepositoryInfos(self.project.ppath)
        dlg = VcsRepositoryInfoDialog(self, info)
        dlg.exec_()
        
    def getProjectType(self):
        """
        Public method to get the selected project type.
        
        @return selected UI type (string)
        """
        return self.projectTypeComboBox.itemData(self.projectTypeComboBox.currentIndex())
        
    def getPPath(self):
        """
        Public method to get the project path.
        
        @return data of the project directory edit (string)
        """
        return os.path.abspath(self.dirEdit.text())
        
    def storeData(self):
        """
        Public method to store the entered/modified data.
        """
        self.project.ppath = os.path.abspath(self.dirEdit.text())
        fn = self.nameEdit.text()
        if fn:
            self.project.name = fn
            fn = "{0}.e4p".format(fn)
            self.project.pfile = os.path.join(self.project.ppath, fn)
        else:
            self.project.pfile = ""
        self.project.pdata["VERSION"] = [self.versionEdit.text()]
        fn = self.mainscriptEdit.text()
        if fn:
            fn = self.project.getRelativePath(fn)
            self.project.pdata["MAINSCRIPT"] = [fn]
            self.project.translationsRoot = os.path.splitext(fn)[0]
        else:
            self.project.pdata["MAINSCRIPT"] = []
            self.project.translationsRoot = ""
        self.project.pdata["AUTHOR"] = [self.authorEdit.text()]
        self.project.pdata["EMAIL"] = [self.emailEdit.text()]
        self.project.pdata["DESCRIPTION"] = [self.descriptionEdit.toPlainText()]
        self.project.pdata["PROGLANGUAGE"] = \
            [self.languageComboBox.currentText()]
        self.project.pdata["MIXEDLANGUAGE"] = [self.mixedLanguageCheckBox.isChecked()]
        projectType = self.getProjectType()
        if projectType is not None:
            self.project.pdata["PROJECTTYPE"] = [projectType]
        self.project.pdata["EOL"] = [self.eolComboBox.currentIndex()]
        
        # TODO: store state of VCS checkbox to self.project.vcsRequested
        
        if self.spellPropertiesDlg is not None:
            self.spellPropertiesDlg.storeData()
        
        if self.transPropertiesDlg is not None:
            self.transPropertiesDlg.storeData()
