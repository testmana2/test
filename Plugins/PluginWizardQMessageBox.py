# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the QMessageBox wizard plugin.
"""

from PyQt4.QtCore import QObject
from PyQt4.QtGui import QDialog

from E5Gui.E5Application import e5App
from E5Gui.E5Action import E5Action
from E5Gui import E5MessageBox

# Start-Of-Header
name = "QMessageBox Wizard Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = True
deactivateable = True
version = "5.4.0"
className = "MessageBoxWizard"
packageName = "__core__"
shortDescription = "Show the QMessageBox wizard."
longDescription = """This plugin shows the QMessageBox wizard."""
pyqtApi = 2
# End-Of-Header

error = ""


class MessageBoxWizard(QObject):
    """
    Class implementing the QMessageBox wizard plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super().__init__(ui)
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
        self.action = E5Action(
            self.trUtf8('QMessageBox Wizard'),
            self.trUtf8('Q&MessageBox Wizard...'), 0, 0, self,
            'wizards_qmessagebox')
        self.action.setStatusTip(self.trUtf8('QMessageBox Wizard'))
        self.action.setWhatsThis(self.trUtf8(
            """<b>QMessageBox Wizard</b>"""
            """<p>This wizard opens a dialog for entering all the parameters"""
            """ needed to create a QMessageBox. The generated code is"""
            """ inserted at the current cursor position.</p>"""
        ))
        self.action.triggered[()].connect(self.__handle)
        
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
        from WizardPlugins.MessageBoxWizard.MessageBoxWizardDialog import \
            MessageBoxWizardDialog
        dlg = MessageBoxWizardDialog(None)
        if dlg.exec_() == QDialog.Accepted:
            line, index = editor.getCursorPosition()
            indLevel = editor.indentation(line) // editor.indentationWidth()
            if editor.indentationsUseTabs():
                indString = '\t'
            else:
                indString = editor.indentationWidth() * ' '
            return (dlg.getCode(indLevel, indString), True)
        else:
            return (None, False)
        
    def __handle(self):
        """
        Private method to handle the wizards action.
        """
        editor = e5App().getObject("ViewManager").activeWindow()
        
        if editor == None:
            E5MessageBox.critical(
                self.__ui,
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
