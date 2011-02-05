# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Editor APIs configuration page.
"""

from PyQt4.QtCore import QDir, pyqtSlot, QFileInfo
from PyQt4.QtGui import QFileDialog, QInputDialog

from E5Gui.E5Application import e5App
from E5Gui.E5Completers import E5FileCompleter

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_EditorAPIsPage import Ui_EditorAPIsPage

from QScintilla.APIsManager import APIsManager
import QScintilla.Lexers

import Preferences
import Utilities

class EditorAPIsPage(ConfigurationPageBase, Ui_EditorAPIsPage):
    """
    Class implementing the Editor APIs configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("EditorAPIsPage")
        
        self.prepareApiButton.setText(self.trUtf8("Compile APIs"))
        self.__apisManager = APIsManager()
        self.__currentAPI = None
        self.__inPreparation = False
        
        self.apiFileCompleter = E5FileCompleter(self.apiFileEdit)
        
        # set initial values
        self.pluginManager = e5App().getObject("PluginManager")
        self.apiAutoPrepareCheckBox.setChecked(
            Preferences.getEditor("AutoPrepareAPIs"))
        
        self.apis = {}
        apiLanguages = sorted([''] + \
                       list(QScintilla.Lexers.getSupportedLanguages().keys()))
        for lang in apiLanguages:
            if lang != "Guessed":
                self.apiLanguageComboBox.addItem(lang)
        self.currentApiLanguage = ''
        self.on_apiLanguageComboBox_activated(self.currentApiLanguage)
        
        for lang in apiLanguages[1:]:
            self.apis[lang] = Preferences.getEditorAPI(lang)[:]
        
    def save(self):
        """
        Public slot to save the Editor APIs configuration.
        """
        Preferences.setEditor("AutoPrepareAPIs",
            self.apiAutoPrepareCheckBox.isChecked())
        
        lang = self.apiLanguageComboBox.currentText()
        self.apis[lang] = self.__editorGetApisFromApiList()
        
        for lang, apis in list(self.apis.items()):
            Preferences.setEditorAPI(lang, apis)
        
    @pyqtSlot(str)
    def on_apiLanguageComboBox_activated(self, language):
        """
        Private slot to fill the api listbox of the api page.
        
        @param language selected API language (string)
        """
        if self.currentApiLanguage == language:
            return
            
        self.apis[self.currentApiLanguage] = self.__editorGetApisFromApiList()
        self.currentApiLanguage = language
        self.apiList.clear()
        
        if not language:
            self.apiGroup.setEnabled(False)
            return
            
        self.apiGroup.setEnabled(True)
        for api in self.apis[self.currentApiLanguage]:
            if api:
                self.apiList.addItem(api)
        self.__currentAPI = self.__apisManager.getAPIs(self.currentApiLanguage)
        if self.__currentAPI is not None:
            self.__currentAPI.apiPreparationFinished.connect(
                self.__apiPreparationFinished)
            self.__currentAPI.apiPreparationCancelled.connect(
                self.__apiPreparationCancelled)
            self.__currentAPI.apiPreparationStarted.connect(
                self.__apiPreparationStarted)
            self.addInstalledApiFileButton.setEnabled(
                self.__currentAPI.installedAPIFiles() != "")
        else:
            self.addInstalledApiFileButton.setEnabled(False)
        
        self.addPluginApiFileButton.setEnabled(
            len(self.pluginManager.getPluginApiFiles(self.currentApiLanguage)) > 0)
        
    def __editorGetApisFromApiList(self):
        """
        Private slot to retrieve the api filenames from the list.
        
        @return list of api filenames (list of strings)
        """
        apis = []
        for row in range(self.apiList.count()):
            apis.append(self.apiList.item(row).text())
        return apis
        
    @pyqtSlot()
    def on_apiFileButton_clicked(self):
        """
        Private method to select an api file.
        """
        file = QFileDialog.getOpenFileName(
            self,
            self.trUtf8("Select API file"),
            self.apiFileEdit.text(),
            self.trUtf8("API File (*.api);;All Files (*)"), 
            QFileDialog.DontUseNativeDialog)
            
        if file:
            self.apiFileEdit.setText(Utilities.toNativeSeparators(file))
        
    @pyqtSlot()
    def on_addApiFileButton_clicked(self):
        """
        Private slot to add the api file displayed to the listbox.
        """
        file = self.apiFileEdit.text()
        if file:
            self.apiList.addItem(Utilities.toNativeSeparators(file))
            self.apiFileEdit.clear()
        
    @pyqtSlot()
    def on_deleteApiFileButton_clicked(self):
        """
        Private slot to delete the currently selected file of the listbox.
        """
        crow = self.apiList.currentRow()
        if crow >= 0:
            itm = self.apiList.takeItem(crow)
            del itm
        
    @pyqtSlot()
    def on_addInstalledApiFileButton_clicked(self):
        """
        Private slot to add an API file from the list of installed API files
        for the selected lexer language.
        """
        installedAPIFiles = self.__currentAPI.installedAPIFiles()
        installedAPIFilesPath = QFileInfo(installedAPIFiles[0]).path()
        installedAPIFilesShort = []
        for installedAPIFile in installedAPIFiles:
            installedAPIFilesShort.append(QFileInfo(installedAPIFile).fileName())
        file, ok = QInputDialog.getItem(
            self,
            self.trUtf8("Add from installed APIs"),
            self.trUtf8("Select from the list of installed API files"),
            installedAPIFilesShort,
            0, False)
        if ok:
            self.apiList.addItem(Utilities.toNativeSeparators(
                QFileInfo(QDir(installedAPIFilesPath), file).absoluteFilePath()))
        
    @pyqtSlot()
    def on_addPluginApiFileButton_clicked(self):
        """
        Private slot to add an API file from the list of API files installed
        by plugins for the selected lexer language.
        """
        pluginAPIFiles = self.pluginManager.getPluginApiFiles(self.currentApiLanguage)
        pluginAPIFilesDict = {}
        for apiFile in pluginAPIFiles:
            pluginAPIFilesDict[QFileInfo(apiFile).fileName()] = apiFile
        file, ok = QInputDialog.getItem(
            self,
            self.trUtf8("Add from Plugin APIs"),
            self.trUtf8(
                "Select from the list of API files installed by plugins"),
            sorted(pluginAPIFilesDict.keys()),
            0, False)
        if ok:
            self.apiList.addItem(Utilities.toNativeSeparators(
                pluginAPIFilesDict[file]))
        
    @pyqtSlot()
    def on_prepareApiButton_clicked(self):
        """
        Private slot to prepare the API file for the currently selected language.
        """
        if self.__inPreparation:
            self.__currentAPI and self.__currentAPI.cancelPreparation()
        else:
            if self.__currentAPI is not None:
                self.__currentAPI.prepareAPIs(
                    ondemand = True, 
                    rawList = self.__editorGetApisFromApiList())
        
    def __apiPreparationFinished(self):
        """
        Private method called after the API preparation has finished.
        """
        self.prepareApiProgressBar.reset()
        self.prepareApiProgressBar.setRange(0, 100)
        self.prepareApiProgressBar.setValue(0)
        self.prepareApiButton.setText(self.trUtf8("Compile APIs"))
        self.__inPreparation = False
    
    def __apiPreparationCancelled(self):
        """
        Private slot called after the API preparation has been cancelled.
        """
        self.__apiPreparationFinished()
    
    def __apiPreparationStarted(self):
        """
        Private method called after the API preparation has started.
        """
        self.prepareApiProgressBar.setRange(0, 0)
        self.prepareApiProgressBar.setValue(0)
        self.prepareApiButton.setText(self.trUtf8("Cancel compilation"))
        self.__inPreparation = True
        
    def saveState(self):
        """
        Public method to save the current state of the widget.
        
        @return index of the selected lexer language (integer)
        """
        return self.apiLanguageComboBox.currentIndex()
        
    def setState(self, state):
        """
        Public method to set the state of the widget.
        
        @param state state data generated by saveState
        """
        self.apiLanguageComboBox.setCurrentIndex(state)
        self.on_apiLanguageComboBox_activated(self.apiLanguageComboBox.currentText())
    
def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = EditorAPIsPage()
    return page
