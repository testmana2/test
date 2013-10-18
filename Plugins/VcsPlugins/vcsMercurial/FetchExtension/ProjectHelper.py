# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the fetch extension project helper.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

from PyQt4.QtGui import QMenu

from E5Gui.E5Action import E5Action
from E5Gui import E5MessageBox

from ..HgExtensionProjectHelper import HgExtensionProjectHelper

import UI.PixmapCache


class FetchProjectHelper(HgExtensionProjectHelper):
    """
    Class implementing the fetch extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        super(FetchProjectHelper, self).__init__()
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.hgFetchAct = E5Action(self.trUtf8('Fetch changes'),
                UI.PixmapCache.getIcon("vcsUpdate.png"),
                self.trUtf8('Fetch changes'),
                0, 0, self, 'mercurial_fetch')
        self.hgFetchAct.setStatusTip(self.trUtf8(
            'Fetch changes from a remote repository'
        ))
        self.hgFetchAct.setWhatsThis(self.trUtf8(
            """<b>Fetch changes</b>"""
            """<p>This pulls changes from a remote repository into the """
            """local repository. If the pulled changes add a new branch"""
            """ head, the head is automatically merged, and the result of"""
            """ the merge is committed. Otherwise, the working directory"""
            """ is updated to include the new changes.</p>"""
        ))
        self.hgFetchAct.triggered[()].connect(self.__hgFetch)
        self.actions.append(self.hgFetchAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.menuTitle(), mainMenu)
        menu.setIcon(UI.PixmapCache.getIcon("vcsUpdate.png"))
        menu.setTearOffEnabled(True)
        
        menu.addAction(self.hgFetchAct)
        
        return menu
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        @return title of the menu (string)
        """
        return self.trUtf8("Fetch")
    
    def __hgFetch(self):
        """
        Private slot used to fetch changes from a remote repository.
        """
        shouldReopen = self.vcs.getExtensionObject("fetch")\
            .hgFetch(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(None,
                self.trUtf8("Fetch"),
                self.trUtf8("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
