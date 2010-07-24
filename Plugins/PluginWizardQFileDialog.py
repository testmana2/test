# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the QFileDialog wizard plugin.
"""

from PyQt4.QtCore import QObject, SIGNAL
from PyQt4.QtGui import QDialog, QMessageBox

from E5Gui.E5Application import e5App
from E5Gui.E5Action import E5Action

from WizardPlugins.FileDialogWizard.FileDialogWizardDialog import \
    FileDialogWizardDialog

# Start-Of-Header
name = "QFileDialog Wizard Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = True
deactivateable = True
version = "5.1.0"
className = "FileDialogWizard"
packageName = "__core__"
shortDescription = "Show the QFileDialog wizard."
longDescription = """This plugin shows the QFileDialog wizard."""
pyqtApi = 2
# End-Of-Header

error = ""

class FileDialogWizard(QObject):
    """
    Class implementing the QFileDialog wizard plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        QObject.__init__(self, ui)
        self.__ui = ui

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        self.__initAction()
        self.__initMenu()
        
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        menu = self.__ui.getMenu("wizards")
        if menu:
            menu.removeAction(self.action)
        self.__ui.removeE5Actions([self.action], 'wizards')
    
    def __initAction(self):
        """
        Private method to initialize the action.
        """
        self.action = E5Action(self.trUtf8('QFileDialog Wizard'),
             self.trUtf8('Q&FileDialog Wizard...'), 0, 0, self,
             'wizards_qfiledialog')
        self.action.setStatusTip(self.trUtf8('QFileDialog Wizard'))
        self.action.setWhatsThis(self.trUtf8(
            """<b>QFileDialog Wizard</b>"""
            """<p>This wizard opens a dialog for entering all the parameters"""
            """ needed to create a QFileDialog. The generated code is inserted"""
            """ at the current cursor position.</p>"""
        ))
        self.connect(self.action, SIGNAL('triggered()'), self.__handle)
        
        self.__ui.addE5Actions([self.action], 'wizards')

    def __initMenu(self):
        """
        Private method to add the actions to the right menu.
        """
        menu = self.__ui.getMenu("wizards")
        if menu:
            menu.addAction(self.action)
    
    def __callForm(self, editor):
        """
        Private method to display a dialog and get the code.
        
        @param editor reference to the current editor
        @return the generated code (string)
        """
        dlg = FileDialogWizardDialog(None)
        if dlg.exec_() == QDialog.Accepted:
            line, index = editor.getCursorPosition()
            indLevel = editor.indentation(line) // editor.indentationWidth()
            if editor.indentationsUseTabs():
                indString = '\t'
            else:
                indString = editor.indentationWidth() * ' '
            return (dlg.getCode(indLevel, indString), 1)
        else:
            return (None, 0)
        
    def __handle(self):
        """
        Private method to handle the wizards action 
        """
        editor = e5App().getObject("ViewManager").activeWindow()
        
        if editor == None:
                QMessageBox.critical(None, 
                self.trUtf8('No current editor'),
                self.trUtf8('Please open or create a file first.'))
        else:
            code, ok = self.__callForm(editor)
            if ok:
                line, index = editor.getCursorPosition()
                # It should be done on this way to allow undo
                editor.beginUndoAction()
                editor.insertAt(code, line, index)
                editor.endUndoAction()