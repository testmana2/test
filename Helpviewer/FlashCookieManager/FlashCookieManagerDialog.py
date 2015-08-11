# -*- coding: utf-8 -*-

# Copyright (c) 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to manage the flash cookies.
"""

from PyQt5.QtCore import pyqtSlot, Qt, QPoint, QTimer
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem, QApplication

from .Ui_FlashCookieManagerDialog import Ui_FlashCookieManagerDialog

import Preferences
import UI.PixmapCache


class FlashCookieManagerDialog(QDialog, Ui_FlashCookieManagerDialog):
    """
    Class implementing a dialog to manage the flash cookies.
    """
    def __init__(self, manager, parent=None):
        """
        Constructor
        
        @param manager reference to the Flash cookie manager object
        @type FlashCookieManager
        @param parent reference to the parent widget
        @type QWidget
        """
        super(FlashCookieManagerDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.cookiesList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cookiesList.customContextMenuRequested.connect(
            self.__cookiesListContextMenuRequested)
        
        self.__manager = manager
    
    @pyqtSlot()
    def on_whiteList_itemSelectionChanged(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_blackList_itemSelectionChanged(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_removeWhiteButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_addWhiteButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_removeBlackButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_addBlackButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot(str)
    def on_filterEdit_textChanged(self, p0):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_cookiesList_currentItemChanged(self, current, previous):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_cookiesList_itemSelectionChanged(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot(QPoint)
    def __cookiesListContextMenuRequested(self, point):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_reloadButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_removeAllButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_removeButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    def refreshView(self, forceReload=False):
        """
        Public method to refresh the dialog view.
        
        @param forceReload flag indicating to reload the cookies
        @type bool
        """
        blocked = self.filterEdit.blockSignals(True)
        self.filterEdit.clear()
        self.contentsEdit.clear()
        self.filterEdit.blockSignals(blocked)
        
        if forceReload:
            self.__manager.clearCache()
            self.__manager.clearNewOrigins()
        
        QTimer.singleShot(0, self.__refreshCookiesList)
        QTimer.singleShot(0, self.__refreshFilterLists)
    
    def showPage(self, index):
        """
        Public method to display a given page.
        
        @param index index of the page to be shown
        @type int
        """
        self.cookiesTabWidget.setCurrentIndex(index)
    
    @pyqtSlot()
    def __refreshCookiesList(self):
        """
        Private slot to refresh the cookies list.
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        cookies = self.__manager.flashCookies()
        self.cookiesList.clear()
        
        counter = 0
        originDict = {}
        for cookie in cookies:
            cookieOrigin = cookie.origin
            if cookieOrigin.startswith("."):
                cookieOrigin = cookieOrigin[1:]
            
            if cookieOrigin in originDict:
                itm = QTreeWidgetItem(originDict[cookieOrigin])
            else:
                newParent = QTreeWidgetItem(self.cookiesList)
                newParent.setText(0, cookieOrigin)
                newParent.setIcon(UI.PixmapCache.getIcon("dirOpen.png"))
                self.cookiesList.addTopLevelItem(newParent)
                originDict[cookieOrigin] = newParent
                
                itm = QTreeWidgetItem(newParent)
            
            suffix = ""
            if cookie.path.startswith(
                self.__manager.flashPlayerDataPath() + 
                    "/macromedia.com/support/flashplayer/sys"):
                suffix = self.tr(" (settings)")
            
            if cookie.path + "/" + cookie.name in \
                    self.__manager.newCookiesList():
                suffix += self.tr(" [new]")
                font = itm.font(0)
                font.setBold(True)
                itm.setFont(font)
                itm.parent().setExpanded(True)
            
            itm.setText(0, cookie.name + suffix)
            itm.setData(0, Qt.UserRole, cookie)
            
            counter += 1
            if counter > 100:
                QApplication.processEvents()
                counter = 0
        
        QApplication.restoreOverrideCursor()
    
    @pyqtSlot()
    def __refreshFilterLists(self):
        """
        Private slot to refresh the white and black lists.
        """
        self.whiteList.clear()
        self.blackList.clear()
        
        self.whiteList.addItems(Preferences.getHelp("FlashCookiesWhitelist"))
        self.blackList.addItems(Preferences.getHelp("FlashCookiesBlacklist"))
