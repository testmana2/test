# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an importer for Firefox bookmarks.
"""

import os

from PyQt4.QtCore import QCoreApplication, QDate, Qt, QUrl
from PyQt4.QtSql import QSqlDatabase, QSqlQuery

from ..BookmarkNode import BookmarkNode

from .BookmarksImporter import BookmarksImporter

import UI.PixmapCache
import Globals


def getImporterInfo(id):
    """
    Module function to get information for the given source id.
    
    @return tuple with an icon (QPixmap), readable name (string), name of
        the default bookmarks file (string), an info text (string),
        a prompt (string) and the default directory of the bookmarks file (string)
    """
    if id == "firefox":
        if Globals.isWindowsPlatform():
            standardDir = os.path.expandvars(
                "%APPDATA%\\Mozilla\\Firefox\\Profiles")
        else:
            standardDir = os.path.expanduser("~/.mozilla/firefox")
        return (
            UI.PixmapCache.getPixmap("chrome.png"),
            "Mozilla Firefox",
            "places.sqlite",
            QCoreApplication.translate("FirefoxImporter",
                """Mozilla Firefox stores its bookmarks in the <b>places.sqlite</b> """
                """SQLite database. This file is usually located in"""),
            QCoreApplication.translate("FirefoxImporter",
                """Please choose the file to begin importing bookmarks."""),
            standardDir,
        )
    else:
        raise ValueError("Unsupported browser ID given ({0}).".format(id))


class FirefoxImporter(BookmarksImporter):
    """
    Class implementing the Chrome bookmarks importer.
    """
    def __init__(self, id="", parent=None):
        """
        Constructor
        
        @param id source ID (string)
        @param parent reference to the parent object (QObject)
        """
        super().__init__(id, parent)
        
        self.__fileName = ""
        self.__db = None
    
    def setPath(self, path):
        """
        Public method to set the path of the bookmarks file or directory.
        
        @param path bookmarks file or directory (string)
        """
        self.__fileName = path
    
    def open(self):
        """
        Public method to open the bookmarks file.
        
        @return flag indicating success (boolean)
        """
        if not os.path.exists(self.__fileName):
            self._error = True
            self._errorString = self.trUtf8("File '{0}' does not exist.")\
                .format(self.__fileName)
            return False
        
        self.__db = QSqlDatabase.addDatabase("QSQLITE")
        self.__db.setDatabaseName(self.__fileName)
        opened = self.__db.open()
        
        if not opened:
            self._error = True
            self._errorString = self.trUtf8("Unable to open database.\nReason: {0}")\
                .format(self.__db.lastError().text())
            return False
        
        return True
    
    def importedBookmarks(self):
        """
        Public method to get the imported bookmarks.
        
        @return imported bookmarks (BookmarkNode)
        """
        importRootNode = BookmarkNode(BookmarkNode.Folder)
        
        # step 1: build the hierarchy of bookmark folders
        folders = {}
        query = QSqlQuery(self.__db)
        query.exec_(
            "SELECT id, parent, title FROM moz_bookmarks WHERE type = 2 and title !=''")
        while query.next():
            id_ = int(query.value(0))
            parent = int(query.value(1))
            title = query.value(2)
            if parent in folders:
                folder = BookmarkNode(BookmarkNode.Folder, folders[parent])
            else:
                folder = BookmarkNode(BookmarkNode.Folder, importRootNode)
            folder.title = title.replace("&", "&&")
            folders[id_] = folder
        
        query = QSqlQuery(self.__db)
        query.exec_(
            "SELECT parent, title, fk, position FROM moz_bookmarks"
            " WHERE type = 1 and title != '' ORDER BY position")
        while query.next():
            parent = int(query.value(0))
            title = query.value(1).replace("&", "&&")
            placesId = int(query.value(2))
            
            query2 = QSqlQuery(self.__db)
            query2.exec_("SELECT url FROM moz_places WHERE id = {0}".format(placesId))
            if not query2.next():
                continue
            
            url = QUrl(query2.value(0))
            if not title or url.isEmpty() or url.scheme() in ["place", "about"]:
                continue
            
            if parent in folders:
                bookmark = BookmarkNode(BookmarkNode.Bookmark, folders[parent])
            else:
                bookmark = BookmarkNode(BookmarkNode.Bookmark, importRootNode)
            bookmark.url = url.toString()
            bookmark.title = title.replace("&", "&&")
        
        if query.lastError().isValid():
            self._error = True
            self._errorString = query.lastError().text()
        
        if self._id == "firefox":
            importRootNode.title = self.trUtf8("Mozilla Firefox Import")
        else:
            importRootNode.title = self.trUtf8("Imported {0}")\
                .format(QDate.currentDate().toString(Qt.SystemLocaleShortDate))
        return importRootNode
