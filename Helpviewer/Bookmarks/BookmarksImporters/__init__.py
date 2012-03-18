# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing bookmarks importers for various sources.
"""

from PyQt4.QtCore import QCoreApplication

import UI.PixmapCache


def getImporters():
    """
    Module function to get a list of supported importers.
    
    @return list of tuples with an icon (QIcon), readable name (string) and
        internal name (string)
    """
    return [
        (UI.PixmapCache.getIcon("ericWeb48.png"),
         "eric5 Web Browser",
         "e5browser"),
        (UI.PixmapCache.getIcon("xbel.png"),
         QCoreApplication.translate("BookmarksImporters", "XBEL File"),
         "xbel"),
        (UI.PixmapCache.getIcon("html.png"),
         QCoreApplication.translate("BookmarksImporters", "HTML File"),
         "html"),
    ]


def getImporterInfo(id):
    """
    Module function to get information for the given source id.
    
    @param id source id to get info for (string)
    @return tuple with an icon (QPixmap), readable name (string), name of
        the default bookmarks file (string), an info text (string),
        a prompt (string) and the default directory of the bookmarks file (string)
    """
    if id in ["e5browser", "xbel"]:
        from . import XbelImporter
        return XbelImporter.getImporterInfo(id)
    elif id == "html":
        from . import HtmlImporter
        return HtmlImporter.getImporterInfo(id)

def getImporter(id, parent=None):
    """
    Module function to get an importer for the given source id.
    
    @param id source id to get an importer for (string)
    @param parent reference to the parent object (QObject)
    @return bookmarks importer (BookmarksImporter)
    """
    if id in ["e5browser", "xbel"]:
        from . import XbelImporter
        return XbelImporter.XbelImporter(id, parent)
    elif id == "html":
        from . import HtmlImporter
        return HtmlImporter.HtmlImporter(id, parent)
    else:
        raise ValueError("No importer for ID {0}.".format(id))
