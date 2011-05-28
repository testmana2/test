# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the purge extension project helper.
"""

from PyQt4.QtCore import QObject
from PyQt4.QtGui import QMenu

from E5Gui.E5Action import E5Action

import UI.PixmapCache


class PurgeProjectHelper(QObject):
    """
    Class implementing the purge extension project helper.
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
        self.hgPurgeAct = E5Action(self.trUtf8('Purge Files'),
                UI.PixmapCache.getIcon("fileDelete.png"),
                self.trUtf8('Purge Files'),
                0, 0, self, 'mercurial_purge')
        self.hgPurgeAct.setStatusTip(self.trUtf8(
            'Delete files and directories not known to Mercurial'
        ))
        self.hgPurgeAct.setWhatsThis(self.trUtf8(
            """<b>Purge Files</b>"""
            """<p>This deletes files and directories not known to Mercurial."""
            """ That means that purge will delete:<ul>"""
            """<li>unknown files (marked with "not tracked" in the status dialog)</li>"""
            """<li>empty directories</li>"""
            """</ul>Note that ignored files will be left untouched.</p>"""
        ))
        self.hgPurgeAct.triggered[()].connect(self.__hgPurge)
        self.actions.append(self.hgPurgeAct)
        
        self.hgPurgeAllAct = E5Action(self.trUtf8('Purge All Files'),
                self.trUtf8('Purge All Files'),
                0, 0, self, 'mercurial_purge_all')
        self.hgPurgeAllAct.setStatusTip(self.trUtf8(
            'Delete files and directories not known to Mercurial including ignored ones'
        ))
        self.hgPurgeAllAct.setWhatsThis(self.trUtf8(
            """<b>Purge All Files</b>"""
            """<p>This deletes files and directories not known to Mercurial."""
            """ That means that purge will delete:<ul>"""
            """<li>unknown files (marked with "not tracked" in the status dialog)</li>"""
            """<li>empty directories</li>"""
            """<li>ignored files and directories</li>"""
            """</ul></p>"""
        ))
        self.hgPurgeAllAct.triggered[()].connect(self.__hgPurgeAll)
        self.actions.append(self.hgPurgeAllAct)
        
        self.hgPurgeListAct = E5Action(self.trUtf8('List Files to be Purged'),
                UI.PixmapCache.getIcon("fileDeleteList.png"),
                self.trUtf8('List Files to be Purged...'),
                0, 0, self, 'mercurial_purge_list')
        self.hgPurgeListAct.setStatusTip(self.trUtf8(
            'List files and directories not known to Mercurial'
        ))
        self.hgPurgeListAct.setWhatsThis(self.trUtf8(
            """<b>List Files to be Purged</b>"""
            """<p>This lists files and directories not known to Mercurial."""
            """ These would be deleted by the "Purge Files" menu entry.</p>"""
        ))
        self.hgPurgeListAct.triggered[()].connect(self.__hgPurgeList)
        self.actions.append(self.hgPurgeListAct)
        
        self.hgPurgeAllListAct = E5Action(self.trUtf8('List All Files to be Purged'),
                self.trUtf8('List All Files to be Purged...'),
                0, 0, self, 'mercurial_purge_all_list')
        self.hgPurgeAllListAct.setStatusTip(self.trUtf8(
            'List files and directories not known to Mercurial including ignored ones'
        ))
        self.hgPurgeAllListAct.setWhatsThis(self.trUtf8(
            """<b>List All Files to be Purged</b>"""
            """<p>This lists files and directories not known to Mercurial including"""
            """ ignored ones. These would be deleted by the "Purge All Files" menu"""
            """ entry.</p>"""
        ))
        self.hgPurgeAllListAct.triggered[()].connect(self.__hgPurgeAllList)
        self.actions.append(self.hgPurgeAllListAct)
    
    def initMenu(self, mainMenu):
        """
        Public method to generate the extension menu.
        
        @param mainMenu reference to the main menu (QMenu)
        @return populated menu (QMenu)
        """
        menu = QMenu(self.trUtf8("Purge"), mainMenu)
        
        menu.addAction(self.hgPurgeAct)
        menu.addAction(self.hgPurgeAllAct)
        menu.addSeparator()
        menu.addAction(self.hgPurgeListAct)
        menu.addAction(self.hgPurgeAllListAct)
        
        return menu
    
    def __hgPurge(self):
        """
        Private slot used to remove files not tracked by Mercurial.
        """
        self.vcs.getExtensionObject("purge")\
            .hgPurge(self.project.getProjectPath(), all=False)
    
    def __hgPurgeAll(self):
        """
        Private slot used to remove all files not tracked by Mercurial.
        """
        self.vcs.getExtensionObject("purge")\
            .hgPurge(self.project.getProjectPath(), all=True)
    
    def __hgPurgeList(self):
        """
        Private slot used to list files not tracked by Mercurial.
        """
        self.vcs.getExtensionObject("purge")\
            .hgPurgeList(self.project.getProjectPath(), all=False)
    
    def __hgPurgeAllList(self):
        """
        Private slot used to list all files not tracked by Mercurial.
        """
        self.vcs.getExtensionObject("purge")\
            .hgPurgeList(self.project.getProjectPath(), all=True)
