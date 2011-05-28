# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the fetch extension interface.
"""

import os

from PyQt4.QtCore import QObject
from PyQt4.QtGui import QDialog

from ..HgDialog import HgDialog

from .HgFetchDialog import HgFetchDialog


class Fetch(QObject):
    """
    Class implementing the fetch extension interface.
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
        Public method used to shutdown the fetch interface.
        """
        pass
    
    def hgFetch(self, name):
        """
        Public method to fetch changes from a remote repository.
        
        @param name file/directory name (string)
        """
        # find the root of the repo
        repodir = self.vcs.splitPath(name)[0]
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if repodir == os.sep:
                return
        
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
            
            dia = HgDialog(self.trUtf8('Fetching from a remote Mercurial repository'))
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
                self.vcs.checkVCSStatus()
        return res
