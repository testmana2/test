# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the AdBlock icon for the main window status bar.
"""

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QAction, QMenu

from E5Gui.E5ClickableLabel import E5ClickableLabel

import Helpviewer.HelpWindow

import UI.PixmapCache


class AdBlockIcon(E5ClickableLabel):
    """
    Class implementing the AdBlock icon for the main window status bar.
    """
    def __init__(self, parent):
        """
        Constructor
        
        @param parent reference to the parent widget (HelpWindow)
        """
        super().__init__(parent)
        
        self.__mw = parent
        self.__menuAction = None
        self.__enabled = False
        
        self.setMaximumHeight(16)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(
            self.trUtf8("AdBlock lets you block unwanted content on web pages."))
        
        self.clicked.connect(self.__showMenu)
    
    def setEnabled(self, enabled):
        """
        Public slot to set the enabled state.
        
        @param enabled enabled state (boolean)
        """
        if enabled:
            self.setPixmap(UI.PixmapCache.getPixmap("adBlockPlus16.png"))
        else:
            self.setPixmap(UI.PixmapCache.getPixmap("adBlockPlusDisabled16.png"))
        self.__enabled = enabled
    
    def __createMenu(self, menu=None):
        """
        Private slot to create the context menu.
        
        @param menu parent menu (QMenu)
        """
        if menu is None:
            menu = self.sender()
            if menu is None:
                return
        
        menu.clear()
        
        manager = Helpviewer.HelpWindow.HelpWindow.adblockManager()
        
        if manager.isEnabled():
            menu.addAction(UI.PixmapCache.getIcon("adBlockPlusDisabled.png"),
                self.trUtf8("Disable AdBlock"), self.__enableAdBlock).setData(False)
        else:
            menu.addAction(UI.PixmapCache.getIcon("adBlockPlus.png"),
                self.trUtf8("Enable AdBlock"), self.__enableAdBlock).setData(True)
        menu.addSeparator()
        menu.addAction(UI.PixmapCache.getIcon("adBlockPlus.png"),
            self.trUtf8("AdBlock Configuration"), manager.showDialog)
        menu.addSeparator()
        
        entries = self.__mw.currentBrowser().page().getAdBlockedPageEntries()
        if entries:
            menu.addAction(
                self.trUtf8("Blocked URL (AdBlock Rule) - click to edit rule"))\
                .setEnabled(False)
            for entry in entries:
                address = entry.urlString()[-55:]
                actionText = self.trUtf8("{0} with ({1})").format(
                    address, entry.rule.filter()).replace("&", "&&")
                act = menu.addAction(actionText, manager.showRule)
                act.setData(entry.rule)
        else:
            menu.addAction(self.trUtf8("No content blocked")).setEnabled(False)
    
    def menuAction(self):
        """
        Public method to get a reference to the menu action.
        
        @return reference to the menu action (QAction)
        """
        if not self.__menuAction:
            self.__menuAction = QAction(self.trUtf8("AdBlock"))
            self.__menuAction.setMenu(QMenu())
            self.__menuAction.menu().aboutToShow.connect(self.__createMenu)
        
        if self.__enabled:
            self.__menuAction.setIcon(UI.PixmapCache.getIcon("adBlockPlus.png"))
        else:
            self.__menuAction.setIcon(UI.PixmapCache.getIcon("adBlockPlusDisabled.png"))
        
        return self.__menuAction
    
    def __showMenu(self, pos):
        """
        Private slot to show the context menu.
        
        @param pos position the context menu should be shown (QPoint)
        """
        menu = QMenu()
        self.__createMenu(menu)
        menu.exec_(pos)
    
    def __enableAdBlock(self):
        """
        Private slot to enable or disable AdBlock.
        """
        act = self.sender()
        if act is not None:
            Helpviewer.HelpWindow.HelpWindow.adblockManager().setEnabled(act.data())
