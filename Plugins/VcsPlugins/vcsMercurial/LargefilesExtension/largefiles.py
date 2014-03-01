# -*- coding: utf-8 -*-

# Copyright (c) 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the largefiles extension interface.
"""

import os

from PyQt4.QtGui import QDialog

from E5Gui.E5Application import e5App

from ..HgExtension import HgExtension
from ..HgDialog import HgDialog


class Largefiles(HgExtension):
    """
    Class implementing the largefiles extension interface.
    """
    def __init__(self, vcs):
        """
        Constructor
        
        @param vcs reference to the Mercurial vcs object
        """
        super().__init__(vcs)
    
    def hgLfconvert(self, direction, projectFile):
        """
        Public slot to convert the repository format of the current project.
        
        @param direction direction of the conversion (string, one of
            'largefiles' or 'normal')
        @param projectFile file name of the current project file (string)
        """
        assert direction in ["largefiles", "normal"]
        
        projectDir = os.path.dirname(projectFile)
        
        # find the root of the repo
        repodir = projectDir
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return False
        
        from .LfConvertDataDialog import LfConvertDataDialog
        dlg = LfConvertDataDialog(projectDir, direction)
        if dlg.exec_() == QDialog.Accepted:
            newName, minSize, patterns = dlg.getData()
            newProjectFile = os.path.join(
                newName, os.path.basename(projectFile))
            
            # step 1: convert the current project to new project
            args = self.vcs.initCommand("lfconvert")
            if direction == 'normal':
                args.append('--to-normal')
            else:
                args.append("--size")
                args.append(str(minSize))
            args.append(projectDir)
            args.append(newName)
            if direction == 'largefiles' and patterns:
                args.extend(patterns)
            
            dia = HgDialog(self.tr('Convert Project - Converting'), self.vcs)
            res = dia.startProcess(args, repodir)
            if res:
                dia.exec_()
                res = dia.normalExit() and os.path.isdir(
                    os.path.join(newName, self.vcs.adminDir))
            
            # step 2: create working directory contents
            if res:
                args = self.vcs.initCommand("update")
                args.append("--verbose")
                dia = HgDialog(self.tr('Convert Project - Extracting'),
                               self.vcs, useClient=False)
                res = dia.startProcess(args, newName)
                if res:
                    dia.exec_()
                    res = dia.normalExit() and os.path.isfile(newProjectFile)
            
            # step 3: close current project and open new one
            if res:
                e5App().getObject("Project").openProject(newProjectFile)
                if direction == 'largefiles':
                    self.vcs.hgEditConfig(newName, largefilesData={
                        "minsize": minSize, "pattern": patterns})
                else:
                    self.vcs.hgEditConfig(newName, withLargefiles=False)
    
    def hgAdd(self, names, mode):
        """
        Public method used to add a file to the Mercurial repository.
        
        @param name file name(s) to be added (string or list of string)
        @param mode add mode (string one of 'normal' or 'large')
        """
        args = self.vcs.initCommand("add")
        args.append("-v")
        if mode == "large":
            args.append("--large")
        else:
            args.append("--normal")
        
        if isinstance(names, list):
            dname = self.vcs.splitPathList(names)[0]
        else:
            dname = self.vcs.splitPath(names)[0]
        
        # find the root of the repo
        repodir = dname
        while not os.path.isdir(os.path.join(repodir, self.vcs.adminDir)):
            repodir = os.path.dirname(repodir)
            if os.path.splitdrive(repodir)[1] == os.sep:
                return
        
        if isinstance(names, list):
            self.vcs.addArguments(args, names)
        else:
            args.append(names)
        
        dia = HgDialog(
            self.tr('Adding files to the Mercurial repository'),
            self.vcs)
        res = dia.startProcess(args, repodir)
        if res:
            dia.exec_()
