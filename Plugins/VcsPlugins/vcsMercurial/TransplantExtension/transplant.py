# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the transplant extension interface.
"""

import os

from PyQt4.QtCore import QObject
from PyQt4.QtGui import QDialog

from ..HgDialog import HgDialog

from .TransplantDialog import TransplantDialog


class Transplant(QObject):
    """
    Class implementing the transplant extension interface.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        QObject.__init__(self, vcs)
        
        self.vcs = vcs
    
    def shutdown(self):
        """
        Public method used to shutdown the transplant interface.
        """
        pass
    
    def hgTransplant(self, path):
        """
        Public method to transplant changesets from another branch.
        
        @param path directory name of the project (string)
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(path)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return False
        
        res = False
        dlg = TransplantDialog(self.vcs.hgGetBranchesList(repodir))
        if dlg.exec_() == QDialog.Accepted:
            revs, sourceRepo, branch, all, pruneRevs, mergeRevs, log = dlg.getData()
            
            args = []
            args.append("transplant")
            if sourceRepo:
                args.append("--source")
                args.append(sourceRepo)
            if branch:
                args.append("--branch")
                args.append(branch)
                if all:
                    args.append("--all")
            for pruneRev in pruneRevs:
                args.append("--prune")
                args.append(pruneRev)
            for mergeRev in mergeRevs:
                args.append("--merge")
                args.append(mergeRev)
            if log:
                args.append("--log")
            args.extend(revs)
            
            dia = HgDialog(self.trUtf8('Transplant Changesets'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
                self.vcs.checkVCSStatus()
        return res
    
    def hgTransplantContinue(self, path):
        """
        Public method to transplant changesets from another branch.
        
        @param path directory name of the project (string)
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(path)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
        args = []
        args.append("transplant")
        args.append("--continue")
        
        dia = HgDialog(self.trUtf8('Transplant Changesets (Continue'))
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
            res = dia.hasAddOrDelete()
            self.vcs.checkVCSStatus()
        return res
