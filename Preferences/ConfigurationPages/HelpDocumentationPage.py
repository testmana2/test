# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Help Documentation configuration page.
"""

from PyQt4.QtCore import QDir, pyqtSlot
from PyQt4.QtGui import QFileDialog

from E4Gui.E4Completers import E4DirCompleter

from .ConfigurationPageBase import ConfigurationPageBase
from .Ui_HelpDocumentationPage import Ui_HelpDocumentationPage

import Preferences
import Utilities

class HelpDocumentationPage(ConfigurationPageBase, Ui_HelpDocumentationPage):
    """
    Class implementing the Help Documentation configuration page.
    """
    def __init__(self):
        """
        Constructor
        """
        ConfigurationPageBase.__init__(self)
        self.setupUi(self)
        self.setObjectName("HelpDocumentationPage")
        
        self.pythonDocDirCompleter = E4DirCompleter(self.pythonDocDirEdit)
        self.qt4DocDirCompleter = E4DirCompleter(self.qt4DocDirEdit)
        self.pyqt4DocDirCompleter = E4DirCompleter(self.pyqt4DocDirEdit)
        self.pysideDocDirCompleter = E4DirCompleter(self.pysideDocDirEdit)
        
        try:
            import PySide
            self.pysideGroup.setEnabled(True)
            del PySide
        except ImportError:
            self.pysideGroup.setEnabled(False)
        
        # set initial values
        self.pythonDocDirEdit.setText(\
            Preferences.getHelp("PythonDocDir"))
        self.qt4DocDirEdit.setText(\
            Preferences.getHelp("Qt4DocDir"))
        self.pyqt4DocDirEdit.setText(\
            Preferences.getHelp("PyQt4DocDir"))
        self.pysideDocDirEdit.setText(\
            Preferences.getHelp("PySideDocDir"))
        
    def save(self):
        """
        Public slot to save the Help Documentation configuration.
        """
        Preferences.setHelp("PythonDocDir",
            self.pythonDocDirEdit.text())
        Preferences.setHelp("Qt4DocDir",
            self.qt4DocDirEdit.text())
        Preferences.setHelp("PyQt4DocDir",
            self.pyqt4DocDirEdit.text())
        Preferences.setHelp("PySideDocDir",
            self.pysideDocDirEdit.text())
        
    @pyqtSlot()
    def on_pythonDocDirButton_clicked(self):
        """
        Private slot to select the Python documentation directory.
        """
        dir = QFileDialog.getExistingDirectory(\
            self,
            self.trUtf8("Select Python documentation directory"),
            self.pythonDocDirEdit.text(),
            QFileDialog.Options(QFileDialog.ShowDirsOnly))
        
        if dir:
            self.pythonDocDirEdit.setText(\
                Utilities.toNativeSeparators(dir))
        
    @pyqtSlot()
    def on_qt4DocDirButton_clicked(self):
        """
        Private slot to select the Qt4 documentation directory.
        """
        dir = QFileDialog.getExistingDirectory(\
            self,
            self.trUtf8("Select Qt4 documentation directory"),
            self.qt4DocDirEdit.text(),
            QFileDialog.Options(QFileDialog.ShowDirsOnly))
        
        if dir:
            self.qt4DocDirEdit.setText(\
                Utilities.toNativeSeparators(dir))
        
    @pyqtSlot()
    def on_pyqt4DocDirButton_clicked(self):
        """
        Private slot to select the PyQt4 documentation directory.
        """
        dir = QFileDialog.getExistingDirectory(\
            self,
            self.trUtf8("Select PyQt4 documentation directory"),
            self.pyqt4DocDirEdit.text(),
            QFileDialog.Options(QFileDialog.ShowDirsOnly))
        
        if dir:
            self.pyqt4DocDirEdit.setText(\
                Utilities.toNativeSeparators(dir))
        
    @pyqtSlot()
    def on_pysideDocDirButton_clicked(self):
        """
        Private slot to select the PySide documentation directory.
        """
        dir = QFileDialog.getExistingDirectory(\
            self,
            self.trUtf8("Select PySide documentation directory"),
            self.pysideDocDirEdit.text(),
            QFileDialog.Options(QFileDialog.ShowDirsOnly))
        
        if dir:
            self.pysideDocDirEdit.setText(Utilities.toNativeSeparators(dir))
    
def create(dlg):
    """
    Module function to create the configuration page.
    
    @param dlg reference to the configuration dialog
    """
    page = HelpDocumentationPage()
    return page
