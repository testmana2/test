# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS project browser helper for Mercurial.
"""

import os

from PyQt4.QtGui import QMenu, QDialog

from Project.ProjectBrowserModel import ProjectBrowserFileItem

from VCS.ProjectBrowserHelper import VcsProjectBrowserHelper

from UI.DeleteFilesConfirmationDialog import DeleteFilesConfirmationDialog
import UI.PixmapCache


class HgProjectBrowserHelper(VcsProjectBrowserHelper):
    """
    Class implementing the VCS project browser helper for Mercurial.
    """
    def __init__(self, vcsObject, browserObject, projectObject, isTranslationsBrowser,
        parent=None, name=None):
        """
        Constructor
        
        @param vcsObject reference to the vcs object
        @param browserObject reference to the project browser object
        @param projectObject reference to the project object
        @param isTranslationsBrowser flag indicating, the helper is requested for the
            translations browser (this needs some special treatment)
        @param parent parent widget (QWidget)
        @param name name of this object (string)
        """
        VcsProjectBrowserHelper.__init__(self, vcsObject, browserObject, projectObject,
            isTranslationsBrowser, parent, name)
    
    def showContextMenu(self, menu, standardItems):
        """
        Slot called before the context menu is shown.
        
        It enables/disables the VCS menu entries depending on the overall
        VCS status and the file status.
        
        @param menu reference to the menu to be shown
        @param standardItems array of standard items that need activation/deactivation
            depending on the overall VCS status
        """
        if self.browser.currentItem().data(1) == self.vcs.vcsName():
            for act in self.vcsMenuActions:
                act.setEnabled(True)
            for act in self.vcsAddMenuActions:
                act.setEnabled(False)
            for act in standardItems:
                act.setEnabled(False)
            if not hasattr(self.browser.currentItem(), 'fileName'):
                self.annotateAct.setEnabled(False)
        else:
            for act in self.vcsMenuActions:
                act.setEnabled(False)
            for act in self.vcsAddMenuActions:
                act.setEnabled(True)
            for act in standardItems:
                act.setEnabled(True)
    
    def showContextMenuMulti(self, menu, standardItems):
        """
        Slot called before the context menu (multiple selections) is shown.
        
        It enables/disables the VCS menu entries depending on the overall
        VCS status and the files status.
        
        @param menu reference to the menu to be shown
        @param standardItems array of standard items that need activation/deactivation
            depending on the overall VCS status
        """
        vcsName = self.vcs.vcsName()
        items = self.browser.getSelectedItems()
        vcsItems = 0
        # determine number of selected items under VCS control
        for itm in items:
            if itm.data(1) == vcsName:
                vcsItems += 1
        
        if vcsItems > 0:
            if vcsItems != len(items):
                for act in self.vcsMultiMenuActions:
                    act.setEnabled(False)
            else:
                for act in self.vcsMultiMenuActions:
                    act.setEnabled(True)
            for act in self.vcsAddMultiMenuActions:
                act.setEnabled(False)
            for act in standardItems:
                act.setEnabled(False)
        else:
            for act in self.vcsMultiMenuActions:
                act.setEnabled(False)
            for act in self.vcsAddMultiMenuActions:
                act.setEnabled(True)
            for act in standardItems:
                act.setEnabled(True)
    
    def showContextMenuDir(self, menu, standardItems):
        """
        Slot called before the context menu is shown.
        
        It enables/disables the VCS menu entries depending on the overall
        VCS status and the directory status.
        
        @param menu reference to the menu to be shown
        @param standardItems array of standard items that need activation/deactivation
            depending on the overall VCS status
        """
        if self.browser.currentItem().data(1) == self.vcs.vcsName():
            for act in self.vcsDirMenuActions:
                act.setEnabled(True)
            for act in self.vcsAddDirMenuActions:
                act.setEnabled(False)
            for act in standardItems:
                act.setEnabled(False)
        else:
            for act in self.vcsDirMenuActions:
                act.setEnabled(False)
            for act in self.vcsAddDirMenuActions:
                act.setEnabled(True)
            for act in standardItems:
                act.setEnabled(True)
    
    def showContextMenuDirMulti(self, menu, standardItems):
        """
        Slot called before the context menu is shown.
        
        It enables/disables the VCS menu entries depending on the overall
        VCS status and the directory status.
        
        @param menu reference to the menu to be shown
        @param standardItems array of standard items that need activation/deactivation
            depending on the overall VCS status
        """
        vcsName = self.vcs.vcsName()
        items = self.browser.getSelectedItems()
        vcsItems = 0
        # determine number of selected items under VCS control
        for itm in items:
            if itm.data(1) == vcsName:
                vcsItems += 1
        
        if vcsItems > 0:
            if vcsItems != len(items):
                for act in self.vcsDirMultiMenuActions:
                    act.setEnabled(False)
            else:
                for act in self.vcsDirMultiMenuActions:
                    act.setEnabled(True)
            for act in self.vcsAddDirMultiMenuActions:
                act.setEnabled(False)
            for act in standardItems:
                act.setEnabled(False)
        else:
            for act in self.vcsDirMultiMenuActions:
                act.setEnabled(False)
            for act in self.vcsAddDirMultiMenuActions:
                act.setEnabled(True)
            for act in standardItems:
                act.setEnabled(True)

    ############################################################################
    # Protected menu generation methods below
    ############################################################################

    def _addVCSMenu(self, mainMenu):
        """
        Protected method used to add the VCS menu to all project browsers.
        
        @param mainMenu reference to the menu to be amended
        """
        self.vcsMenuActions = []
        self.vcsAddMenuActions = []
        
        menu = QMenu(self.trUtf8("Version Control"))
        
        act = menu.addAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons", "mercurial.png")),
            self.vcs.vcsName(), self._VCSInfoDisplay)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addSeparator()
        
        act = menu.addAction(UI.PixmapCache.getIcon("vcsCommit.png"),
            self.trUtf8('Commit changes to repository...'),
            self._VCSCommit)
        self.vcsMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsAdd.png"),
            self.trUtf8('Add to repository'),
            self._VCSAdd)
        self.vcsAddMenuActions.append(act)
        act = menu.addAction(UI.PixmapCache.getIcon("vcsRemove.png"),
            self.trUtf8('Remove from repository (and disk)'),
            self._VCSRemove)
        self.vcsMenuActions.append(act)
        act = menu.addAction(UI.PixmapCache.getIcon("vcsRemove.png"),
            self.trUtf8('Remove from repository only'),
            self.__HgForget)
        self.vcsMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(self.trUtf8('Copy in repository'), self.__HgCopy)
        self.vcsMenuActions.append(act)
        act = menu.addAction(self.trUtf8('Move in repository'), self.__HgMove)
        self.vcsMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsLog.png"),
            self.trUtf8('Show log'), self._VCSLog)
        self.vcsMenuActions.append(act)
        act = menu.addAction(UI.PixmapCache.getIcon("vcsLog.png"),
            self.trUtf8('Show log browser'), self.__HgLogBrowser)
        self.vcsMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsStatus.png"),
            self.trUtf8('Show status'), self._VCSStatus)
        self.vcsMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsDiff.png"),
            self.trUtf8('Show difference'), self._VCSDiff)
        self.vcsMenuActions.append(act)
        act = menu.addAction(UI.PixmapCache.getIcon("vcsDiff.png"),
            self.trUtf8('Show difference (extended)'),
            self.__HgExtendedDiff)
        self.vcsMenuActions.append(act)
        self.annotateAct = menu.addAction(self.trUtf8('Show annotated file'),
            self.__HgAnnotate)
        self.vcsMenuActions.append(self.annotateAct)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsRevert.png"),
            self.trUtf8('Revert changes'), self._VCSRevert)
        self.vcsMenuActions.append(act)
        act = menu.addAction(self.trUtf8('Resolve conflict'), self.__HgResolve)
        self.vcsMenuActions.append(act)
        menu.addSeparator()
        menu.addAction(self.trUtf8('Select all local file entries'),
                        self.browser.selectLocalEntries)
        menu.addAction(self.trUtf8('Select all versioned file entries'),
                        self.browser.selectVCSEntries)
        menu.addAction(self.trUtf8('Select all local directory entries'),
                        self.browser.selectLocalDirEntries)
        menu.addAction(self.trUtf8('Select all versioned directory entries'),
                        self.browser.selectVCSDirEntries)
        menu.addSeparator()
        
        mainMenu.addSeparator()
        mainMenu.addMenu(menu)
        self.menu = menu
    
    def _addVCSMenuMulti(self, mainMenu):
        """
        Protected method used to add the VCS menu for multi selection to all
        project browsers.
        
        @param mainMenu reference to the menu to be amended
        """
        self.vcsMultiMenuActions = []
        self.vcsAddMultiMenuActions = []
        
        menu = QMenu(self.trUtf8("Version Control"))
        
        act = menu.addAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons", "mercurial.png")),
            self.vcs.vcsName(), self._VCSInfoDisplay)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addSeparator()
        
        act = menu.addAction(UI.PixmapCache.getIcon("vcsCommit.png"),
            self.trUtf8('Commit changes to repository...'),
            self._VCSCommit)
        self.vcsMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsAdd.png"),
            self.trUtf8('Add to repository'), self._VCSAdd)
        self.vcsAddMultiMenuActions.append(act)
        act = menu.addAction(UI.PixmapCache.getIcon("vcsRemove.png"),
            self.trUtf8('Remove from repository (and disk)'),
            self._VCSRemove)
        self.vcsMultiMenuActions.append(act)
        act = menu.addAction(UI.PixmapCache.getIcon("vcsRemove.png"),
            self.trUtf8('Remove from repository only'),
            self.__HgForget)
        self.vcsMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsStatus.png"),
            self.trUtf8('Show status'), self._VCSStatus)
        self.vcsMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsDiff.png"),
            self.trUtf8('Show difference'), self._VCSDiff)
        self.vcsMultiMenuActions.append(act)
        act = menu.addAction(UI.PixmapCache.getIcon("vcsDiff.png"),
            self.trUtf8('Show difference (extended)'),
            self.__HgExtendedDiff)
        self.vcsMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsRevert.png"),
            self.trUtf8('Revert changes'), self._VCSRevert)
        self.vcsMultiMenuActions.append(act)
        act = menu.addAction(self.trUtf8('Resolve conflict'), self.__HgResolve)
        self.vcsMultiMenuActions.append(act)
        menu.addSeparator()
        menu.addAction(self.trUtf8('Select all local file entries'),
                        self.browser.selectLocalEntries)
        menu.addAction(self.trUtf8('Select all versioned file entries'),
                        self.browser.selectVCSEntries)
        menu.addAction(self.trUtf8('Select all local directory entries'),
                        self.browser.selectLocalDirEntries)
        menu.addAction(self.trUtf8('Select all versioned directory entries'),
                        self.browser.selectVCSDirEntries)
        menu.addSeparator()
        
        mainMenu.addSeparator()
        mainMenu.addMenu(menu)
        self.menuMulti = menu
    
    def _addVCSMenuBack(self, mainMenu):
        """
        Protected method used to add the VCS menu to all project browsers.
        
        @param mainMenu reference to the menu to be amended
        """
        menu = QMenu(self.trUtf8("Version Control"))
        
        act = menu.addAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons", "mercurial.png")),
            self.vcs.vcsName(), self._VCSInfoDisplay)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addSeparator()
        
        menu.addAction(self.trUtf8('Select all local file entries'),
                        self.browser.selectLocalEntries)
        menu.addAction(self.trUtf8('Select all versioned file entries'),
                        self.browser.selectVCSEntries)
        menu.addAction(self.trUtf8('Select all local directory entries'),
                        self.browser.selectLocalDirEntries)
        menu.addAction(self.trUtf8('Select all versioned directory entries'),
                        self.browser.selectVCSDirEntries)
        menu.addSeparator()
        
        mainMenu.addSeparator()
        mainMenu.addMenu(menu)
        self.menuBack = menu
    
    def _addVCSMenuDir(self, mainMenu):
        """
        Protected method used to add the VCS menu to all project browsers.
        
        @param mainMenu reference to the menu to be amended
        """
        if mainMenu is None:
            return
        
        self.vcsDirMenuActions = []
        self.vcsAddDirMenuActions = []
        
        menu = QMenu(self.trUtf8("Version Control"))
        
        act = menu.addAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons", "mercurial.png")),
            self.vcs.vcsName(), self._VCSInfoDisplay)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addSeparator()
        
        act = menu.addAction(UI.PixmapCache.getIcon("vcsCommit.png"),
            self.trUtf8('Commit changes to repository...'),
            self._VCSCommit)
        self.vcsDirMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsAdd.png"),
            self.trUtf8('Add to repository'), self._VCSAdd)
        self.vcsAddDirMenuActions.append(act)
        act = menu.addAction(UI.PixmapCache.getIcon("vcsRemove.png"),
            self.trUtf8('Remove from repository (and disk)'),
            self._VCSRemove)
        self.vcsDirMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(self.trUtf8('Copy in repository'), self.__HgCopy)
        self.vcsDirMenuActions.append(act)
        act = menu.addAction(self.trUtf8('Move in repository'), self.__HgMove)
        self.vcsDirMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsLog.png"),
            self.trUtf8('Show log'), self._VCSLog)
        self.vcsDirMenuActions.append(act)
        act = menu.addAction(UI.PixmapCache.getIcon("vcsLog.png"),
            self.trUtf8('Show log browser'), self.__HgLogBrowser)
        self.vcsDirMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsStatus.png"),
            self.trUtf8('Show status'), self._VCSStatus)
        self.vcsDirMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsDiff.png"),
            self.trUtf8('Show difference'), self._VCSDiff)
        self.vcsDirMenuActions.append(act)
        act = menu.addAction(UI.PixmapCache.getIcon("vcsDiff.png"),
            self.trUtf8('Show difference (extended)'),
            self.__HgExtendedDiff)
        self.vcsDirMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsRevert.png"),
            self.trUtf8('Revert changes'), self._VCSRevert)
        self.vcsDirMenuActions.append(act)
        act = menu.addAction(self.trUtf8('Resolve conflict'), self.__HgResolve)
        self.vcsDirMenuActions.append(act)
        menu.addSeparator()
        menu.addAction(self.trUtf8('Select all local file entries'),
                        self.browser.selectLocalEntries)
        menu.addAction(self.trUtf8('Select all versioned file entries'),
                        self.browser.selectVCSEntries)
        menu.addAction(self.trUtf8('Select all local directory entries'),
                        self.browser.selectLocalDirEntries)
        menu.addAction(self.trUtf8('Select all versioned directory entries'),
                        self.browser.selectVCSDirEntries)
        menu.addSeparator()
        
        mainMenu.addSeparator()
        mainMenu.addMenu(menu)
        self.menuDir = menu
    
    def _addVCSMenuDirMulti(self, mainMenu):
        """
        Protected method used to add the VCS menu to all project browsers.
        
        @param mainMenu reference to the menu to be amended
        """
        if mainMenu is None:
            return
        
        self.vcsDirMultiMenuActions = []
        self.vcsAddDirMultiMenuActions = []
        
        menu = QMenu(self.trUtf8("Version Control"))
        
        act = menu.addAction(
            UI.PixmapCache.getIcon(
                os.path.join("VcsPlugins", "vcsMercurial", "icons", "mercurial.png")),
            self.vcs.vcsName(), self._VCSInfoDisplay)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        menu.addSeparator()
        
        act = menu.addAction(UI.PixmapCache.getIcon("vcsCommit.png"),
            self.trUtf8('Commit changes to repository...'),
            self._VCSCommit)
        self.vcsDirMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsAdd.png"),
            self.trUtf8('Add to repository'), self._VCSAdd)
        self.vcsAddDirMultiMenuActions.append(act)
        act = menu.addAction(UI.PixmapCache.getIcon("vcsRemove.png"),
            self.trUtf8('Remove from repository (and disk)'),
            self._VCSRemove)
        self.vcsDirMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsStatus.png"),
            self.trUtf8('Show status'), self._VCSStatus)
        self.vcsDirMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsDiff.png"),
            self.trUtf8('Show difference'), self._VCSDiff)
        self.vcsDirMultiMenuActions.append(act)
        act = menu.addAction(UI.PixmapCache.getIcon("vcsDiff.png"),
            self.trUtf8('Show difference (extended)'),
            self.__HgExtendedDiff)
        self.vcsDirMultiMenuActions.append(act)
        menu.addSeparator()
        act = menu.addAction(UI.PixmapCache.getIcon("vcsRevert.png"),
            self.trUtf8('Revert changes'), self._VCSRevert)
        self.vcsDirMultiMenuActions.append(act)
        act = menu.addAction(self.trUtf8('Resolve conflict'), self.__HgResolve)
        self.vcsDirMultiMenuActions.append(act)
        menu.addSeparator()
        menu.addAction(self.trUtf8('Select all local file entries'),
                        self.browser.selectLocalEntries)
        menu.addAction(self.trUtf8('Select all versioned file entries'),
                        self.browser.selectVCSEntries)
        menu.addAction(self.trUtf8('Select all local directory entries'),
                        self.browser.selectLocalDirEntries)
        menu.addAction(self.trUtf8('Select all versioned directory entries'),
                        self.browser.selectVCSDirEntries)
        menu.addSeparator()
        
        mainMenu.addSeparator()
        mainMenu.addMenu(menu)
        self.menuDirMulti = menu
    
    ############################################################################
    # Menu handling methods below
    ############################################################################
    
    def __HgCopy(self):
        """
        Private slot called by the context menu to copy the selected file.
        """
        itm = self.browser.currentItem()
        try:
            fn = itm.fileName()
        except AttributeError:
            fn = itm.dirName()
        self.vcs.hgCopy(fn, self.project)
    
    def __HgMove(self):
        """
        Private slot called by the context menu to move the selected file.
        """
        itm = self.browser.currentItem()
        try:
            fn = itm.fileName()
        except AttributeError:
            fn = itm.dirName()
        isFile = os.path.isfile(fn)
        movefiles = self.browser.project.getFiles(fn)
        if self.vcs.vcsMove(fn, self.project):
            if isFile:
                self.browser.closeSourceWindow.emit(fn)
            else:
                for mf in movefiles:
                    self.browser.closeSourceWindow.emit(mf)
    
    def __HgExtendedDiff(self):
        """
        Private slot called by the context menu to show the difference of a file to
        the repository.
        
        This gives the chance to enter the revisions to compare.
        """
        names = []
        for itm in self.browser.getSelectedItems():
            try:
                names.append(itm.fileName())
            except AttributeError:
                names.append(itm.dirName())
        self.vcs.hgExtendedDiff(names)
    
    def __HgAnnotate(self):
        """
        Private slot called by the context menu to show the annotations of a file.
        """
        itm = self.browser.currentItem()
        fn = itm.fileName()
        self.vcs.hgAnnotate(fn)
    
    def __HgLogBrowser(self):
        """
        Private slot called by the context menu to show the log browser for a file.
        """
        itm = self.browser.currentItem()
        try:
            fn = itm.fileName()
        except AttributeError:
            fn = itm.dirName()
        self.vcs.hgLogBrowser(fn)
    
    def __HgResolve(self):
        """
        Private slot called by the context menu to resolve conflicts of a file.
        """
        names = []
        for itm in self.browser.getSelectedItems():
            try:
                names.append(itm.fileName())
            except AttributeError:
                names.append(itm.dirName())
        self.vcs.hgResolve(names)
        
    def __HgForget(self):
        """
        Private slot called by the context menu to remove the selected file from the
        Mercurial repository leaving a copy in the project directory.
        """
        if self.isTranslationsBrowser:
            items = self.browser.getSelectedItems([ProjectBrowserFileItem])
            names = [itm.fileName() for itm in items]
            
            dlg = DeleteFilesConfirmationDialog(self.parent(),
                self.trUtf8("Remove from repository only"),
                self.trUtf8("Do you really want to remove these translation files from"
                    " the repository?"),
                names)
        else:
            items = self.browser.getSelectedItems()
            names = [itm.fileName() for itm in items]
            files = [self.browser.project.getRelativePath(name) \
                for name in names]
            
            dlg = DeleteFilesConfirmationDialog(self.parent(),
                self.trUtf8("Remove from repository only"),
                self.trUtf8("Do you really want to remove these files"
                    " from the repository?"),
                files)
        
        if dlg.exec_() == QDialog.Accepted:
            self.vcs.hgForget(names)
        
        for fn in names:
            self._updateVCSStatus(fn)
