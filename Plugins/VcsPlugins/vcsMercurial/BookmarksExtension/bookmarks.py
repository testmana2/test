# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the bookmarks extension interface.
"""

import os

from PyQt4.QtCore import QObject
from PyQt4.QtGui import QDialog, QInputDialog

from ..HgDialog import HgDialog

from .HgBookmarksListDialog import HgBookmarksListDialog
from .HgBookmarkDialog import HgBookmarkDialog
from .HgBookmarkRenameDialog import HgBookmarkRenameDialog


class Bookmarks(QObject):
    """
    Class implementing the bookmarks extension interface.
    """
    def __init__(self, vcs):
        """
        Constructor
        """
        QObject.__init__(self, vcs)
        
        self.vcs = vcs
        
        self.bookmarksListDlg = None
        self.bookmarksList = []
    
    def shutdown(self):
        """
        Public method used to shutdown the bookmarks interface.
        """
        if self.bookmarksListDlg is not None:
            self.bookmarksListDlg.close()
    
    def hgListBookmarks(self, path):
        """
        Public method used to list the available bookmarks.
        
        @param path directory name of the project (string)
        """
        self.bookmarksList = []
        
        self.bookmarksListDlg = HgBookmarksListDialog(self.vcs)
        self.bookmarksListDlg.show()
        self.bookmarksListDlg.start(path, self.bookmarksList)
    
    def hgGetLoadedBookmarksList(self):
        """
        Public method to get the list of loaded bookmarks.
        
        @return list of loaded bookmarks (list of string)
        """
        return self.bookmarksList[:]
    
    def hgBookmarkDefine(self, name):
        """
        Public method to define a bookmark.
        
        @param name file/directory name (string)
        """
        dname, fname = self.vcs.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        dlg = HgBookmarkDialog(self.vcs.tagsList, self.vcs.branchesList, 
            self.bookmarksList)
        if dlg.exec_() == QDialog.Accepted:
            rev, bookmark = dlg.getData()
            
            args = []
            args.append("bookmarks")
            if rev:
                args.append("--rev")
                args.append(rev)
            args.append(bookmark)
            
            dia = HgDialog(self.trUtf8('Mercurial Bookmark'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgBookmarkDelete(self, name):
        """
        Public method to delete a bookmark.
        
        @param name file/directory name (string)
        """
        dname, fname = self.vcs.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        bookmark, ok = QInputDialog.getItem(
            None,
            self.trUtf8("Delete Bookmark"),
            self.trUtf8("Select the bookmark to be deleted:"),
            [""] + self.bookmarksList,
            0, True)
        if ok and bookmark:
            args = []
            args.append("bookmarks")
            args.append("--delete")
            args.append(bookmark)
            
            dia = HgDialog(self.trUtf8('Delete Mercurial Bookmark'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgBookmarkRename(self, name):
        """
        Public method to rename a bookmark.
        
        @param name file/directory name (string)
        """
        dname, fname = self.vcs.splitPath(name)
        
        # find the root of the repo
        repodir = str(dname)
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        dlg = HgBookmarkRenameDialog(self.bookmarksList)
        if dlg.exec_() == QDialog.Accepted:
            newName, oldName = dlg.getData()
            
            args = []
            args.append("bookmarks")
            args.append("--rename")
            args.append(oldName)
            args.append(newName)
            
            dia = HgDialog(self.trUtf8('Delete Mercurial Bookmark'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
