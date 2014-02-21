# -*- coding: utf-8 -*-

# Copyright (c) 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the shelve extension project helper.
"""

from PyQt4.QtGui import QMenu

from E5Gui.E5Action import E5Action
from E5Gui import E5MessageBox

from ..HgExtensionProjectHelper import HgExtensionProjectHelper


class ShelveProjectHelper(HgExtensionProjectHelper):
    """
    Class implementing the queues extension project helper.
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__()
    
    def initActions(self):
        """
        Public method to generate the action objects.
        """
        self.hgShelveAct = E5Action(
            self.tr('Shelve changes'),
            self.tr('Shelve changes...'),
            0, 0, self, 'mercurial_shelve')
        self.hgShelveAct.setStatusTip(self.tr(
            'Shelve all current changes of the project'
        ))
        self.hgShelveAct.setWhatsThis(self.tr(
            """<b>Shelve changes</b>"""
            """<p>This shelves all current changes of the project.</p>"""
        ))
        self.hgShelveAct.triggered[()].connect(self.__hgShelve)
        self.actions.append(self.hgShelveAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.menuTitle(), mainMenu)
        menu.setTearOffEnabled(True)
        
        menu.addAction(self.hgShelveAct)
        
        return menu
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        @return title of the menu (string)
        """
        return self.tr("Shelve")
    
    def __hgShelve(self):
        """
        Private slot used to shelve all current changes.
        """
        shouldReopen = self.vcs.getExtensionObject("shelve")\
            .hgShelve(self.project.getProjectPath())
        if shouldReopen:
            res = E5MessageBox.yesNo(
                None,
                self.tr("Shelve"),
                self.tr("""The project should be reread. Do this now?"""),
                yesDefault=True)
            if res:
                self.project.reopenProject()
