# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Syntax Checker plugin.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

import os

from PyQt4.QtCore import QObject

from E5Gui.E5Application import e5App

from E5Gui.E5Action import E5Action

import Preferences

# Start-Of-Header
name = "Syntax Checker Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = True
deactivateable = True
version = "5.4.0"
className = "SyntaxCheckerPlugin"
packageName = "__core__"
shortDescription = "Show the Syntax Checker dialog."
longDescription = """This plugin implements the Syntax Checker dialog.""" \
 """ Syntax Checker is used to check Python source files for correct syntax."""
pyqtApi = 2
# End-Of-Header

error = ""


class SyntaxCheckerPlugin(QObject):
    """
    Class implementing the Syntax Checker plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        super(SyntaxCheckerPlugin, self).__init__(ui)
        self.__ui = ui
        self.__initialize()
        
    def __initialize(self):
        """
        Private slot to (re)initialize the plugin.
        """
        self.__projectAct = None
        self.__projectSyntaxCheckerDialog = None
        
        self.__projectBrowserAct = None
        self.__projectBrowserMenu = None
        self.__projectBrowserSyntaxCheckerDialog = None
        
        self.__editors = []
        self.__editorAct = None
        self.__editorSyntaxCheckerDialog = None

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        menu = e5App().getObject("Project").getMenu("Checks")
        if menu:
            self.__projectAct = E5Action(
                self.trUtf8('Check Syntax'),
                self.trUtf8('&Syntax...'), 0, 0,
                self, 'project_check_syntax')
            self.__projectAct.setStatusTip(
                self.trUtf8('Check syntax.'))
            self.__projectAct.setWhatsThis(self.trUtf8(
                """<b>Check Syntax...</b>"""
                """<p>This checks Python files for syntax errors.</p>"""
            ))
            self.__projectAct.triggered[()].connect(self.__projectSyntaxCheck)
            e5App().getObject("Project").addE5Actions([self.__projectAct])
            menu.addAction(self.__projectAct)
        
        self.__editorAct = E5Action(
            self.trUtf8('Check Syntax'),
            self.trUtf8('&Syntax...'), 0, 0,
            self, "")
        self.__editorAct.setWhatsThis(self.trUtf8(
                """<b>Check Syntax...</b>"""
                """<p>This checks Python files for syntax errors.</p>"""
        ))
        self.__editorAct.triggered[()].connect(self.__editorSyntaxCheck)
        
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
                    self.trUtf8('Check Syntax'),
                    self.trUtf8('&Syntax...'), 0, 0,
                    self, "")
                self.__projectBrowserAct.setWhatsThis(self.trUtf8(
                    """<b>Check Syntax...</b>"""
                    """<p>This checks Python files for syntax errors.</p>"""
                ))
                self.__projectBrowserAct.triggered[()].connect(
                    self.__projectBrowserSyntaxCheck)
            if not self.__projectBrowserAct in menu.actions():
                menu.addAction(self.__projectBrowserAct)
    
    def __projectSyntaxCheck(self):
        """
        Public slot used to check the project files for syntax errors.
        """
        project = e5App().getObject("Project")
        project.saveAllScripts()
        ppath = project.getProjectPath()
        files = [os.path.join(ppath, file) \
                 for file in project.pdata["SOURCES"] \
                 if file.endswith(
                    tuple(Preferences.getPython("Python3Extensions")) +
                    tuple(Preferences.getPython("PythonExtensions")))]
        
        from CheckerPlugins.SyntaxChecker.SyntaxCheckerDialog import \
            SyntaxCheckerDialog
        self.__projectSyntaxCheckerDialog = SyntaxCheckerDialog()
        self.__projectSyntaxCheckerDialog.show()
        self.__projectSyntaxCheckerDialog.prepare(files, project)
    
    def __projectBrowserSyntaxCheck(self):
        """
        Private method to handle the syntax check context menu action of the
        project sources browser.
        """
        browser = e5App().getObject("ProjectBrowser").getProjectBrowser(
            "sources")
        itm = browser.model().item(browser.currentIndex())
        try:
            fn = itm.fileName()
        except AttributeError:
            fn = itm.dirName()
        
        from CheckerPlugins.SyntaxChecker.SyntaxCheckerDialog import \
            SyntaxCheckerDialog
        self.__projectBrowserSyntaxCheckerDialog = SyntaxCheckerDialog()
        self.__projectBrowserSyntaxCheckerDialog.show()
        self.__projectBrowserSyntaxCheckerDialog.start(fn)
    
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
            self.__editorAct.setEnabled(
                editor.isPy3File() or editor.isPy2File())
    
    def __editorSyntaxCheck(self):
        """
        Private slot to handle the syntax check context menu action of the
        editors.
        """
        editor = e5App().getObject("ViewManager").activeWindow()
        if editor is not None:
                from CheckerPlugins.SyntaxChecker.SyntaxCheckerDialog import \
                    SyntaxCheckerDialog
                self.__editorSyntaxCheckerDialog = SyntaxCheckerDialog()
                self.__editorSyntaxCheckerDialog.show()
                self.__editorSyntaxCheckerDialog.start(
                    editor.getFileName() or "Unnamed.py", editor.text())
