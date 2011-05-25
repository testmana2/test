# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the bookmarks extension project helper.
"""

from PyQt4.QtCore import QObject
from PyQt4.QtGui import QMenu

from E5Gui.E5Action import E5Action

import UI.PixmapCache


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
                UI.PixmapCache.getIcon("listBookmarks.png"),
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
                UI.PixmapCache.getIcon("addBookmark.png"),
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
                UI.PixmapCache.getIcon("deleteBookmark.png"),
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
                UI.PixmapCache.getIcon("renameBookmark.png"),
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
    
        self.hgBookmarkMoveAct = E5Action(self.trUtf8('Move bookmark'),
                UI.PixmapCache.getIcon("moveBookmark.png"),
                self.trUtf8('Move bookmark...'),
                0, 0, self, 'mercurial_move_bookmark')
        self.hgBookmarkMoveAct.setStatusTip(self.trUtf8(
            'Move a bookmark of the project'
        ))
        self.hgBookmarkMoveAct.setWhatsThis(self.trUtf8(
            """<b>Move bookmark</b>"""
            """<p>This moves a bookmark of the project to another changeset.</p>"""
        ))
        self.hgBookmarkMoveAct.triggered[()].connect(self.__hgBookmarkMove)
        self.actions.append(self.hgBookmarkMoveAct)
        
        self.hgBookmarkIncomingAct = E5Action(self.trUtf8('Show incoming bookmarks'),
                UI.PixmapCache.getIcon("incomingBookmark.png"),
                self.trUtf8('Show incoming bookmarks'),
                0, 0, self, 'mercurial_incoming_bookmarks')
        self.hgBookmarkIncomingAct.setStatusTip(self.trUtf8(
            'Show a list of incoming bookmarks'
        ))
        self.hgBookmarkIncomingAct.setWhatsThis(self.trUtf8(
            """<b>Show incoming bookmarks</b>"""
            """<p>This shows a list of new bookmarks available at the remote"""
            """ repository.</p>"""
        ))
        self.hgBookmarkIncomingAct.triggered[()].connect(self.__hgBookmarkIncoming)
        self.actions.append(self.hgBookmarkIncomingAct)
        
        self.hgBookmarkPullAct = E5Action(self.trUtf8('Pull bookmark'),
                UI.PixmapCache.getIcon("pullBookmark.png"),
                self.trUtf8('Pull bookmark'),
                0, 0, self, 'mercurial_pull_bookmark')
        self.hgBookmarkPullAct.setStatusTip(self.trUtf8(
            'Pull a bookmark from a remote repository'
        ))
        self.hgBookmarkPullAct.setWhatsThis(self.trUtf8(
            """<b>Pull bookmark</b>"""
            """<p>This pulls a bookmark from a remote repository into the """
            """local repository.</p>"""
        ))
        self.hgBookmarkPullAct.triggered[()].connect(self.__hgBookmarkPull)
        self.actions.append(self.hgBookmarkPullAct)
        
        self.hgBookmarkOutgoingAct = E5Action(self.trUtf8('Show outgoing bookmarks'),
                UI.PixmapCache.getIcon("outgoingBookmark.png"),
                self.trUtf8('Show outgoing bookmarks'),
                0, 0, self, 'mercurial_outgoing_bookmarks')
        self.hgBookmarkOutgoingAct.setStatusTip(self.trUtf8(
            'Show a list of outgoing bookmarks'
        ))
        self.hgBookmarkOutgoingAct.setWhatsThis(self.trUtf8(
            """<b>Show outgoing bookmarks</b>"""
            """<p>This shows a list of new bookmarks available at the local"""
            """ repository.</p>"""
        ))
        self.hgBookmarkOutgoingAct.triggered[()].connect(self.__hgBookmarkOutgoing)
        self.actions.append(self.hgBookmarkOutgoingAct)
        
        self.hgBookmarkPushAct = E5Action(self.trUtf8('Push bookmark'),
                UI.PixmapCache.getIcon("pushBookmark.png"),
                self.trUtf8('Push bookmark'),
                0, 0, self, 'mercurial_push_bookmark')
        self.hgBookmarkPushAct.setStatusTip(self.trUtf8(
            'Push a bookmark to a remote repository'
        ))
        self.hgBookmarkPushAct.setWhatsThis(self.trUtf8(
            """<b>Push bookmark</b>"""
            """<p>This pushes a bookmark from the local repository to a """
            """remote repository.</p>"""
        ))
        self.hgBookmarkPushAct.triggered[()].connect(self.__hgBookmarkPush)
        self.actions.append(self.hgBookmarkPushAct)
    
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
        menu.addAction(self.hgBookmarkMoveAct)
        menu.addSeparator()
        menu.addAction(self.hgBookmarksListAct)
        menu.addSeparator()
        menu.addAction(self.hgBookmarkIncomingAct)
        menu.addAction(self.hgBookmarkPullAct)
        menu.addSeparator()
        menu.addAction(self.hgBookmarkOutgoingAct)
        menu.addAction(self.hgBookmarkPushAct)
        
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
        Private slot used to rename a bookmark.
        """
        self.vcs.getExtensionObject("bookmarks")\
            .hgBookmarkRename(self.project.getProjectPath())
    
    def __hgBookmarkMove(self):
        """
        Private slot used to move a bookmark.
        """
        self.vcs.getExtensionObject("bookmarks")\
            .hgBookmarkMove(self.project.getProjectPath())
    
    def __hgBookmarkIncoming(self):
        """
        Private slot used to show a list of incoming bookmarks.
        """
        self.vcs.getExtensionObject("bookmarks")\
            .hgBookmarkIncoming(self.project.getProjectPath())
    
    def __hgBookmarkOutgoing(self):
        """
        Private slot used to show a list of outgoing bookmarks.
        """
        self.vcs.getExtensionObject("bookmarks")\
            .hgBookmarkOutgoing(self.project.getProjectPath())
    
    def __hgBookmarkPull(self):
        """
        Private slot used to pull a bookmark from a remote repository.
        """
        self.vcs.getExtensionObject("bookmarks")\
            .hgBookmarkPull(self.project.getProjectPath())
    
    def __hgBookmarkPush(self):
        """
        Private slot used to push a bookmark to a remote repository.
        """
        self.vcs.getExtensionObject("bookmarks")\
            .hgBookmarkPush(self.project.getProjectPath())
