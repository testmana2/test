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
from .HgQueuesRenamePatchDialog import HgQueuesRenamePatchDialog
from .HgQueuesFoldDialog import HgQueuesFoldDialog
from .HgQueuesHeaderDialog import HgQueuesHeaderDialog

import Preferences


class Queues(QObject):
    """
    Class implementing the queues extension interface.
    """
    APPLIED_LIST = 0
    UNAPPLIED_LIST = 1
    SERIES_LIST = 2
    
    POP = 0
    PUSH = 1
    GOTO = 2
    
    def __init__(self, vcs):
        """
        Constructor
        """
        QObject.__init__(self, vcs)
        
        self.vcs = vcs
        
        self.qdiffDialog = None
        self.qheaderDialog = None
    
    def shutdown(self):
        """
        Public method used to shutdown the queues interface.
        """
        if self.qdiffDialog is not None:
            self.qdiffDialog.close()
        if self.qheaderDialog is not None:
            self.qheaderDialog.close()
    
    def __getPatchesList(self, repodir, listType, withSummary=False):
        """
        Public method to get a list of patches of a given type.
        
        @param repodir directory name of the repository (string)
        @param listType type of patches list to get
            (Queues.APPLIED_LIST, Queues.UNAPPLIED_LIST, Queues.SERIES_LIST)
        @param withSummary flag indicating to get a summary as well (boolean)
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
            raise ValueError("illegal value for listType")
        if withSummary:
            args.append("--summary")
        
        process.setWorkingDirectory(repodir)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                output = \
                    str(process.readAllStandardOutput(), ioEncoding, 'replace')
                for line in output.splitlines():
                    if withSummary:
                        l = line.strip().split(": ")
                        if len(l) == 1:
                            patch, summary = l[0][:-1], ""
                        else:
                            patch, summary = l[0], l[1]
                        patchesList.append("{0}@@{1}".format(patch, summary))
                    else:
                        patchesList.append(line.strip())
        
        return patchesList
    
    def __getCurrentPatch(self, repodir):
        """
        Public method to get the name of the current patch.
        
        @param repodir directory name of the repository (string)
        @return name of the current patch (string)
        """
        currentPatch = ""
        
        ioEncoding = Preferences.getSystem("IOEncoding")
        process = QProcess()
        args = []
        args.append("qtop")
        
        process.setWorkingDirectory(repodir)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                currentPatch = str(
                    process.readAllStandardOutput(),
                    ioEncoding, 'replace').strip()
        
        return currentPatch
    
    def __getCommitMessage(self, repodir):
        """
        Public method to get the commit message of the current patch.
        
        @param repodir directory name of the repository (string)
        @return name of the current patch (string)
        """
        message = ""
        
        ioEncoding = Preferences.getSystem("IOEncoding")
        process = QProcess()
        args = []
        args.append("qheader")
        
        process.setWorkingDirectory(repodir)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                message = str(
                    process.readAllStandardOutput(),
                    ioEncoding, 'replace')
        
        return message
    
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
        
        dlg = HgQueuesNewPatchDialog(HgQueuesNewPatchDialog.NEW_MODE)
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
    
    def hgQueueRefreshPatch(self, name, editMessage=False):
        """
        Public method to refresh the current patch.
        
        @param name file/directory name (string)
        @param editMessage flag indicating to edit the current
            commit message (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append("qrefresh")
        
        if editMessage:
            currentMessage = self.__getCommitMessage(repodir)
            dlg = HgQueuesNewPatchDialog(HgQueuesNewPatchDialog.REFRESH_MODE,
                                         currentMessage)
            if dlg.exec_() == QDialog.Accepted:
                name, message, (userData, currentUser, userName), \
                (dateData, currentDate, dateStr) = dlg.getData()
                if message != "" and message != currentMessage:
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
            else:
                return
        
        dia = HgDialog(self.trUtf8('Update Current Patch'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            self.vcs.checkVCSStatus()
    
    def hgQueueShowPatch(self, name):
        """
        Public method to show the contents of the current patch.
        
        @param name file/directory name (string)
        """
        self.qdiffDialog = HgDiffDialog(self.vcs)
        self.qdiffDialog.show()
        QApplication.processEvents()
        self.qdiffDialog.start(name, qdiff=True)
    
    def hgQueueShowHeader(self, name):
        """
        Public method to show the commit message of the current patch.
        
        @param name file/directory name (string)
        """
        self.qheaderDialog = HgQueuesHeaderDialog(self.vcs)
        self.qheaderDialog.show()
        QApplication.processEvents()
        self.qheaderDialog.start(name)
    
    def hgQueuePushPopPatches(self, name, operation, all=False, named=False, force=False):
        """
        Public method to push patches onto the stack or pop patches off the stack.
        
        @param name file/directory name (string)
        @param operation operation type to be performed (Queues.POP,
            Queues.PUSH, Queues.GOTO)
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
        if operation == Queues.POP:
            args.append("qpop")
            title = self.trUtf8("Pop Patches")
            listType = Queues.APPLIED_LIST
        elif operation == Queues.PUSH:
            args.append("qpush")
            title = self.trUtf8("Push Patches")
            listType = Queues.UNAPPLIED_LIST
        elif operation == Queues.GOTO:
            args.append("qgoto")
            title = self.trUtf8("Go to Patch")
            listType = Queues.SERIES_LIST
        else:
            raise ValueError("illegal value for operation")
        if force:
            args.append("--force")
        if all and operation in (Queues.POP, Queues.PUSH):
            args.append("--all")
        elif named or operation == Queues.GOTO:
            patchnames = self.__getPatchesList(repodir, listType)
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
    
    def hgQueueListPatches(self, name):
        """
        Public method to show a list of all patches.
        
        @param name file/directory name (string)
        """
        self.queuesListDialog = HgQueuesListDialog(self.vcs)
        self.queuesListDialog.show()
        self.queuesListDialog.start(name)
    
    def hgQueueFinishAppliedPatches(self, name):
        """
        Public method to finish all applied patches.
        
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
    
    def hgQueueRenamePatch(self, name):
        """
        Public method to rename the current or a selected patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append("qrename")
        patchnames = sorted(self.__getPatchesList(repodir, Queues.SERIES_LIST))
        if patchnames:
            currentPatch = self.__getCurrentPatch(repodir)
            if currentPatch:
                dlg = HgQueuesRenamePatchDialog(currentPatch, patchnames)
                if dlg.exec_() == QDialog.Accepted:
                    newName, selectedPatch = dlg.getData()
                    if selectedPatch:
                        args.append(selectedPatch)
                    args.append(newName)
                    
                    dia = HgDialog(self.trUtf8("Rename Patch"))
                    res = dia.startProcess(args, repodir)
                    if res:
                        dia.exec_()
    
    def hgQueueDeletePatch(self, name):
        """
        Public method to delete a selected unapplied patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append("qdelete")
        patchnames = sorted(self.__getPatchesList(repodir, Queues.UNAPPLIED_LIST))
        if patchnames:
            patch, ok = QInputDialog.getItem(
                None,
                self.trUtf8("Select Patch"),
                self.trUtf8("Select the patch to be deleted:"),
                patchnames,
                0, False)
            if ok and patch:
                args.append(patch)
                
                dia = HgDialog(self.trUtf8("Delete Patch"))
                res = dia.startProcess(args, repodir)
                if res:
                    dia.exec_()
        else:
            E5MessageBox.information(None,
                self.trUtf8("Select Patch"),
                self.trUtf8("""No patches to select from."""))
    
    def hgQueueFoldUnappliedPatches(self, name):
        """
        Public method to fold patches into the current patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append("qfold")
        patchnames = sorted(
            self.__getPatchesList(repodir, Queues.UNAPPLIED_LIST, withSummary=True))
        if patchnames:
            dlg = HgQueuesFoldDialog(patchnames)
            if dlg.exec_() == QDialog.Accepted:
                message, patchesList = dlg.getData()
                if message:
                    args.append("--message")
                    args.append(message)
                if patchesList:
                    args.extend(patchesList)
                    
                    dia = HgDialog(self.trUtf8("Fold Patches"))
                    res = dia.startProcess(args, repodir)
                    if res:
                        dia.exec_()
                else:
                    E5MessageBox.information(None,
                        self.trUtf8("Fold Patches"),
                        self.trUtf8("""No patches selected."""))
        else:
            E5MessageBox.information(None,
                self.trUtf8("Fold Patches"),
                self.trUtf8("""No patches available to be folded."""))
