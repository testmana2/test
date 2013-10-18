# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the rebase extension project helper.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

from PyQt4.QtGui import QMenu

from E5Gui.E5Action import E5Action
from E5Gui import E5MessageBox

from ..HgExtensionProjectHelper import HgExtensionProjectHelper

import UI.PixmapCache


class RebaseProjectHelper(HgExtensionProjectHelper):
    """
    Class implementing the rebase extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        super(RebaseProjectHelper, self).__init__()
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.hgRebaseAct = E5Action(self.trUtf8('Rebase Changesets'),
                UI.PixmapCache.getIcon("vcsRebase.png"),
                self.trUtf8('Rebase Changesets'),
                0, 0, self, 'mercurial_rebase')
        self.hgRebaseAct.setStatusTip(self.trUtf8(
            'Rebase changesets to another branch'
        ))
        self.hgRebaseAct.setWhatsThis(self.trUtf8(
            """<b>Rebase Changesets</b>"""
            """<p>This rebases changesets to another branch.</p>"""
        ))
        self.hgRebaseAct.triggered[()].connect(self.__hgRebase)
        self.actions.append(self.hgRebaseAct)
        
        self.hgRebaseContinueAct = E5Action(
                self.trUtf8('Continue Rebase Session'),
                self.trUtf8('Continue Rebase Session'),
                0, 0, self, 'mercurial_rebase_continue')
        self.hgRebaseContinueAct.setStatusTip(self.trUtf8(
            'Continue the last rebase session after repair'
        ))
        self.hgRebaseContinueAct.setWhatsThis(self.trUtf8(
            """<b>Continue Rebase Session</b>"""
            """<p>This continues the last rebase session after repair.</p>"""
        ))
        self.hgRebaseContinueAct.triggered[()].connect(self.__hgRebaseContinue)
        self.actions.append(self.hgRebaseContinueAct)
        
        self.hgRebaseAbortAct = E5Action(
                self.trUtf8('Abort Rebase Session'),
                self.trUtf8('Abort Rebase Session'),
                0, 0, self, 'mercurial_rebase_abort')
        self.hgRebaseAbortAct.setStatusTip(self.trUtf8(
            'Abort the last rebase session'
        ))
        self.hgRebaseAbortAct.setWhatsThis(self.trUtf8(
            """<b>Abort Rebase Session</b>"""
            """<p>This aborts the last rebase session.</p>"""
        ))
        self.hgRebaseAbortAct.triggered[()].connect(self.__hgRebaseAbort)
        self.actions.append(self.hgRebaseAbortAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.menuTitle(), mainMenu)
        menu.setIcon(UI.PixmapCache.getIcon("vcsRebase.png"))
        menu.setTearOffEnabled(True)
        
        menu.addAction(self.hgRebaseAct)
        menu.addAction(self.hgRebaseContinueAct)
        menu.addAction(self.hgRebaseAbortAct)
        
        return menu
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        @return title of the menu (string)
        """
        return self.trUtf8("Rebase")
    
    def __hgRebase(self):
        """
        Private slot used to rebase changesets to another branch.
        """
        shouldReopen = self.vcs.getExtensionObject("rebase")\
            .hgRebase(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(None,
                self.trUtf8("Rebase Changesets"),
                self.trUtf8("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgRebaseContinue(self):
        """
        Private slot used to continue the last rebase session after repair.
        """
        shouldReopen = self.vcs.getExtensionObject("rebase")\
            .hgRebaseContinue(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(None,
                self.trUtf8("Rebase Changesets (Continue)"),
                self.trUtf8("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
    
    def __hgRebaseAbort(self):
        """
        Private slot used to abort the last rebase session.
        """
        shouldReopen = self.vcs.getExtensionObject("rebase")\
            .hgRebaseAbort(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(None,
                self.trUtf8("Rebase Changesets (Abort)"),
                self.trUtf8("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
