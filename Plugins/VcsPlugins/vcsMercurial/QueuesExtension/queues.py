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
from .HgQueuesListGuardsDialog import HgQueuesListGuardsDialog
from .HgQueuesListAllGuardsDialog import HgQueuesListAllGuardsDialog
from .HgQueuesDefineGuardsDialog import HgQueuesDefineGuardsDialog
from .HgQueuesGuardsSelectionDialog import HgQueuesGuardsSelectionDialog
from .HgQueuesQueueManagementDialog import HgQueuesQueueManagementDialog

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
    
    QUEUE_DELETE = 0
    QUEUE_PURGE = 1
    QUEUE_ACTIVATE = 2
    
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        QObject.__init__(self, vcs)
        
        self.vcs = vcs
        
        self.qdiffDialog = None
        self.qheaderDialog = None
        self.queuesListDialog = None
        self.queuesListGuardsDialog = None
        self.queuesListAllGuardsDialog = None
        self.queuesDefineGuardsDialog = None
        self.queuesListQueuesDialog = None
    
    def shutdown(self):
        """
        Public method used to shutdown the queues interface.
        """
        if self.qdiffDialog is not None:
            self.qdiffDialog.close()
        if self.qheaderDialog is not None:
            self.qheaderDialog.close()
        if self.queuesListDialog is not None:
            self.queuesListDialog.close()
        if self.queuesListGuardsDialog is not None:
            self.queuesListGuardsDialog.close()
        if self.queuesListAllGuardsDialog is not None:
            self.queuesListAllGuardsDialog.close()
        if self.queuesDefineGuardsDialog is not None:
            self.queuesDefineGuardsDialog.close()
        if self.queuesListQueuesDialog is not None:
            self.queuesListQueuesDialog.close()
    
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
    
    def getGuardsList(self, repodir, all=True):
        """
        Public method to get a list of all guards defined.
        
        @param repodir directory name of the repository (string)
        @param all flag indicating to get all guards (boolean)
        @return sorted list of guards (list of strings)
        """
        guardsList = []
        
        ioEncoding = Preferences.getSystem("IOEncoding")
        process = QProcess()
        args = []
        args.append("qselect")
        if all:
            args.append("--series")
        
        process.setWorkingDirectory(repodir)
        process.start('hg', args)
        procStarted = process.waitForStarted()
        if procStarted:
            finished = process.waitForFinished(30000)
            if finished and process.exitCode() == 0:
                output = \
                    str(process.readAllStandardOutput(), ioEncoding, 'replace')
                for guard in output.splitlines():
                    guard = guard.strip()
                    if all:
                        guard = guard[1:]
                    if guard not in guardsList:
                        guardsList.append(guard)
        
        return sorted(guardsList)
    
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
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return False
        
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
        args.append("-v")
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
                    return False
            else:
                E5MessageBox.information(None,
                    self.trUtf8("Select Patch"),
                    self.trUtf8("""No patches to select from."""))
                return False
        
        dia = HgDialog(title)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            res = dia.hasAddOrDelete()
            self.vcs.checkVCSStatus()
        return res
    
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
    
    def hgQueueGuardsList(self, name):
        """
        Public method to list the guards for the current or a named patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        patchnames = sorted(
            self.__getPatchesList(repodir, Queues.SERIES_LIST))
        if patchnames:
            self.queuesListGuardsDialog = HgQueuesListGuardsDialog(self.vcs, patchnames)
            self.queuesListGuardsDialog.show()
            self.queuesListGuardsDialog.start(name)
        else:
            E5MessageBox.information(None,
                self.trUtf8("List Guards"),
                self.trUtf8("""No patches available to list guards for."""))
    
    def hgQueueGuardsListAll(self, name):
        """
        Public method to list all guards of all patches.
        
        @param name file/directory name (string)
        """
        self.queuesListAllGuardsDialog = HgQueuesListAllGuardsDialog(self.vcs)
        self.queuesListAllGuardsDialog.show()
        self.queuesListAllGuardsDialog.start(name)
    
    def hgQueueGuardsDefine(self, name):
        """
        Public method to define guards for the current or a named patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        patchnames = sorted(
            self.__getPatchesList(repodir, Queues.SERIES_LIST))
        if patchnames:
            self.queuesDefineGuardsDialog = HgQueuesDefineGuardsDialog(
                self.vcs, self, patchnames)
            self.queuesDefineGuardsDialog.show()
            self.queuesDefineGuardsDialog.start(name)
        else:
            E5MessageBox.information(None,
                self.trUtf8("Define Guards"),
                self.trUtf8("""No patches available to define guards for."""))
    
    def hgQueueGuardsDropAll(self, name):
        """
        Public method to drop all guards of the current or a named patch.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        patchnames = sorted(
            self.__getPatchesList(repodir, Queues.SERIES_LIST))
        if patchnames:
            patch, ok = QInputDialog.getItem(
                None,
                self.trUtf8("Drop All Guards"),
                self.trUtf8("Select the patch to drop guards for"
                            " (leave empty for the current patch):"),
                [""] + patchnames,
                0, False)
            if ok:
                process = QProcess()
                args = []
                args.append("qguard")
                if patch:
                    args.append(patch)
                args.append("--none")
                
                process.setWorkingDirectory(repodir)
                process.start('hg', args)
                procStarted = process.waitForStarted()
                if procStarted:
                    process.waitForFinished(30000)
        else:
            E5MessageBox.information(None,
                self.trUtf8("Drop All Guards"),
                self.trUtf8("""No patches available to define guards for."""))
    
    def hgQueueGuardsSetActive(self, name):
        """
        Public method to set the active guards.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        guardsList = self.getGuardsList(repodir)
        if guardsList:
            activeGuardsList = self.getGuardsList(repodir, all=False)
            dlg = HgQueuesGuardsSelectionDialog(
                guardsList, activeGuards=activeGuardsList, listOnly=False)
            if dlg.exec_() == QDialog.Accepted:
                guards = dlg.getData()
                if guards:
                    args = []
                    args.append("qselect")
                    args.extend(guards)
                    
                    dia = HgDialog(self.trUtf8('Set Active Guards'))
                    res = dia.startProcess(args, repodir)
                    if res:
                        dia.exec_()
        else:
            E5MessageBox.information(None,
                self.trUtf8("Set Active Guards"),
                self.trUtf8("""No guards available to select from."""))
            return
    
    def hgQueueGuardsDeactivate(self, name):
        """
        Public method to deactivate all active guards.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append("qselect")
        args.append("--none")
        
        dia = HgDialog(self.trUtf8('Deactivate Guards'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
    
    def hgQueueGuardsIdentifyActive(self, name):
        """
        Public method to list all active guards.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        guardsList = self.getGuardsList(repodir, all=False)
        if guardsList:
            dlg = HgQueuesGuardsSelectionDialog(guardsList, listOnly=True)
            dlg.exec_()
    
    def hgQueueCreateRenameQueue(self, name, isCreate):
        """
        Public method to create a new queue or rename the active queue.
        
        @param name file/directory name (string)
        @param isCreate flag indicating to create a new queue (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        if isCreate:
            title = self.trUtf8("Create New Queue")
        else:
            title = self.trUtf8("Rename Active Queue")
        dlg = HgQueuesQueueManagementDialog(HgQueuesQueueManagementDialog.NAME_INPUT,
            title, False, repodir)
        if dlg.exec_() == QDialog.Accepted:
            queueName = dlg.getData()
            if queueName:
                ioEncoding = Preferences.getSystem("IOEncoding")
                process = QProcess()
                args = []
                args.append("qqueue")
                if isCreate:
                    args.append("--create")
                else:
                    args.append("--rename")
                args.append(queueName)
                
                process.setWorkingDirectory(repodir)
                process.start('hg', args)
                procStarted = process.waitForStarted()
                if procStarted:
                    finished = process.waitForFinished(30000)
                    if finished:
                        if process.exitCode() != 0:
                            error = \
                                str(process.readAllStandardError(), ioEncoding, 'replace')
                            if isCreate:
                                errMsg = self.trUtf8(
                                    "Error while creating a new queue.")
                            else:
                                errMsg = self.trUtf8(
                                    "Error while renaming the active queue.")
                            E5MessageBox.warning(None,
                                title,
                                """<p>{0}</p><p>{1}</p>""".format(errMsg, error))
                        else:
                            if self.queuesListQueuesDialog is not None and \
                               self.queuesListQueuesDialog.isVisible():
                                self.queuesListQueuesDialog.refresh()
    
    def hgQueueDeletePurgeActivateQueue(self, name, operation):
        """
        Public method to delete the reference to a queue and optionally
        remove the patch directory or set the active queue.
        
        @param name file/directory name (string)
        @param operation operation to be performed (Queues.QUEUE_DELETE,
            Queues.QUEUE_PURGE, Queues.QUEUE_ACTIVATE)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        if operation == Queues.QUEUE_PURGE:
            title = self.trUtf8("Purge Queue")
        elif operation == Queues.QUEUE_DELETE:
            title = self.trUtf8("Delete Queue")
        elif operation == Queues.QUEUE_ACTIVATE:
            title = self.trUtf8("Activate Queue")
        else:
            raise ValueError("illegal value for operation")
        
        dlg = HgQueuesQueueManagementDialog(HgQueuesQueueManagementDialog.QUEUE_INPUT,
            title, True, repodir)
        if dlg.exec_() == QDialog.Accepted:
            queueName = dlg.getData()
            if queueName:
                ioEncoding = Preferences.getSystem("IOEncoding")
                process = QProcess()
                args = []
                args.append("qqueue")
                if operation == Queues.QUEUE_PURGE:
                    args.append("--purge")
                elif operation == Queues.QUEUE_DELETE:
                    args.append("--delete")
                args.append(queueName)
                
                process.setWorkingDirectory(repodir)
                process.start('hg', args)
                procStarted = process.waitForStarted()
                if procStarted:
                    finished = process.waitForFinished(30000)
                    if finished:
                        if process.exitCode() != 0:
                            error = \
                                str(process.readAllStandardError(), ioEncoding, 'replace')
                            if operation == Queues.QUEUE_PURGE:
                                errMsg = self.trUtf8("Error while purging the queue.")
                            elif operation == Queues.QUEUE_DELETE:
                                errMsg = self.trUtf8("Error while deleting the queue.")
                            elif operation == Queues.QUEUE_ACTIVATE:
                                errMsg = self.trUtf8(
                                    "Error while setting the active queue.")
                            E5MessageBox.warning(None,
                                title,
                                """<p>{0}</p><p>{1}</p>""".format(errMsg, error))
                        else:
                            if self.queuesListQueuesDialog is not None and \
                               self.queuesListQueuesDialog.isVisible():
                                self.queuesListQueuesDialog.refresh()
    
    def hgQueueListQueues(self, name):
        """
        Public method to list available queues.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        self.queuesListQueuesDialog = HgQueuesQueueManagementDialog(
            HgQueuesQueueManagementDialog.NO_INPUT,
            self.trUtf8("Available Queues"),
            False, repodir)
        self.queuesListQueuesDialog.show()