# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an importer for HTML bookmark files.
"""

import os

from PyQt4.QtCore import QCoreApplication, QDate, Qt

from .BookmarksImporter import BookmarksImporter

import UI.PixmapCache


def getImporterInfo(id):
    """
    Module function to get information for the given HTML source id.
    
    @param id id of the browser ("chrome" or "chromium")
    @return tuple with an icon (QPixmap), readable name (string), name of
        the default bookmarks file (string), an info text (string),
        a prompt (string) and the default directory of the bookmarks file (string)
    @exception ValueError raised to indicate an invalid browser ID
    """
    if id == "html":
        return (
            UI.PixmapCache.getPixmap("html.png"),
            "HTML Netscape Bookmarks",
            QCoreApplication.translate("HtmlImporter",
                "HTML Netscape Bookmarks") + " (*.htm *.html)",
            QCoreApplication.translate("HtmlImporter",
                """You can import bookmarks from any browser that supports HTML """
                """exporting. This file has usually the extension .htm or .html."""),
            QCoreApplication.translate("HtmlImporter",
                """Please choose the file to begin importing bookmarks."""),
            "",
        )
    else:
        raise ValueError("Unsupported browser ID given ({0}).".format(id))


class HtmlImporter(BookmarksImporter):
    """
    Class implementing the HTML bookmarks importer.
    """
    def __init__(self, id="", parent=None):
        """
        Constructor
        
        @param id source ID (string)
        @param parent reference to the parent object (QObject)
        """
        super().__init__(id, parent)
        
        self.__fileName = ""
        self.__inFile = None
    
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
        from ..BookmarkNode import BookmarkNode
        from ..NsHtmlReader import NsHtmlReader
        
        reader = NsHtmlReader()
        importRootNode = reader.read(self.__fileName)
        
        importRootNode.setType(BookmarkNode.Folder)
        if self._id == "html":
            importRootNode.title = self.trUtf8("HTML Import")
        else:
            importRootNode.title = self.trUtf8("Imported {0}")\
                .format(QDate.currentDate().toString(Qt.SystemLocaleShortDate))
        return importRootNode
