# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing an importer for HTML bookmark files.
"""

import os
import tempfile

from PyQt4.QtCore import QCoreApplication, QXmlStreamReader, QDate, Qt
from PyQt4.QtWebKit import QWebPage

from ..BookmarkNode import BookmarkNode
from ..XbelReader import XbelReader

from .BookmarksImporter import BookmarksImporter

import UI.PixmapCache

##########################################################################################

extract_js = r"""
function walk() {
    var parent = arguments[0];
    var indent = arguments[1];

    var result = "";
    var children = parent.childNodes;
    var folderName = "";
    var folded = "";
    for (var i = 0; i < children.length; i++) {
        var object = children.item(i);
        if (object.nodeName == "HR") {
            result += indent + "<separator/>\n";
        }
        if (object.nodeName == "H3") {
            folderName = object.innerHTML;
            folded = object.folded;
            if (object.folded == undefined)
                folded = "false";
            else
                folded = "true";
        }
        if (object.nodeName == "A") {
            result += indent + "<bookmark href=\"" + encodeURI(object.href).replace(/&/g, '&amp;') + "\">\n";
            result += indent + indent + "<title>" + object.innerHTML + "</title>\n";
            result += indent + "</bookmark>\n";
        }

        var currentIndent = indent;
        if (object.nodeName == "DL" && folderName != "") {
            result += indent + "<folder folded=\"" + folded + "\">\n";
            indent += "    ";
            result += indent + "<title>" + folderName + "</title>\n";
        }
        result += walk(object, indent);
        if (object.nodeName == "DL" && folderName != "") {
            result += currentIndent + "</folder>\n";
        }
    }
    return result;
}

var xbel = walk(document, "    ");

if (xbel != "") {
    xbel = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!DOCTYPE xbel>\n<xbel version=\"1.0\">\n" + xbel + "</xbel>\n";
}

xbel;
"""

##########################################################################################


def getImporterInfo(id):
    """
    Module function to get information for the given HTML source id.
    
    @return tuple with an icon (QPixmap), readable name (string), name of
        the default bookmarks file (string), an info text (string),
        a prompt (string) and the default directory of the bookmarks file (string)
    """
    if id == "html":
        return (
            UI.PixmapCache.getPixmap("html.png"),
            "HTML Netscape Bookmarks",
            QCoreApplication.translate("HtmlImporter",
                "HTML Netscape Bookmarks") + " (*.htm *.html)",
            QCoreApplication.translate("HtmlImporter",
                """You can import bookmarks from any browser that supports HTML """
                """exporting. This file has usually the extension .htm or .html.""" ),
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
        try:
            f = open(self.__fileName, "r")
            contents = f.read()
            f.close()
        except IOError as err:
            self._error = True
            self._errorString = self.trUtf8("File '{0}' cannot be read.\nReason: {1}")\
                .format(self.__fileName, str(err))
            return None
        
        reader = XbelReader()
        webpage = QWebPage()
        webpage.mainFrame().setHtml(contents)
        result = webpage.mainFrame().evaluateJavaScript(extract_js)
        
        fd, name = tempfile.mkstemp(text=True)
        f = os.fdopen(fd, "w")
        f.write(result)
        f.close()
        importRootNode = reader.read(name)
        os.remove(name)
        
        if reader.error() != QXmlStreamReader.NoError:
            self._error = True
            self._errorString = self.trUtf8(
                """Error when importing bookmarks on line {0}, column {1}:\n{2}""")\
                .format(reader.lineNumber(),
                        reader.columnNumber(),
                        reader.errorString())
            return None
        
        importRootNode.setType(BookmarkNode.Folder)
        if self._id == "html":
            importRootNode.title = self.trUtf8("HTML Import")
        else:
            importRootNode.title = self.trUtf8("Imported {0}")\
                .format(QDate.currentDate().toString(Qt.SystemLocaleShortDate))
        return importRootNode
