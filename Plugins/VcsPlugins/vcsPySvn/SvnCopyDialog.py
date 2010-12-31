# -*- coding: utf-8 -*-

# Copyright (c) 2003 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter the data for a copy operation.
"""

import os.path

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from E5Gui.E5Completers import E5FileCompleter, E5DirCompleter

from .Ui_SvnCopyDialog import Ui_SvnCopyDialog

class SvnCopyDialog(QDialog, Ui_SvnCopyDialog):
    """
    Class implementing a dialog to enter the data for a copy operation.
    """
    def __init__(self, source, parent = None, move = False, force = False):
        """
        Constructor
        
        @param source name of the source file/directory (string)
        @param parent parent widget (QWidget)
        @param move flag indicating a move operation (boolean)
        @param force flag indicating a forced operation (boolean)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.source = source
        if os.path.isdir(self.source):
            self.targetCompleter = E5DirCompleter(self.targetEdit)
        else:
            self.targetCompleter = E5FileCompleter(self.targetEdit)
        
        if move:
            self.setWindowTitle(self.trUtf8('Subversion Move'))
        else:
            self.forceCheckBox.setEnabled(False)
        self.forceCheckBox.setChecked(force)
        
        self.sourceEdit.setText(source)
        
    def getData(self):
        """
        Public method to retrieve the copy data.
        
        @return the target name (string) and a flag indicating
            the operation should be enforced (boolean)
        """
        return self.targetEdit.text(), self.forceCheckBox.isChecked()
        
    @pyqtSlot()
    def on_dirButton_clicked(self):
        """
        Private slot to handle the button press for selecting the target via a 
        selection dialog.
        """
        if os.path.isdir(self.source):
            target = QFileDialog.getExistingDirectory(
                None,
                self.trUtf8("Select target"),
                self.targetEdit.text(),
                QFileDialog.Options(QFileDialog.ShowDirsOnly))
        else:
            target = QFileDialog.getSaveFileName(
                None,
                self.trUtf8("Select target"),
                self.targetEdit.text(),
                "",
                QFileDialog.Options(QFileDialog.DontConfirmOverwrite))
        
        if target:
            self.targetEdit.setText(target)