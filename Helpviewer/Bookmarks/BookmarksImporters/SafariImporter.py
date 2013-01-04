# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an importer for Apple Safari bookmarks.
"""

import os

from PyQt4.QtCore import QCoreApplication, QDate, Qt

from ..BookmarkNode import BookmarkNode

from .BookmarksImporter import BookmarksImporter

import UI.PixmapCache
import Globals

from Utilities import binplistlib


def getImporterInfo(id):
    """
    Module function to get information for the given source id.
    
    @return tuple with an icon (QPixmap), readable name (string), name of
        the default bookmarks file (string), an info text (string),
        a prompt (string) and the default directory of the bookmarks file (string)
    """
    if id == "safari":
        if Globals.isWindowsPlatform():
            standardDir = os.path.expandvars(
                "%APPDATA%\\Apple Computer\\Safari")
        elif Globals.isMacPlatform():
            standardDir = os.path.expanduser("~/Library/Safari")
        else:
            standardDir = ""
        return (
            UI.PixmapCache.getPixmap("safari.png"),
            "Apple Safari",
            "Bookmarks.plist",
            QCoreApplication.translate("SafariImporter",
                """Apple Safari stores its bookmarks in the <b>Bookmarks.plist</b> """
                """file. This file is usually located in"""),
            QCoreApplication.translate("SafariImporter",
                """Please choose the file to begin importing bookmarks."""),
            standardDir,
        )
    else:
        raise ValueError("Unsupported browser ID given ({0}).".format(id))


class SafariImporter(BookmarksImporter):
    """
    Class implementing the Apple Safari bookmarks importer.
    """
    def __init__(self, id="", parent=None):
        """
        Constructor
        
        @param id source ID (string)
        @param parent reference to the parent object (QObject)
        """
        super().__init__(id, parent)
        
        self.__fileName = ""
    
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
        return True
    
    def importedBookmarks(self):
        """
        Public method to get the imported bookmarks.
        
        @return imported bookmarks (BookmarkNode)
        """
        try:
            bookmarksDict = binplistlib.readPlist(self.__fileName)
        except binplistlib.InvalidPlistException as err:
            self._error = True
            self._errorString = self.trUtf8(
                "Bookmarks file cannot be read.\nReason: {0}".format(str(err)))
            return None
        
        importRootNode = BookmarkNode(BookmarkNode.Folder)
        if bookmarksDict["WebBookmarkFileVersion"] == 1 and \
           bookmarksDict["WebBookmarkType"] == "WebBookmarkTypeList":
            self.__processChildren(bookmarksDict["Children"], importRootNode)
        
        if self._id == "safari":
            importRootNode.title = self.trUtf8("Apple Safari Import")
        else:
            importRootNode.title = self.trUtf8("Imported {0}")\
                .format(QDate.currentDate().toString(Qt.SystemLocaleShortDate))
        return importRootNode
    
    def __processChildren(self, children, rootNode):
        """
        Private method to process the list of children.
        
        @param children list of child nodes to be processed (list of dict)
        @param rootNode node to add the bookmarks to (BookmarkNode)
        """
        for child in children:
            if child["WebBookmarkType"] == "WebBookmarkTypeList":
                folder = BookmarkNode(BookmarkNode.Folder, rootNode)
                folder.title = child["Title"].replace("&", "&&")
                if "Children" in child:
                    self.__processChildren(child["Children"], folder)
            elif child["WebBookmarkType"] == "WebBookmarkTypeLeaf":
                url = child["URLString"]
                if url.startswith(("place:", "about:")):
                    continue
                
                bookmark = BookmarkNode(BookmarkNode.Bookmark, rootNode)
                bookmark.url = url
                bookmark.title = child["URIDictionary"]["title"].replace("&", "&&")