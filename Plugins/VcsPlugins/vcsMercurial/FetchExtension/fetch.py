# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the fetch extension interface.
"""

import os

from PyQt4.QtGui import QDialog

from ..HgExtension import HgExtension
from ..HgDialog import HgDialog

from .HgFetchDialog import HgFetchDialog


class Fetch(HgExtension):
    """
    Class implementing the fetch extension interface.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        super().__init__(vcs)
    
    def hgFetch(self, name):
        """
        Public method to fetch changes from a remote repository.
        
        @param name file/directory name (string)
        @return flag indicating that the project should be reread (boolean)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        res = False
        dlg = HgFetchDialog()
        if dlg.exec_() == QDialog.Accepted:
            message, switchParent = dlg.getData()
            
            args = []
            args.append("fetch")
            if message != "":
                args.append("--message")
                args.append(message)
            if switchParent:
                args.append("--switch-parent")
            args.append("-v")
            
            dia = HgDialog(self.trUtf8('Fetching from a remote Mercurial repository'),
                           self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
                self.vcs.checkVCSStatus()
        return res