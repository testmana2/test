# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Spelling Properties dialog.
"""

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from E5Gui.E5Completers import E5FileCompleter

from QScintilla.SpellChecker import SpellChecker

from .Ui_SpellingPropertiesDialog import Ui_SpellingPropertiesDialog

import Utilities
import Preferences

class SpellingPropertiesDialog(QDialog, Ui_SpellingPropertiesDialog):
    """
    Class implementing the Spelling Properties dialog.
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
        
        self.pwlCompleter = E5FileCompleter(self.pwlEdit)
        self.pelCompleter = E5FileCompleter(self.pelEdit)
        
        self.spellingComboBox.addItem(self.trUtf8("<default>"))
        self.spellingComboBox.addItems(sorted(SpellChecker.getAvailableLanguages()))
        
        if not new:
            self.initDialog()
    
    def initDialog(self):
        """
        Public method to initialize the dialogs data.
        """
        index = self.spellingComboBox.findText(self.project.pdata["SPELLLANGUAGE"][0])
        if index == -1:
            index = 0
        self.spellingComboBox.setCurrentIndex(index)
        if self.project.pdata["SPELLWORDS"][0]:
            self.pwlEdit.setText(
                os.path.join(self.project.ppath, self.project.pdata["SPELLWORDS"][0]))
        if self.project.pdata["SPELLEXCLUDES"][0]:
            self.pelEdit.setText(
                os.path.join(self.project.ppath, self.project.pdata["SPELLEXCLUDES"][0]))
    
    @pyqtSlot()
    def on_pwlButton_clicked(self):
        """
        Private slot to select the project word list file.
        """
        pwl = self.pwlEdit.text()
        if not pwl:
            pwl = self.project.ppath
        file = QFileDialog.getOpenFileName(
            self,
            self.trUtf8("Select project word list"),
            pwl,
            self.trUtf8("Dictionary File (*.dic);;All Files (*)"))
        
        if file:
            self.pwlEdit.setText(Utilities.toNativeSeparators(file))
    
    @pyqtSlot()
    def on_pelButton_clicked(self):
        """
        Private slot to select the project exclude list file.
        """
        pel = self.pelEdit.text()
        if not pel:
            pel = self.project.ppath
        file = QFileDialog.getOpenFileName(
            self,
            self.trUtf8("Select project exclude list"),
            pel,
            self.trUtf8("Dictionary File (*.dic);;All Files (*)"))
            
        if file:
            self.pelEdit.setText(Utilities.toNativeSeparators(file))
    
    def storeData(self):
        """
        Public method to store the entered/modified data.
        """
        if self.spellingComboBox.currentIndex() == 0:
            self.project.pdata["SPELLLANGUAGE"] = \
                [Preferences.getEditor("SpellCheckingDefaultLanguage")]
        else:
            self.project.pdata["SPELLLANGUAGE"] = \
                [self.spellingComboBox.currentText()]
        self.project.pdata["SPELLWORDS"] = \
            [self.project.getRelativePath(self.pwlEdit.text())]
        self.project.pdata["SPELLEXCLUDES"] = \
            [self.project.getRelativePath(self.pelEdit.text())]