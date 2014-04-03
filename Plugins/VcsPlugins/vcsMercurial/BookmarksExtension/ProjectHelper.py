# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the bookmarks extension project helper.
"""

from __future__ import unicode_literals

from PyQt4.QtGui import QMenu

from E5Gui.E5Action import E5Action

from ..HgExtensionProjectHelper import HgExtensionProjectHelper

import UI.PixmapCache


class BookmarksProjectHelper(HgExtensionProjectHelper):
    """
    Class implementing the bookmarks extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        super(BookmarksProjectHelper, self).__init__()
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.hgBookmarksListAct = E5Action(
            self.tr('List bookmarks'),
            UI.PixmapCache.getIcon("listBookmarks.png"),
            self.tr('List bookmarks...'),
            0, 0, self, 'mercurial_list_bookmarks')
        self.hgBookmarksListAct.setStatusTip(self.tr(
            'List bookmarks of the project'
        ))
        self.hgBookmarksListAct.setWhatsThis(self.tr(
            """<b>List bookmarks</b>"""
            """<p>This lists the bookmarks of the project.</p>"""
        ))
        self.hgBookmarksListAct.triggered.connect(self.__hgBookmarksList)
        self.actions.append(self.hgBookmarksListAct)
    
        self.hgBookmarkDefineAct = E5Action(
            self.tr('Define bookmark'),
            UI.PixmapCache.getIcon("addBookmark.png"),
            self.tr('Define bookmark...'),
            0, 0, self, 'mercurial_define_bookmark')
        self.hgBookmarkDefineAct.setStatusTip(self.tr(
            'Define a bookmark for the project'
        ))
        self.hgBookmarkDefineAct.setWhatsThis(self.tr(
            """<b>Define bookmark</b>"""
            """<p>This defines a bookmark for the project.</p>"""
        ))
        self.hgBookmarkDefineAct.triggered.connect(self.__hgBookmarkDefine)
        self.actions.append(self.hgBookmarkDefineAct)
    
        self.hgBookmarkDeleteAct = E5Action(
            self.tr('Delete bookmark'),
            UI.PixmapCache.getIcon("deleteBookmark.png"),
            self.tr('Delete bookmark...'),
            0, 0, self, 'mercurial_delete_bookmark')
        self.hgBookmarkDeleteAct.setStatusTip(self.tr(
            'Delete a bookmark of the project'
        ))
        self.hgBookmarkDeleteAct.setWhatsThis(self.tr(
            """<b>Delete bookmark</b>"""
            """<p>This deletes a bookmark of the project.</p>"""
        ))
        self.hgBookmarkDeleteAct.triggered.connect(self.__hgBookmarkDelete)
        self.actions.append(self.hgBookmarkDeleteAct)
    
        self.hgBookmarkRenameAct = E5Action(
            self.tr('Rename bookmark'),
            UI.PixmapCache.getIcon("renameBookmark.png"),
            self.tr('Rename bookmark...'),
            0, 0, self, 'mercurial_rename_bookmark')
        self.hgBookmarkRenameAct.setStatusTip(self.tr(
            'Rename a bookmark of the project'
        ))
        self.hgBookmarkRenameAct.setWhatsThis(self.tr(
            """<b>Rename bookmark</b>"""
            """<p>This renames a bookmark of the project.</p>"""
        ))
        self.hgBookmarkRenameAct.triggered.connect(self.__hgBookmarkRename)
        self.actions.append(self.hgBookmarkRenameAct)
    
        self.hgBookmarkMoveAct = E5Action(
            self.tr('Move bookmark'),
            UI.PixmapCache.getIcon("moveBookmark.png"),
            self.tr('Move bookmark...'),
            0, 0, self, 'mercurial_move_bookmark')
        self.hgBookmarkMoveAct.setStatusTip(self.tr(
            'Move a bookmark of the project'
        ))
        self.hgBookmarkMoveAct.setWhatsThis(self.tr(
            """<b>Move bookmark</b>"""
            """<p>This moves a bookmark of the project to another"""
            """ changeset.</p>"""
        ))
        self.hgBookmarkMoveAct.triggered.connect(self.__hgBookmarkMove)
        self.actions.append(self.hgBookmarkMoveAct)
        
        self.hgBookmarkIncomingAct = E5Action(
            self.tr('Show incoming bookmarks'),
            UI.PixmapCache.getIcon("incomingBookmark.png"),
            self.tr('Show incoming bookmarks'),
            0, 0, self, 'mercurial_incoming_bookmarks')
        self.hgBookmarkIncomingAct.setStatusTip(self.tr(
            'Show a list of incoming bookmarks'
        ))
        self.hgBookmarkIncomingAct.setWhatsThis(self.tr(
            """<b>Show incoming bookmarks</b>"""
            """<p>This shows a list of new bookmarks available at the remote"""
            """ repository.</p>"""
        ))
        self.hgBookmarkIncomingAct.triggered.connect(
            self.__hgBookmarkIncoming)
        self.actions.append(self.hgBookmarkIncomingAct)
        
        self.hgBookmarkPullAct = E5Action(
            self.tr('Pull bookmark'),
            UI.PixmapCache.getIcon("pullBookmark.png"),
            self.tr('Pull bookmark'),
            0, 0, self, 'mercurial_pull_bookmark')
        self.hgBookmarkPullAct.setStatusTip(self.tr(
            'Pull a bookmark from a remote repository'
        ))
        self.hgBookmarkPullAct.setWhatsThis(self.tr(
            """<b>Pull bookmark</b>"""
            """<p>This pulls a bookmark from a remote repository into the """
            """local repository.</p>"""
        ))
        self.hgBookmarkPullAct.triggered.connect(self.__hgBookmarkPull)
        self.actions.append(self.hgBookmarkPullAct)
        
        self.hgBookmarkOutgoingAct = E5Action(
            self.tr('Show outgoing bookmarks'),
            UI.PixmapCache.getIcon("outgoingBookmark.png"),
            self.tr('Show outgoing bookmarks'),
            0, 0, self, 'mercurial_outgoing_bookmarks')
        self.hgBookmarkOutgoingAct.setStatusTip(self.tr(
            'Show a list of outgoing bookmarks'
        ))
        self.hgBookmarkOutgoingAct.setWhatsThis(self.tr(
            """<b>Show outgoing bookmarks</b>"""
            """<p>This shows a list of new bookmarks available at the local"""
            """ repository.</p>"""
        ))
        self.hgBookmarkOutgoingAct.triggered.connect(
            self.__hgBookmarkOutgoing)
        self.actions.append(self.hgBookmarkOutgoingAct)
        
        self.hgBookmarkPushAct = E5Action(
            self.tr('Push bookmark'),
            UI.PixmapCache.getIcon("pushBookmark.png"),
            self.tr('Push bookmark'),
            0, 0, self, 'mercurial_push_bookmark')
        self.hgBookmarkPushAct.setStatusTip(self.tr(
            'Push a bookmark to a remote repository'
        ))
        self.hgBookmarkPushAct.setWhatsThis(self.tr(
            """<b>Push bookmark</b>"""
            """<p>This pushes a bookmark from the local repository to a """
            """remote repository.</p>"""
        ))
        self.hgBookmarkPushAct.triggered.connect(self.__hgBookmarkPush)
        self.actions.append(self.hgBookmarkPushAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.menuTitle(), mainMenu)
        menu.setIcon(UI.PixmapCache.getIcon("bookmark22.png"))
        menu.setTearOffEnabled(True)
        
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
        
        menu.aboutToShow.connect(self.__aboutToShowMenu)
        
        return menu
    
    def __aboutToShowMenu(self):
        """
        Private slot to handle the aboutToShow signal of the background menu.
        """
        self.hgBookmarkPullAct.setEnabled(self.vcs.canPull())
        self.hgBookmarkIncomingAct.setEnabled(self.vcs.canPull())
        
        self.hgBookmarkPushAct.setEnabled(self.vcs.canPush())
        self.hgBookmarkOutgoingAct.setEnabled(self.vcs.canPush())
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        @return title of the menu (string)
        """
        return self.tr("Bookmarks")
    
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
