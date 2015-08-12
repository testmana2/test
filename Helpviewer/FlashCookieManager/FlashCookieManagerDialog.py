# -*- coding: utf-8 -*-

# Copyright (c) 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to manage the flash cookies.
"""

from PyQt5.QtCore import pyqtSlot, Qt, QPoint, QTimer
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem, QApplication, QMenu

from E5Gui import E5MessageBox

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
        Private slot handling the selection of items in the whitelist.
        """
        enable = len(self.whiteList.selectedItems()) > 0
        self.removeWhiteButton.setEnabled(enable)
    
    @pyqtSlot()
    def on_blackList_itemSelectionChanged(self):
        """
        Private slot handling the selection of items in the blacklist.
        """
        enable = len(self.blackList.selectedItems()) > 0
        self.removeBlackButton.setEnabled(enable)
    
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
        return
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_cookiesList_currentItemChanged(self, current, previous):
        """
        Private slot handling a change of the current cookie item.
        
        @param current reference to the current item
        @type QTreeWidgetItem
        @param previous reference to the previous item
        @type QTreeWidgetItem
        """
        if current is None:
            self.removeButton.setEnabled(False)
            return
        
        cookie = current.data(0, Qt.UserRole)
        if cookie is None:
            self.nameLabel.setText(self.tr("<no flash cookie selected>"))
            self.sizeLabel.setText(self.tr("<no flash cookie selected>"))
            self.originLabel.setText(self.tr("<no flash cookie selected>"))
            self.modifiedLabel.setText(self.tr("<no flash cookie selected>"))
            self.contentsEdit.clear()
            self.pathEdit.clear()
            self.removeButton.setText(self.tr("Remove Cookie Group"))
        else:
            suffix = ""
            if cookie.path.startswith(
                self.__manager.flashPlayerDataPath() +
                    "/macromedia.com/support/flashplayer/sys"):
                suffix = self.tr(" (settings)")
            self.nameLabel.setText(
                self.tr("{0}{1}", "name and suffix")
                .format(cookie.name, suffix))
            self.sizeLabel.setText(self.tr("{0} Byte").format(cookie.size))
            self.originLabel.setText(cookie.origin)
            self.modifiedLabel.setText(
                cookie.lastModified.toString("yyyy-MM-dd hh:mm:ss"))
            self.contentsEdit.setPlainText(cookie.contents)
            self.pathEdit.setText(cookie.path)
            self.removeButton.setText(self.tr("Remove Cookie"))
        self.removeButton.setEnabled(True)
    
    @pyqtSlot(QPoint)
    def __cookiesListContextMenuRequested(self, pos):
        """
        Private slot handling the cookies list context menu.
        
        @param pos position to show the menu at
        @type QPoint
        """
        itm = self.cookiesList.itemAt(pos)
        if itm is None:
            return
        
        menu = QMenu()
        addBlacklistAct = menu.addAction(self.tr("Add to blacklist"))
        addWhitelistAct = menu.addAction(self.tr("Add to whitelist"))
        
        self.cookiesList.setCurrentItem(itm)
        
        activatedAction = menu.exec_(
            self.cookiesList.viewport().mapToGlobal(pos))
        if itm.childCount() == 0:
            origin = itm.data(0, Qt.UserRole).origin
        else:
            origin = itm.text(0)
        
        if activatedAction == addBlacklistAct:
            self.__addBlacklist(origin)
        elif activatedAction == addWhitelistAct:
            self.__addWhitelist(origin)
    
    @pyqtSlot()
    def on_reloadButton_clicked(self):
        """
        Private slot handling a press of the reload button.
        """
        self.refreshView(True)
    
    @pyqtSlot()
    def on_removeAllButton_clicked(self):
        """
        Private slot to remove all cookies.
        """
        ok = E5MessageBox.yesNo(
            self,
            self.tr("Remove All"),
            self.tr("""Do you really want to delete all flash cookies on"""
                    """ your computer?"""))
        if ok:
            cookies = self.__manager.flashCookies()
            for cookie in cookies:
                self.__manager.removeCookie(cookie)
            
            self.cookiesList.clear()
            self.__manager.clearNewOrigins()
            self.__manager.clearCache()
    
    @pyqtSlot()
    def on_removeButton_clicked(self):
        """
        Private slot to remove one cookie or a cookie group.
        """
        itm = self.cookiesList.currentItem()
        if itm is None:
            return
        
        cookie = itm.data(0, Qt.UserRole)
        if cookie is None:
            # remove a whole cookie group
            origin = itm.text(0)
            cookieList = self.__manager.flashCookies()
            for fcookie in cookieList:
                if fcookie.origin == origin:
                    self.__manager.removeCookie(fcookie)
            
            index = self.cookiesList.indexOfTopLevelItem(itm)
            self.cookiesList.takeTopLevelItem(index)
        else:
            self.__manager.removeCookie(cookie)
            parent = itm.parent()
            index = parent.indexOfChild(itm)
            parent.takeChild(index)
            
            if parent.childCount() == 0:
                # remove origin item as well
                index = self.cookiesList.indexOfTopLevelItem(parent)
                self.cookiesList.takeTopLevelItem(index)
                del parent
        del itm
    
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
                newParent.setIcon(0, UI.PixmapCache.getIcon("dirOpen.png"))
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
            
            itm.setText(0, self.tr("{0}{1}", "name and suffix").format(
                cookie.name, suffix))
            itm.setData(0, Qt.UserRole, cookie)
            
            counter += 1
            if counter > 100:
                QApplication.processEvents()
                counter = 0
        
        self.removeAllButton.setEnabled(
            self.cookiesList.topLevelItemCount() > 0)
        self.removeButton.setEnabled(False)
        
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
        
        self.on_whiteList_itemSelectionChanged()
        self.on_blackList_itemSelectionChanged()
    
    def closeEvent(self, evt):
        """
        Protected method to handle the close event.
        
        @param evt reference to the close event
        @type QCloseEvent
        """
        self.__manager.clearNewOrigins()
        
        whiteList = []
        for row in range(self.whiteList.count()):
            whiteList.append(self.whiteList.item(row).text())
        
        blackList = []
        for row in range(self.blackList.count()):
            blackList.append(self.blackList.item(row).text())
        
        Preferences.setHelp("FlashCookiesWhitelist", whiteList)
        Preferences.setHelp("FlashCookiesBlacklist", blackList)
        
        evt.accept()
