# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the purge extension interface.
"""

import os

from PyQt4.QtCore import QProcess
from PyQt4.QtGui import QDialog

from ..HgExtension import HgExtension
from ..HgDialog import HgDialog

from .HgPurgeListDialog import HgPurgeListDialog

from UI.DeleteFilesConfirmationDialog import DeleteFilesConfirmationDialog

import Preferences


class Purge(HgExtension):
    """
    Class implementing the purge extension interface.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        super().__init__(vcs)
        
        self.purgeListDialog = None
    
    def shutdown(self):
        """
        Public method used to shutdown the purge interface.
        """
        if self.purgeListDialog is not None:
            self.purgeListDialog.close()
    
    def __getEntries(self, repodir, all):
        """
        Public method to get a list of files/directories being purged.
        
        @param repodir directory name of the repository (string)
        @param all flag indicating to delete all files including ignored ones (boolean)
        @return name of the current patch (string)
        """
        purgeEntries = []
        
        args = []
        args.append("purge")
        args.append("--print")
        if all:
            args.append("--all")
        
        client = self.vcs.getClient()
        if client:
            out, err = client.runcommand(args)
            if out:
                purgeEntries = out.strip().split()
        else:
            ioEncoding = Preferences.getSystem("IOEncoding")
            process = QProcess()
            process.setWorkingDirectory(repodir)
            process.start('hg', args)
            procStarted = process.waitForStarted()
            if procStarted:
                finished = process.waitForFinished(30000)
                if finished and process.exitCode() == 0:
                    purgeEntries = str(
                        process.readAllStandardOutput(),
                        ioEncoding, 'replace').strip().split()
        
        return purgeEntries
    
    def hgPurge(self, name, all=False):
        """
        Public method to purge files and directories not tracked by Mercurial.
        
        @param name file/directory name (string)
        @param all flag indicating to delete all files including ignored ones (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return False
        
        if all:
            title = self.trUtf8("Purge All Files")
            message = self.trUtf8("""Do really want to delete all files not tracked by"""
                                  """ Mercurial (including ignored ones)?""")
        else:
            title = self.trUtf8("Purge Files")
            message = self.trUtf8("""Do really want to delete files not tracked by"""
                                  """ Mercurial?""")
        entries = self.__getEntries(repodir, all)
        dlg = DeleteFilesConfirmationDialog(None, title, message, entries)
        if dlg.exec_() == QDialog.Accepted:
            args = []
            args.append("purge")
            if all:
                args.append("--all")
            args.append("-v")
            
            dia = HgDialog(title, self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
    
    def hgPurgeList(self, name, all=False):
        """
        Public method to list files and directories not tracked by Mercurial.
        
        @param name file/directory name (string)
        @param all flag indicating to list all files including ignored ones (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return False
        
        entries = self.__getEntries(repodir, all)
        self.purgeListDialog = HgPurgeListDialog(entries)
        self.purgeListDialog.show()
