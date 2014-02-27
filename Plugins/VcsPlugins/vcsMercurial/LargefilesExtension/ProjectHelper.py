# -*- coding: utf-8 -*-

# Copyright (c) 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the shelve extension project helper.
"""

from PyQt4.QtGui import QMenu

from E5Gui.E5Action import E5Action

from ..HgExtensionProjectHelper import HgExtensionProjectHelper


class LargefilesProjectHelper(HgExtensionProjectHelper):
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
        self.hgConvertToLargefilesAct = E5Action(
            self.tr('Convert repository to largefiles'),
            self.tr('Convert repository to largefiles...'),
            0, 0, self, 'mercurial_convert_to_largefiles')
        self.hgConvertToLargefilesAct.setStatusTip(self.tr(
            'Convert the repository of the project to a largefiles repository.'
        ))
        self.hgConvertToLargefilesAct.setWhatsThis(self.tr(
            """<b>Convert repository to largefiles</b>"""
            """<p>This converts the repository of the project to a"""
            """ largefiles repository. A new project  is created. The"""
            """ current one is kept as a backup.</p>"""
        ))
        self.hgConvertToLargefilesAct.triggered[()].connect(
            lambda: self.__hgLfconvert("largefiles"))
        self.actions.append(self.hgConvertToLargefilesAct)
        
        self.hgConvertToNormalAct = E5Action(
            self.tr('Convert repository to normal'),
            self.tr('Convert repository to normal...'),
            0, 0, self, 'mercurial_convert_to_normal')
        self.hgConvertToNormalAct.setStatusTip(self.tr(
            'Convert the repository of the project to a normal repository.'
        ))
        self.hgConvertToNormalAct.setWhatsThis(self.tr(
            """<b>Convert repository to normal</b>"""
            """<p>This converts the repository of the project to a"""
            """ normal repository. A new project is created. The current"""
            """ one is kept as a backup.</p>"""
        ))
        self.hgConvertToNormalAct.triggered[()].connect(
            lambda: self.__hgLfconvert("normal"))
        self.actions.append(self.hgConvertToNormalAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.menuTitle(), mainMenu)
        menu.setTearOffEnabled(True)
        
        menu.addAction(self.hgConvertToLargefilesAct)
        menu.addAction(self.hgConvertToNormalAct)
        
        return menu
    
    def menuTitle(self):
        """
        Public method to get the menu title.
        
        @return title of the menu (string)
        """
        return self.tr("Large Files")
    
    def __hgLfconvert(self, direction):
        """
        Private slot to convert the repository format of the current project.
        
        @param direction direction of the conversion (string, one of
            'largefiles' or 'normal')
        """
        assert direction in ["largefiles", "normal"]
        
        self.vcs.getExtensionObject("largefiles").hgLfconvert(
            direction, self.project.getProjectFile())
