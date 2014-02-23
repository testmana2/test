# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the bookmarks extension interface.
"""

import os

from PyQt4.QtCore import QProcess
from PyQt4.QtGui import QDialog, QInputDialog

from ..HgExtension import HgExtension
from ..HgDialog import HgDialog


class Bookmarks(HgExtension):
    """
    Class implementing the bookmarks extension interface.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        super().__init__(vcs)
        
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
        
        from .HgBookmarksListDialog import HgBookmarksListDialog
        self.bookmarksListDlg = HgBookmarksListDialog(self.vcs)
        self.bookmarksListDlg.show()
        self.bookmarksListDlg.start(path, self.bookmarksList)
    
    def hgGetBookmarksList(self, repodir):
        """
        Public method to get the list of bookmarks.
        
        @param repodir directory name of the repository (string)
        @return list of bookmarks (list of string)
        """
        args = self.vcs.initCommand("bookmarks")
        
        client = self.vcs.getClient()
        output = ""
        if client:
            output = client.runcommand(args)[0]
        else:
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.vcs.getEncoding(), 'replace')
        
        self.bookmarksList = []
        for line in output.splitlines():
            li = line.strip().split()
            if li[-1][0] in "1234567890":
                # last element is a rev:changeset
                del li[-1]
                if li[0] == "*":
                    del li[0]
                name = " ".join(li)
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
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgBookmarkDialog import HgBookmarkDialog
        dlg = HgBookmarkDialog(HgBookmarkDialog.DEFINE_MODE,
                               self.vcs.hgGetTagsList(repodir),
                               self.vcs.hgGetBranchesList(repodir),
                               self.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            rev, bookmark = dlg.getData()
            
            args = self.vcs.initCommand("bookmarks")
            if rev:
                args.append("--rev")
                args.append(rev)
            args.append(bookmark)
            
            dia = HgDialog(self.tr('Mercurial Bookmark'), self.vcs)
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
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        bookmark, ok = QInputDialog.getItem(
            None,
            self.tr("Delete Bookmark"),
            self.tr("Select the bookmark to be deleted:"),
            [""] + sorted(self.hgGetBookmarksList(repodir)),
            0, True)
        if ok and bookmark:
            args = self.vcs.initCommand("bookmarks")
            args.append("--delete")
            args.append(bookmark)
            
            dia = HgDialog(self.tr('Delete Mercurial Bookmark'), self.vcs)
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
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgBookmarkRenameDialog import HgBookmarkRenameDialog
        dlg = HgBookmarkRenameDialog(self.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            newName, oldName = dlg.getData()
            
            args = self.vcs.initCommand("bookmarks")
            args.append("--rename")
            args.append(oldName)
            args.append(newName)
            
            dia = HgDialog(self.tr('Rename Mercurial Bookmark'), self.vcs)
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
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        from .HgBookmarkDialog import HgBookmarkDialog
        dlg = HgBookmarkDialog(HgBookmarkDialog.MOVE_MODE,
                               self.vcs.hgGetTagsList(repodir),
                               self.vcs.hgGetBranchesList(repodir),
                               self.hgGetBookmarksList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            rev, bookmark = dlg.getData()
            
            args = self.vcs.initCommand("bookmarks")
            args.append("--force")
            if rev:
                args.append("--rev")
                args.append(rev)
            args.append(bookmark)
            
            dia = HgDialog(self.tr('Move Mercurial Bookmark'), self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgBookmarkIncoming(self, name):
        """
        Public method to show a list of incoming bookmarks.
        
        @param name file/directory name (string)
        """
        from .HgBookmarksInOutDialog import HgBookmarksInOutDialog
        self.bookmarksInOutDlg = HgBookmarksInOutDialog(
            self.vcs, HgBookmarksInOutDialog.INCOMING)
        self.bookmarksInOutDlg.show()
        self.bookmarksInOutDlg.start(name)
    
    def hgBookmarkOutgoing(self, name):
        """
        Public method to show a list of outgoing bookmarks.
        
        @param name file/directory name (string)
        """
        from .HgBookmarksInOutDialog import HgBookmarksInOutDialog
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
        
        if incoming:
            args = self.vcs.initCommand("incoming")
        else:
            args = self.vcs.initCommand("outgoing")
        args.append('--bookmarks')
        
        client = self.vcs.getClient()
        output = ""
        if client:
            output = client.runcommand(args)[0]
        else:
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted(5000)
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    output = str(process.readAllStandardOutput(),
                                 self.vcs.getEncoding(), 'replace')
        
        for line in output.splitlines():
            if line.startswith(" "):
                li = line.strip().split()
                del li[-1]
                name = " ".join(li)
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
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        bookmarks = self.__getInOutBookmarks(repodir, True)
        
        bookmark, ok = QInputDialog.getItem(
            None,
            self.tr("Pull Bookmark"),
            self.tr("Select the bookmark to be pulled:"),
            [""] + sorted(bookmarks),
            0, True)
        if ok and bookmark:
            args = self.vcs.initCommand("pull")
            args.append('--bookmark')
            args.append(bookmark)
            
            dia = HgDialog(self.tr(
                'Pulling bookmark from a remote Mercurial repository'),
                self.vcs)
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
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        bookmarks = self.__getInOutBookmarks(repodir, False)
        
        bookmark, ok = QInputDialog.getItem(
            None,
            self.tr("Push Bookmark"),
            self.tr("Select the bookmark to be push:"),
            [""] + sorted(bookmarks),
            0, True)
        if ok and bookmark:
            args = self.vcs.initCommand("push")
            args.append('--bookmark')
            args.append(bookmark)
            
            dia = HgDialog(self.tr(
                'Pushing bookmark to a remote Mercurial repository'),
                self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
