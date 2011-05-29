# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the gpg extension project helper.
"""

from PyQt4.QtCore import QObject
from PyQt4.QtGui import QMenu

from E5Gui.E5Action import E5Action

import UI.PixmapCache


class GpgProjectHelper(QObject):
    """
    Class implementing the gpg extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        QObject.__init__(self)
        
        self.actions = []
        
        self.initActions()
    
    def setObjects(self, vcsObject, projectObject):
        """
        Public method to set references to the vcs and project objects.
        
        @param vcsObject reference to the vcs object
        @param projectObject reference to the project object
        """
        self.vcs = vcsObject
        self.project = projectObject
    
    def getActions(self):
        """
        Public method to get a list of all actions.
        
        @return list of all actions (list of E5Action)
        """
        return self.actions[:]
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.hgGpgListAct = E5Action(self.trUtf8('List Signed Changesets'),
                UI.PixmapCache.getIcon("changesetSignList.png"),
                self.trUtf8('List Signed Changesets...'),
                0, 0, self, 'mercurial_gpg_list')
        self.hgGpgListAct.setStatusTip(self.trUtf8(
            'List signed changesets'
        ))
        self.hgGpgListAct.setWhatsThis(self.trUtf8(
            """<b>List Signed Changesets</b>"""
            """<p>This opens a dialog listing all signed changesets.</p>"""
        ))
        self.hgGpgListAct.triggered[()].connect(self.__hgGpgSignatures)
        self.actions.append(self.hgGpgListAct)
        
        self.hgGpgVerifyAct = E5Action(self.trUtf8('Verify Signatures'),
                UI.PixmapCache.getIcon("changesetSignVerify.png"),
                self.trUtf8('Verify Signatures'),
                0, 0, self, 'mercurial_gpg_verify')
        self.hgGpgVerifyAct.setStatusTip(self.trUtf8(
            'Verify all signatures there may be for a particular revision'
        ))
        self.hgGpgVerifyAct.setWhatsThis(self.trUtf8(
            """<b>Verify Signatures</b>"""
            """<p>This verifies all signatures there may be for a particular"""
            """ revision.</p>"""
        ))
        self.hgGpgVerifyAct.triggered[()].connect(self.__hgGpgVerifySignatures)
        self.actions.append(self.hgGpgVerifyAct)
        
        self.hgGpgSignAct = E5Action(self.trUtf8('Sign Revision'),
                UI.PixmapCache.getIcon("changesetSign.png"),
                self.trUtf8('Sign Revision'),
                0, 0, self, 'mercurial_gpg_sign')
        self.hgGpgSignAct.setStatusTip(self.trUtf8(
            'Add a signature for a selected revision'
        ))
        self.hgGpgSignAct.setWhatsThis(self.trUtf8(
            """<b>Sign Revision</b>"""
            """<p>This adds a signature for a selected revision.</p>"""
        ))
        self.hgGpgSignAct.triggered[()].connect(self.__hgGpgSign)
        self.actions.append(self.hgGpgSignAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.menuTitle(), mainMenu)
        menu.setTearOffEnabled(True)
        
        menu.addAction(self.hgGpgListAct)
        menu.addAction(self.hgGpgVerifyAct)
        menu.addAction(self.hgGpgSignAct)
        
        return menu
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        """
        return self.trUtf8("GPG")
    
    def __hgGpgSignatures(self):
        """
        Private slot used to list all signed changesets.
        """
        self.vcs.getExtensionObject("gpg")\
            .hgGpgSignatures(self.project.getProjectPath())
    
    def __hgGpgVerifySignatures(self):
        """
        Private slot used to verify the signatures of a revision.
        """
        self.vcs.getExtensionObject("gpg")\
            .hgGpgVerifySignatures(self.project.getProjectPath())
    
    def __hgGpgSign(self):
        """
        Private slot used to sign a revision.
        """
        self.vcs.getExtensionObject("gpg")\
            .hgGpgSign(self.project.getProjectPath())
