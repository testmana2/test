# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the PEP 8 Checker plugin.
"""

import os

from PyQt4.QtCore import QObject

from E5Gui.E5Application import e5App

from E5Gui.E5Action import E5Action

from CheckerPlugins.Pep8.Pep8Dialog import Pep8Dialog

import Preferences

# Start-Of-Header
name = "PEP 8 Checker Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = True
deactivateable = True
version = "5.3.0"
className = "Pep8CheckerPlugin"
packageName = "__core__"
shortDescription = "Show the PEP 8 Checker dialog."
longDescription = """This plugin implements the PEP 8 Checker dialog.""" \
 """ PEP 8 Checker is used to check Python source files for compliance""" \
 """ to the conventions given in PEP 8."""
pyqtApi = 2
# End-Of-Header

error = ""


class Pep8CheckerPlugin(QObject):
    """
    Class implementing the PEP 8 Checker plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super().__init__(ui)
        self.__ui = ui
        self.__initialize()
        
    def __initialize(self):
        """
        Private slot to (re)initialize the plugin.
        """
        self.__projectAct = None
        self.__projectPep8CheckerDialog = None
        
        self.__projectBrowserAct = None
        self.__projectBrowserMenu = None
        self.__projectBrowserPep8CheckerDialog = None
        
        self.__editors = []
        self.__editorAct = None
        self.__editorPep8CheckerDialog = None

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        menu = e5App().getObject("Project").getMenu("Checks")
        if menu:
            self.__projectAct = E5Action(self.trUtf8('Check PEP 8 Compliance'),
                    self.trUtf8('PEP &8 Compliance...'), 0, 0,
                    self, 'project_check_pep8')
            self.__projectAct.setStatusTip(
                self.trUtf8('Check PEP 8 compliance.'))
            self.__projectAct.setWhatsThis(self.trUtf8(
                """<b>Check PEP 8 Compliance...</b>"""
                """<p>This checks Python files for compliance to the"""
                """ conventions given in PEP 8.</p>"""
            ))
            self.__projectAct.triggered[()].connect(self.__projectPep8Check)
            e5App().getObject("Project").addE5Actions([self.__projectAct])
            menu.addAction(self.__projectAct)
        
        self.__editorAct = E5Action(self.trUtf8('Check PEP 8 Compliance'),
                self.trUtf8('PEP &8 Compliance...'), 0, 0,
                self, "")
        self.__editorAct.setWhatsThis(self.trUtf8(
                """<b>Check PEP 8 Compliance...</b>"""
                """<p>This checks Python files for compliance to the"""
                """ conventions given in PEP 8.</p>"""
        ))
        self.__editorAct.triggered[()].connect(self.__editorPep8Check)
        
        e5App().getObject("Project").showMenu.connect(self.__projectShowMenu)
        e5App().getObject("ProjectBrowser").getProjectBrowser("sources")\
            .showMenu.connect(self.__projectBrowserShowMenu)
        e5App().getObject("ViewManager").editorOpenedEd.connect(
            self.__editorOpened)
        e5App().getObject("ViewManager").editorClosedEd.connect(
            self.__editorClosed)
        
        for editor in e5App().getObject("ViewManager").getOpenEditors():
            self.__editorOpened(editor)
        
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        e5App().getObject("Project").showMenu.disconnect(
            self.__projectShowMenu)
        e5App().getObject("ProjectBrowser").getProjectBrowser("sources")\
            .showMenu.disconnect(self.__projectBrowserShowMenu)
        e5App().getObject("ViewManager").editorOpenedEd.disconnect(
            self.__editorOpened)
        e5App().getObject("ViewManager").editorClosedEd.disconnect(
            self.__editorClosed)
        
        menu = e5App().getObject("Project").getMenu("Checks")
        if menu:
            menu.removeAction(self.__projectAct)
        
        if self.__projectBrowserMenu:
            if self.__projectBrowserAct:
                self.__projectBrowserMenu.removeAction(
                    self.__projectBrowserAct)
        
        for editor in self.__editors:
            editor.showMenu.disconnect(self.__editorShowMenu)
            menu = editor.getMenu("Checks")
            if menu is not None:
                menu.removeAction(self.__editorAct)
        
        self.__initialize()
    
    def __projectShowMenu(self, menuName, menu):
        """
        Private slot called, when the the project menu or a submenu is
        about to be shown.
        
        @param menuName name of the menu to be shown (string)
        @param menu reference to the menu (QMenu)
        """
        if menuName == "Checks" and self.__projectAct is not None:
            self.__projectAct.setEnabled(
                e5App().getObject("Project").getProjectLanguage() in \
                    ["Python3", "Python2", "Python"])
    
    def __projectBrowserShowMenu(self, menuName, menu):
        """
        Private slot called, when the the project browser menu or a submenu is
        about to be shown.
        
        @param menuName name of the menu to be shown (string)
        @param menu reference to the menu (QMenu)
        """
        if menuName == "Checks" and \
           e5App().getObject("Project").getProjectLanguage() in \
                ["Python3", "Python2", "Python"]:
            self.__projectBrowserMenu = menu
            if self.__projectBrowserAct is None:
                self.__projectBrowserAct = E5Action(
                    self.trUtf8('Check PEP 8 Compliance'),
                    self.trUtf8('PEP &8 Compliance...'), 0, 0,
                    self, "")
                self.__projectBrowserAct.setWhatsThis(self.trUtf8(
                    """<b>Check PEP 8 Compliance...</b>"""
                    """<p>This checks Python files for compliance to the"""
                    """ conventions given in PEP 8.</p>"""
                ))
                self.__projectBrowserAct.triggered[()].connect(
                    self.__projectBrowserPep8Check)
            if not self.__projectBrowserAct in menu.actions():
                menu.addAction(self.__projectBrowserAct)
    
    def __projectPep8Check(self):
        """
        Public slot used to check the project files for PEP 8 compliance.
        """
        project = e5App().getObject("Project")
        project.saveAllScripts()
        ppath = project.getProjectPath()
        files = [os.path.join(ppath, file) \
            for file in project.pdata["SOURCES"] \
                if file.endswith(
                    tuple(Preferences.getPython("Python3Extensions")) +
                    tuple(Preferences.getPython("PythonExtensions")))]
        
        self.__projectPep8CheckerDialog = Pep8Dialog()
        self.__projectPep8CheckerDialog.show()
        self.__projectPep8CheckerDialog.prepare(files, project)
    
    def __projectBrowserPep8Check(self):
        """
        Private method to handle the PEP 8 check context menu action of
        the project sources browser.
        """
        browser = e5App().getObject("ProjectBrowser")\
            .getProjectBrowser("sources")
        itm = browser.model().item(browser.currentIndex())
        try:
            fn = itm.fileName()
            isDir = False
        except AttributeError:
            fn = itm.dirName()
            isDir = True
        
        self.__projectBrowserPep8CheckerDialog = Pep8Dialog()
        self.__projectBrowserPep8CheckerDialog.show()
        if isDir:
            self.__projectBrowserPep8CheckerDialog.start(
                fn, save=True)
        else:
            self.__projectBrowserPep8CheckerDialog.start(
                fn, save=True, repeat=True)
    
    def __editorOpened(self, editor):
        """
        Private slot called, when a new editor was opened.
        
        @param editor reference to the new editor (QScintilla.Editor)
        """
        menu = editor.getMenu("Checks")
        if menu is not None:
            menu.addAction(self.__editorAct)
            editor.showMenu.connect(self.__editorShowMenu)
            self.__editors.append(editor)
    
    def __editorClosed(self, editor):
        """
        Private slot called, when an editor was closed.
        
        @param editor reference to the editor (QScintilla.Editor)
        """
        try:
            self.__editors.remove(editor)
        except ValueError:
            pass
    
    def __editorShowMenu(self, menuName, menu, editor):
        """
        Private slot called, when the the editor context menu or a submenu is
        about to be shown.
        
        @param menuName name of the menu to be shown (string)
        @param menu reference to the menu (QMenu)
        @param editor reference to the editor
        """
        if menuName == "Checks":
            if not self.__editorAct in menu.actions():
                menu.addAction(self.__editorAct)
            self.__editorAct.setEnabled(editor.isPy3File() or editor.isPy2File())
    
    def __editorPep8Check(self):
        """
        Private slot to handle the PEP 8 check context menu action
        of the editors.
        """
        editor = e5App().getObject("ViewManager").activeWindow()
        if editor is not None:
            if editor.checkDirty() and editor.getFileName() is not None:
                self.__editorPep8CheckerDialog = Pep8Dialog()
                self.__editorPep8CheckerDialog.show()
                self.__editorPep8CheckerDialog.start(
                    editor.getFileName(),
                    save=True,
                    repeat=True)
