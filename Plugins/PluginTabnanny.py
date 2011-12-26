# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Tabnanny plugin.
"""

import os

from PyQt4.QtCore import QObject

from E5Gui.E5Application import e5App

from E5Gui.E5Action import E5Action

from CheckerPlugins.Tabnanny.TabnannyDialog import TabnannyDialog

import Preferences

# Start-Of-Header
name = "Tabnanny Plugin"
author = "Detlev Offenbach <detlev@die-offenbachs.de>"
autoactivate = True
deactivateable = True
version = "5.1.0"
className = "TabnannyPlugin"
packageName = "__core__"
shortDescription = "Show the Tabnanny dialog."
longDescription = """This plugin implements the Tabnanny dialog.""" \
 """ Tabnanny is used to check Python source files for correct indentations."""
pyqtApi = 2
# End-Of-Header

error = ""

class TabnannyPlugin(QObject):
    """
    Class implementing the Tabnanny plugin.
    """
    def __init__(self, ui):
        """
        Constructor
        
        @param ui reference to the user interface object (UI.UserInterface)
        """
        QObject.__init__(self, ui)
        self.__ui = ui
        self.__initialize()
        
    def __initialize(self):
        """
        Private slot to (re)initialize the plugin.
        """
        self.__projectAct = None
        self.__projectTabnannyDialog = None
        
        self.__projectBrowserAct = None
        self.__projectBrowserMenu = None
        self.__projectBrowserTabnannyDialog = None
        
        self.__editors = []
        self.__editorAct = None
        self.__editorTabnannyDialog = None

    def activate(self):
        """
        Public method to activate this plugin.
        
        @return tuple of None and activation status (boolean)
        """
        menu = e5App().getObject("Project").getMenu("Checks")
        if menu:
            self.__projectAct = E5Action(self.trUtf8('Check Indentations'),
                    self.trUtf8('&Indentations...'), 0, 0,
                    self,'project_check_indentations')
            self.__projectAct.setStatusTip(
                self.trUtf8('Check indentations using tabnanny.'))
            self.__projectAct.setWhatsThis(self.trUtf8(
                """<b>Check Indentations...</b>"""
                """<p>This checks Python files"""
                """ for bad indentations using tabnanny.</p>"""
            ))
            self.__projectAct.triggered[()].connect(self.__projectTabnanny)
            e5App().getObject("Project").addE5Actions([self.__projectAct])
            menu.addAction(self.__projectAct)
        
        self.__editorAct = E5Action(self.trUtf8('Check Indentations'),
                self.trUtf8('&Indentations...'), 0, 0,
                self, "")
        self.__editorAct.setWhatsThis(self.trUtf8(
            """<b>Check Indentations...</b>"""
            """<p>This checks Python files"""
            """ for bad indentations using tabnanny.</p>"""
        ))
        self.__editorAct.triggered[()].connect(self.__editorTabnanny)
        
        e5App().getObject("Project").showMenu.connect(self.__projectShowMenu)
        e5App().getObject("ProjectBrowser").getProjectBrowser("sources")\
            .showMenu.connect(self.__projectBrowserShowMenu)
        e5App().getObject("ViewManager").editorOpenedEd.connect(self.__editorOpened)
        e5App().getObject("ViewManager").editorClosedEd.connect(self.__editorClosed)
        
        for editor in e5App().getObject("ViewManager").getOpenEditors():
            self.__editorOpened(editor)
        
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        e5App().getObject("Project").showMenu.disconnect(self.__projectShowMenu)
        e5App().getObject("ProjectBrowser").getProjectBrowser("sources")\
            .showMenu.disconnect(self.__projectBrowserShowMenu)
        e5App().getObject("ViewManager").editorOpenedEd.disconnect(self.__editorOpened)
        e5App().getObject("ViewManager").editorClosedEd.disconnect(self.__editorClosed)
        
        menu = e5App().getObject("Project").getMenu("Checks")
        if menu:
            menu.removeAction(self.__projectAct)
        
        if self.__projectBrowserMenu:
            if self.__projectBrowserAct:
                self.__projectBrowserMenu.removeAction(self.__projectBrowserAct)
        
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
        Private slot called, when the the project browser context menu or a submenu is 
        about to be shown.
        
        @param menuName name of the menu to be shown (string)
        @param menu reference to the menu (QMenu)
        """
        if menuName == "Checks" and \
           e5App().getObject("Project").getProjectLanguage() in \
                ["Python3", "Python2", "Python"]:
            self.__projectBrowserMenu = menu
            if self.__projectBrowserAct is None:
                self.__projectBrowserAct = E5Action(self.trUtf8('Check Indentations'),
                        self.trUtf8('&Indentations...'), 0, 0,
                        self, "")
                self.__projectBrowserAct.setWhatsThis(self.trUtf8(
                    """<b>Check Indentations...</b>"""
                    """<p>This checks Python files"""
                    """ for bad indentations using tabnanny.</p>"""
                ))
                self.__projectBrowserAct.triggered[()].connect(
                    self.__projectBrowserTabnanny)
            if not self.__projectBrowserAct in menu.actions():
                menu.addAction(self.__projectBrowserAct)
    
    def __projectTabnanny(self):
        """
        Public slot used to check the project files for bad indentations.
        """
        project = e5App().getObject("Project")
        project.saveAllScripts()
        ppath = project.getProjectPath()
        files = [os.path.join(ppath, file) \
            for file in project.pdata["SOURCES"] \
                if file.endswith(tuple(Preferences.getPython("Python3Extensions")) +
                                 tuple(Preferences.getPython("PythonExtensions")))]
        
        self.__projectTabnannyDialog = TabnannyDialog()
        self.__projectTabnannyDialog.show()
        self.__projectTabnannyDialog.prepare(files, project)
    
    def __projectBrowserTabnanny(self):
        """
        Private method to handle the tabnanny context menu action of the project
        sources browser.
        """
        browser = e5App().getObject("ProjectBrowser").getProjectBrowser("sources")
        itm = browser.model().item(browser.currentIndex())
        try:
            fn = itm.fileName()
        except AttributeError:
            fn = itm.dirName()
        
        self.__projectBrowserTabnannyDialog = TabnannyDialog()
        self.__projectBrowserTabnannyDialog.show()
        self.__projectBrowserTabnannyDialog.start(fn)
    
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
    
    def __editorTabnanny(self):
        """
        Private slot to handle the tabnanny context menu action of the editors.
        """
        editor = e5App().getObject("ViewManager").activeWindow()
        if editor is not None:
            if editor.checkDirty() and editor.getFileName() is not None:
                self.__editorTabnannyDialog = TabnannyDialog()
                self.__editorTabnannyDialog.show()
                self.__editorTabnannyDialog.start(editor.getFileName())
