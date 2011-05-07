# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the bookmarks extension interface.
"""

import os

from PyQt4.QtCore import QObject, QProcess
from PyQt4.QtGui import QDialog, QInputDialog

from ..HgDialog import HgDialog

from .HgBookmarksListDialog import HgBookmarksListDialog
from .HgBookmarkDialog import HgBookmarkDialog
from .HgBookmarkRenameDialog import HgBookmarkRenameDialog
from .HgBookmarksInOutDialog import HgBookmarksInOutDialog

import Preferences


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
        self.bookmarksInOutDlg = None
        self.bookmarksList = []
    
    def shutdown(self):
        """
        Public method used to shutdown the bookmarks interface.
        """
        if self.bookmarksListDlg is not None:
            self.bookmarksListDlg.close()
        if self.bookmarksInOutDlg is not None:
            self.bookmarksInOutDlg.close()
    
    def hgListBookmarks(self, path):
        """
        Public method used to list the available bookmarks.
        
        @param path directory name of the project (string)
        """
        self.bookmarksList = []
        
        self.bookmarksListDlg = HgBookmarksListDialog(self.vcs)
        self.bookmarksListDlg.show()
        self.bookmarksListDlg.start(path, self.bookmarksList)
    
    def hgGetBookmarksList(self, repodir):
        """
        Public method to get the list of bookmarks.
        
        @param repodir directory name of the repository (string)
        @return list of bookmarks (list of string)
        """
        ioEncoding = Preferences.getSystem("IOEncoding")
        process = QProcess()
        args = []
        args.append('bookmarks')
        process.setWorkingDirectory(repodir)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                output = \
                    str(process.readAllStandardOutput(), ioEncoding, 'replace')
                self.bookmarksList = []
                for line in output.splitlines():
                    l = line.strip().split()
                    if l[-1][0] in "1234567890":
                        # last element is a rev:changeset
                        del l[-1]
                        if l[0] == "*":
                            del l[0]
                        name = " ".join(l)
                        self.bookmarksList.append(name)
        
        return self.bookmarksList[:]
    
    def hgBookmarkDefine(self, name):
        """
        Public method to define a bookmark.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        dlg = HgBookmarkDialog(HgBookmarkDialog.DEFINE_MODE, 
                               self.vcs.hgGetTagsList(repodir),
                               self.vcs.hgGetBranchesList(repodir),
                               self.hgGetBookmarksList(repodir))
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
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        bookmark, ok = QInputDialog.getItem(
            None,
            self.trUtf8("Delete Bookmark"),
            self.trUtf8("Select the bookmark to be deleted:"),
            [""] + sorted(self.hgGetBookmarksList(repodir)),
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
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        dlg = HgBookmarkRenameDialog(self.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            newName, oldName = dlg.getData()
            
            args = []
            args.append("bookmarks")
            args.append("--rename")
            args.append(oldName)
            args.append(newName)
            
            dia = HgDialog(self.trUtf8('Rename Mercurial Bookmark'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgBookmarkMove(self, name):
        """
        Public method to move a bookmark.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        dlg = HgBookmarkDialog(HgBookmarkDialog.MOVE_MODE, 
                               self.vcs.hgGetTagsList(repodir),
                               self.vcs.hgGetBranchesList(repodir),
                               self.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            rev, bookmark = dlg.getData()
            
            args = []
            args.append("bookmarks")
            args.append("--force")
            if rev:
                args.append("--rev")
                args.append(rev)
            args.append(bookmark)
            
            dia = HgDialog(self.trUtf8('Move Mercurial Bookmark'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgBookmarkIncoming(self, name):
        """
        Public method to show a list of incoming bookmarks.
        
        @param name file/directory name (string)
        """
        self.bookmarksInOutDlg = HgBookmarksInOutDialog(
            self.vcs, HgBookmarksInOutDialog.INCOMING)
        self.bookmarksInOutDlg.show()
        self.bookmarksInOutDlg.start(name)
    
    def hgBookmarkOutgoing(self, name):
        """
        Public method to show a list of outgoing bookmarks.
        
        @param name file/directory name (string)
        """
        self.bookmarksInOutDlg = HgBookmarksInOutDialog(
            self.vcs, HgBookmarksInOutDialog.OUTGOING)
        self.bookmarksInOutDlg.show()
        self.bookmarksInOutDlg.start(name)
    
    def __getInOutBookmarks(self, repodir, incoming):
        """
        Public method to get the list of incoming or outgoing bookmarks.
        
        @param repodir directory name of the repository (string)
        @param incoming flag indicating to get incoming bookmarks (boolean)
        @return list of bookmarks (list of string)
        """
        bookmarksList = []
        
        ioEncoding = Preferences.getSystem("IOEncoding")
        process = QProcess()
        args = []
        if incoming:
            args.append('incoming')
        else:
            args.append('outgoing')
        args.append('--bookmarks')
        process.setWorkingDirectory(repodir)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                output = \
                    str(process.readAllStandardOutput(), ioEncoding, 'replace')
                for line in output.splitlines():
                    if line.startswith(" "):
                        l = line.strip().split()
                        del l[-1]
                        name = " ".join(l)
                        bookmarksList.append(name)
        
        return bookmarksList
    
    def hgBookmarkPull(self, name):
        """
        Public method to pull a bookmark from a remote repository.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        bookmarks = self.__getInOutBookmarks(repodir, True)
        
        bookmark, ok = QInputDialog.getItem(
            None,
            self.trUtf8("Pull Bookmark"),
            self.trUtf8("Select the bookmark to be pulled:"),
            [""] + sorted(bookmarks),
            0, True)
        if ok and bookmark:
            args = []
            args.append('pull')
            args.append('--bookmark')
            args.append(bookmark)
        
        dia = HgDialog(self.trUtf8('Pulling bookmark from a remote Mercurial repository'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
    
    def hgBookmarkPush(self, name):
        """
        Public method to push a bookmark to a remote repository.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        bookmarks = self.__getInOutBookmarks(repodir, False)
        
        bookmark, ok = QInputDialog.getItem(
            None,
            self.trUtf8("Push Bookmark"),
            self.trUtf8("Select the bookmark to be push:"),
            [""] + sorted(bookmarks),
            0, True)
        if ok and bookmark:
            args = []
            args.append('push')
            args.append('--bookmark')
            args.append(bookmark)
        
        dia = HgDialog(self.trUtf8('Pushing bookmark to a remote Mercurial repository'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
