# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a tool bar showing bookmarks.
"""

from PyQt4.QtCore import pyqtSignal, Qt, QUrl
from PyQt4.QtGui import QMenu, QApplication, QCursor
from PyQt4.QtWebKit import QWebPage

from E5Gui.E5ModelToolBar import E5ModelToolBar

import Helpviewer.HelpWindow

from .BookmarksModel import BookmarksModel
from .BookmarksMenu import BookmarksMenu
from .AddBookmarkDialog import AddBookmarkDialog


class BookmarksToolBar(E5ModelToolBar):
    """
    Class implementing a tool bar showing bookmarks.
    
    @signal openUrl(QUrl, str) emitted to open a URL in the current tab
    @signal newUrl(QUrl, str) emitted to open a URL in a new tab
    """
    openUrl = pyqtSignal(QUrl, str)
    newUrl = pyqtSignal(QUrl, str)
    
    def __init__(self, mainWindow, model, parent=None):
        """
        Constructor
        
        @param mainWindow reference to the main window (HelpWindow)
        @param model reference to the bookmarks model (BookmarksModel)
        @param parent reference to the parent widget (QWidget)
        """
        E5ModelToolBar.__init__(self,
            QApplication.translate("BookmarksToolBar", "Bookmarks"), parent)
        
        self.__mw = mainWindow
        self.__bookmarksModel = model
        
        Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
            .bookmarksReloaded.connect(self.__rebuild)
        
        self.setModel(model)
        self.setRootIndex(model.nodeIndex(
            Helpviewer.HelpWindow.HelpWindow.bookmarksManager().toolbar()))
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__contextMenuRequested)
        self.activated.connect(self.__bookmarkActivated)
        
        self.setHidden(True)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        self._build()
    
    def __rebuild(self):
        """
        Private slot to rebuild the toolbar.
        """
        self.__bookmarksModel = \
            Helpviewer.HelpWindow.HelpWindow.bookmarksManager().bookmarksModel()
        self.setModel(self.__bookmarksModel)
        self.setRootIndex(self.__bookmarksModel.nodeIndex(
            Helpviewer.HelpWindow.HelpWindow.bookmarksManager().toolbar()))
        self._build()
    
    def __contextMenuRequested(self, pos):
        """
        Private slot to handle the context menu request.
        
        @param pos position the context menu shall be shown (QPoint)
        """
        act = self.actionAt(pos)
        menu = QMenu()
        
        if act is not None:
            v = act.data()
            
            if act.menu() is None:
                menuAction = menu.addAction(self.trUtf8("&Open"), self.__openBookmark)
                menuAction.setData(v)
                
                menuAction = menu.addAction(self.trUtf8("Open in New &Tab\tCtrl+LMB"),
                    self.__openBookmarkInNewTab)
                menuAction.setData(v)
                
                menu.addSeparator()
            
            menuAction = menu.addAction(self.trUtf8("&Remove"), self.__removeBookmark)
            menuAction.setData(v)
            
            menu.addSeparator()
        
        menu.addAction(self.trUtf8("Add &Bookmark..."), self.__newBookmark)
        menu.addAction(self.trUtf8("Add &Folder..."), self.__newFolder)
        
        menu.exec_(QCursor.pos())
    
    def __bookmarkActivated(self, idx):
        """
        Private slot handling the activation of a bookmark.
        
        @param idx index of the activated bookmark (QModelIndex)
        """
        assert idx.isValid()
        
        if self._mouseButton == Qt.XButton1:
            self.__mw.currentBrowser().pageAction(QWebPage.Back).trigger()
        elif self._mouseButton == Qt.XButton2:
            self.__mw.currentBrowser().pageAction(QWebPage.Forward).trigger()
        elif self._mouseButton == Qt.LeftButton:
            if self._keyboardModifiers & Qt.ControlModifier:
                self.newUrl.emit(
                    idx.data(BookmarksModel.UrlRole),
                    idx.data(Qt.DisplayRole))
            else:
                self.openUrl.emit(
                    idx.data(BookmarksModel.UrlRole),
                    idx.data(Qt.DisplayRole))
    
    def __openToolBarBookmark(self):
        """
        Private slot to open a bookmark in the current browser tab.
        """
        idx = self.index(self.sender())
        
        if self._keyboardModifiers & Qt.ControlModifier:
            self.newUrl.emit(
                idx.data(BookmarksModel.UrlRole),
                idx.data(Qt.DisplayRole))
        else:
            self.openUrl.emit(
                idx.data(BookmarksModel.UrlRole),
                idx.data(Qt.DisplayRole))
        self.resetFlags()
    
    def __openBookmark(self):
        """
        Private slot to open a bookmark in the current browser tab.
        """
        idx = self.index(self.sender())
        
        self.openUrl.emit(
            idx.data(BookmarksModel.UrlRole),
            idx.data(Qt.DisplayRole))
    
    def __openBookmarkInNewTab(self):
        """
        Private slot to open a bookmark in a new browser tab.
        """
        idx = self.index(self.sender())
        
        self.newUrl.emit(
            idx.data(BookmarksModel.UrlRole),
            idx.data(Qt.DisplayRole))
    
    def __removeBookmark(self):
        """
        Private slot to remove a bookmark.
        """
        idx = self.index(self.sender())
        
        self.__bookmarksModel.removeRow(idx.row(), self.rootIndex())
    
    def __newBookmark(self):
        """
        Private slot to add a new bookmark.
        """
        dlg = AddBookmarkDialog()
        dlg.setCurrentIndex(self.rootIndex())
        dlg.exec_()
    
    def __newFolder(self):
        """
        Private slot to add a new bookmarks folder.
        """
        dlg = AddBookmarkDialog()
        dlg.setCurrentIndex(self.rootIndex())
        dlg.setFolder(True)
        dlg.exec_()
    
    def _createMenu(self):
        """
        Protected method to create the menu for a tool bar action.
        
        @return menu for a tool bar action (E5ModelMenu)
        """
        menu = BookmarksMenu(self)
        menu.openUrl.connect(self.openUrl)
        menu.newUrl.connect(self.newUrl)
        return menu
