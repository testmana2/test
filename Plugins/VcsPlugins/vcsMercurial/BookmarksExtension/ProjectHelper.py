# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the bookmarks extension project helper.
"""

from PyQt4.QtCore import QObject
from PyQt4.QtGui import QMenu

from E5Gui.E5Action import E5Action


class BookmarksProjectHelper(QObject):
    """
    Class implementing the bookmarks extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        QObject.__init__(self)
        
        self.actions = []
        
        self.initActions()
    
    def setObjects(self, vcsObject, projectObject):
        """
        Public method to set references to the vcs and project objects.
        
        @param vcsObject reference to the vcs object
        @param projectObject reference to the project object
        """
        self.vcs = vcsObject
        self.project = projectObject
    
    def getActions(self):
        """
        Public method to get a list of all actions.
        
        @return list of all actions (list of E5Action)
        """
        return self.actions[:]
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.hgBookmarksListAct = E5Action(self.trUtf8('List bookmarks'),
                self.trUtf8('List bookmarks...'),
                0, 0, self, 'mercurial_list_bookmarks')
        self.hgBookmarksListAct.setStatusTip(self.trUtf8(
            'List bookmarks of the project'
        ))
        self.hgBookmarksListAct.setWhatsThis(self.trUtf8(
            """<b>List bookmarks</b>"""
            """<p>This lists the bookmarks of the project.</p>"""
        ))
        self.hgBookmarksListAct.triggered[()].connect(self.__hgBookmarksList)
        self.actions.append(self.hgBookmarksListAct)
    
        self.hgBookmarkDefineAct = E5Action(self.trUtf8('Define bookmark'),
                self.trUtf8('Define bookmark...'),
                0, 0, self, 'mercurial_define_bookmark')
        self.hgBookmarkDefineAct.setStatusTip(self.trUtf8(
            'Define a bookmark for the project'
        ))
        self.hgBookmarkDefineAct.setWhatsThis(self.trUtf8(
            """<b>Define bookmark</b>"""
            """<p>This defines a bookmark for the project.</p>"""
        ))
        self.hgBookmarkDefineAct.triggered[()].connect(self.__hgBookmarkDefine)
        self.actions.append(self.hgBookmarkDefineAct)
    
        self.hgBookmarkDeleteAct = E5Action(self.trUtf8('Delete bookmark'),
                self.trUtf8('Delete bookmark...'),
                0, 0, self, 'mercurial_delete_bookmark')
        self.hgBookmarkDeleteAct.setStatusTip(self.trUtf8(
            'Delete a bookmark of the project'
        ))
        self.hgBookmarkDeleteAct.setWhatsThis(self.trUtf8(
            """<b>Delete bookmark</b>"""
            """<p>This deletes a bookmark of the project.</p>"""
        ))
        self.hgBookmarkDeleteAct.triggered[()].connect(self.__hgBookmarkDelete)
        self.actions.append(self.hgBookmarkDeleteAct)
    
        self.hgBookmarkRenameAct = E5Action(self.trUtf8('Rename bookmark'),
                self.trUtf8('Rename bookmark...'),
                0, 0, self, 'mercurial_rename_bookmark')
        self.hgBookmarkRenameAct.setStatusTip(self.trUtf8(
            'Rename a bookmark of the project'
        ))
        self.hgBookmarkRenameAct.setWhatsThis(self.trUtf8(
            """<b>Rename bookmark</b>"""
            """<p>This renames a bookmark of the project.</p>"""
        ))
        self.hgBookmarkRenameAct.triggered[()].connect(self.__hgBookmarkRename)
        self.actions.append(self.hgBookmarkRenameAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the VCS menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.trUtf8("Bookmarks"), mainMenu)
        
        menu.addAction(self.hgBookmarkDefineAct)
        menu.addAction(self.hgBookmarkDeleteAct)
        menu.addAction(self.hgBookmarkRenameAct)
        menu.addSeparator()
        menu.addAction(self.hgBookmarksListAct)
        
        return menu
    
    def __hgBookmarksList(self):
        """
        Private slot used to list the bookmarks. 
        """
        self.vcs.getExtensionObject("bookmarks")\
            .hgListBookmarks(self.project.getProjectPath())
    
    def __hgBookmarkDefine(self):
        """
        Private slot used to define a bookmark.
        """
        self.vcs.getExtensionObject("bookmarks")\
            .hgBookmarkDefine(self.project.getProjectPath())
    
    def __hgBookmarkDelete(self):
        """
        Private slot used to delete a bookmark.
        """
        self.vcs.getExtensionObject("bookmarks")\
            .hgBookmarkDelete(self.project.getProjectPath())
    
    def __hgBookmarkRename(self):
        """
        Private slot used to delete a bookmark.
        """
        self.vcs.getExtensionObject("bookmarks")\
            .hgBookmarkRename(self.project.getProjectPath())
