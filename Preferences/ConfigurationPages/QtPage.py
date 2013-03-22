# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Qt configuration page.
"""

from PyQt4.QtCore import pyqtSlot

from E5Gui.E5Completers import E5DirCompleter
from E5Gui import E5FileDialog

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_QtPage import Ui_QtPage

import Preferences
import Utilities


class QtPage(ConfigurationPageBase, Ui_QtPage):
    """
    Class implementing the Qt configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.setObjectName("QtPage")
        
        self.qt4Completer = E5DirCompleter(self.qt4Edit)
        self.qt4TransCompleter = E5DirCompleter(self.qt4TransEdit)
        
        if not Utilities.isMacPlatform():
            self.qt4Group.hide()
        
        # set initial values
        self.qt4Edit.setText(Preferences.getQt("Qt4Dir"))
        self.qt4TransEdit.setText(Preferences.getQt("Qt4TranslationsDir"))
        self.qt4PrefixEdit.setText(Preferences.getQt("QtToolsPrefix4"))
        self.qt4PostfixEdit.setText(Preferences.getQt("QtToolsPostfix4"))
        self.__updateQt4Sample()
        
    def save(self):
        """
        Public slot to save the Qt configuration.
        """
        Preferences.setQt("Qt4Dir", self.qt4Edit.text())
        Preferences.setQt("Qt4TranslationsDir", self.qt4TransEdit.text())
        Preferences.setQt("QtToolsPrefix4", self.qt4PrefixEdit.text())
        Preferences.setQt("QtToolsPostfix4", self.qt4PostfixEdit.text())
        
    @pyqtSlot()
    def on_qt4Button_clicked(self):
        """
        Private slot to handle the Qt4 directory selection.
        """
        dir = E5FileDialog.getExistingDirectory(
            self,
            self.trUtf8("Select Qt4 Directory"),
            self.qt4Edit.text(),
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
            
        if dir:
            self.qt4Edit.setText(Utilities.toNativeSeparators(dir))
        
    @pyqtSlot()
    def on_qt4TransButton_clicked(self):
        """
        Private slot to handle the Qt4 translations directory selection.
        """
        dir = E5FileDialog.getExistingDirectory(
            self,
            self.trUtf8("Select Qt4 Translations Directory"),
            self.qt4TransEdit.text(),
            E5FileDialog.Options(E5FileDialog.ShowDirsOnly))
            
        if dir:
            self.qt4TransEdit.setText(Utilities.toNativeSeparators(dir))
        
    def __updateQt4Sample(self):
        """
        Private slot to update the Qt4 tools sample label.
        """
        self.qt4SampleLabel.setText("Sample: {0}designer{1}"\
            .format(self.qt4PrefixEdit.text(),
                    self.qt4PostfixEdit.text()))
    
    @pyqtSlot(str)
    def on_qt4PrefixEdit_textChanged(self, txt):
        """
        Private slot to handle a change in the entered Qt directory.
        
        @param txt the entered string (string)
        """
        self.__updateQt4Sample()
    
    @pyqtSlot(str)
    def on_qt4PostfixEdit_textChanged(self, txt):
        """
        Private slot to handle a change in the entered Qt directory.
        
        @param txt the entered string (string)
        """
        self.__updateQt4Sample()
    

def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = QtPage()
    return page
