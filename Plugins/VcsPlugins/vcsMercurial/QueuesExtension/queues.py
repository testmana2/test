# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the queues extension interface.
"""
import os

from PyQt4.QtCore import QObject, QProcess
from PyQt4.QtGui import QDialog, QApplication, QInputDialog

from E5Gui import E5MessageBox

from ..HgDialog import HgDialog
from ..HgDiffDialog import HgDiffDialog

from .HgQueuesNewPatchDialog import HgQueuesNewPatchDialog
from .HgQueuesListDialog import HgQueuesListDialog

import Preferences


class Queues(QObject):
    """
    Class implementing the queues extension interface.
    """
    APPLIED_LIST = 0
    UNAPPLIED_LIST = 1
    SERIES_LIST = 2
    
    def __init__(self, vcs):
        """
        Constructor
        """
        QObject.__init__(self, vcs)
        
        self.vcs = vcs
        
        self.qdiffDialog = None
    
    def shutdown(self):
        """
        Public method used to shutdown the queues interface.
        """
        if self.qdiffDialog is not None:
            self.qdiffDialog.close()
    
    def hgQueueNewPatch(self, name):
        """
        Public method to create a new named patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        dlg = HgQueuesNewPatchDialog()
        if dlg.exec_() == QDialog.Accepted:
            name, message, (userData, currentUser, userName), \
            (dateData, currentDate, dateStr) = dlg.getData()
            
            args = []
            args.append("qnew")
            if message != "":
                args.append("--message")
                args.append(message)
            if userData:
                if currentUser:
                    args.append("--currentuser")
                else:
                    args.append("--user")
                    args.append(userName)
            if dateData:
                if currentDate:
                    args.append("--currentdate")
                else:
                    args.append("--date")
                    args.append(dateStr)
            args.append(name)
            
            dia = HgDialog(self.trUtf8('New Patch'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                self.vcs.checkVCSStatus()
    
    def hgQueueRefreshPatch(self, name):
        """
        Public method to create a new named patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append("qrefresh")
        
        dia = HgDialog(self.trUtf8('Update Current Patch'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            self.vcs.checkVCSStatus()
    
    def hgQueueShowPatch(self, name):
        """
        Public method to create a new named patch.
        
        @param name file/directory name (string)
        """
        self.qdiffDialog = HgDiffDialog(self.vcs)
        self.qdiffDialog.show()
        QApplication.processEvents()
        self.qdiffDialog.start(name, qdiff=True)
    
    def hgQueuePushPopPatches(self, name, pop=False, all=False, named=False, force=False):
        """
        Public method to push patches onto the stack or pop patches off the stack.
        
        @param name file/directory name (string)
        @keyparam pop flag indicating a pop action (boolean)
        @keyparam all flag indicating to push/pop all (boolean)
        @keyparam named flag indicating to push/pop until a named patch
            is at the top of the stack (boolean)
        @keyparam force flag indicating a forceful pop (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        if pop:
            args.append("qpop")
            title = self.trUtf8("Pop Patches")
            listType = Queues.APPLIED_LIST
        else:
            args.append("qpush")
            title = self.trUtf8("Push Patches")
            listType = Queues.UNAPPLIED_LIST
        if force:
            args.append("--force")
        if all:
            args.append("--all")
        elif named:
            patchnames = self.__getUnAppliedPatches(repodir, listType)
            if patchnames:
                patch, ok = QInputDialog.getItem(
                    None,
                    self.trUtf8("Select Patch"),
                    self.trUtf8("Select the target patch name:"),
                    patchnames,
                    0, False)
                if ok and patch:
                    args.append(patch)
                else:
                    return
            else:
                E5MessageBox.information(None,
                    self.trUtf8("Select Patch"),
                    self.trUtf8("""No patches to select from."""))
                return
        
        dia = HgDialog(title)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            self.vcs.checkVCSStatus()
    
    def __getUnAppliedPatches(self, repodir, listType):
        """
        Public method to get the list of applied or unapplied patches.
        
        @param repodir directory name of the repository (string)
        @param listType type of patcheslist to get
            (Queues.APPLIED_LIST, Queues.UNAPPLIED_LIST, Queues.SERIES_LIST)
        @return list of patches (list of string)
        """
        patchesList = []
        
        ioEncoding = Preferences.getSystem("IOEncoding")
        process = QProcess()
        args = []
        if listType == Queues.APPLIED_LIST:
            args.append("qapplied")
        elif listType == Queues.UNAPPLIED_LIST:
            args.append("qunapplied")
        elif listType == Queues.SERIES_LIST:
            args.append("qseries")
        else:
            raise ValueError("Illegal value for listType.")
        
        process.setWorkingDirectory(repodir)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                output = \
                    str(process.readAllStandardOutput(), ioEncoding, 'replace')
                for line in output.splitlines():
                    patchesList.append(line.strip())
        
        return patchesList
    
    def hgQueueListPatches(self, name):
        """
        Public method to create a new named patch.
        
        @param name file/directory name (string)
        """
        self.queuesListDialog = HgQueuesListDialog(self.vcs)
        self.queuesListDialog.show()
        self.queuesListDialog.start(name)
    
    def hgQueueFinishAppliedPatches(self, name):
        """
        Public method to create a new named patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append("qfinish")
        args.append("--applied")
        
        dia = HgDialog(self.trUtf8('Finish Applied Patches'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            self.vcs.checkVCSStatus()
