# -*- coding: utf-8 -*-

# Copyright (c) 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the shelve extension interface.
"""

import os

from PyQt4.QtCore import QDateTime
from PyQt4.QtGui import QDialog

from ..HgExtension import HgExtension
from ..HgDialog import HgDialog


class Shelve(HgExtension):
    """
    Class implementing the shelve extension interface.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        super().__init__(vcs)
    
    def shutdown(self):
        """
        Public method used to shutdown the shelve interface.
        """
    
    def hgShelve(self, name):
        """
        Public method to shelve current changes of files or directories.
        
        @param name directory or file name (string) or list of directory
            or file names (list of string)
        @return flag indicating that the project should be reread (boolean)
        """
        if isinstance(name, list):
            dname = self.vcs.splitPathList(name)[0]
        else:
            dname = self.vcs.splitPath(name)[0]
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        res = False
        from .HgShelveDataDialog import HgShelveDataDialog
        dlg = HgShelveDataDialog()
        if dlg.exec_() == QDialog.Accepted:
            shelveName, dateTime, message, addRemove = dlg.getData()
            
            args = []
            args.append("shelve")
            if shelveName:
                args.append("--name")
                args.append(shelveName)
            if message:
                args.append("--message")
                args.append(message)
            if addRemove:
                args.append("--addRemove")
            if dateTime != QDateTime.currentDateTime():
                args.append("--date")
                args.append(dateTime.toString("yyyy-MM-dd hh:mm:ss"))
            args.append("-v")
            
            if isinstance(name, list):
                self.vcs.addArguments(args, name)
            else:
                args.append(name)
            
            dia = HgDialog(self.tr('Shelve current changes'), self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.hasAddOrDelete()
                self.vcs.checkVCSStatus()
        return res
