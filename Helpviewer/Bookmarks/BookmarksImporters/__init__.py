# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing bookmarks importers for various sources.
"""

from PyQt4.QtCore import QCoreApplication

import UI.PixmapCache
import Globals


def getImporters():
    """
    Module function to get a list of supported importers.
    
    @return list of tuples with an icon (QIcon), readable name (string) and
        internal name (string)
    """
    importers = []
    importers.append(
        (UI.PixmapCache.getIcon("ericWeb48.png"), "eric5 Web Browser", "e5browser"))
    importers.append(
        (UI.PixmapCache.getIcon("chrome.png"), "Google Chrome", "chrome"))
    if not Globals.isWindowsPlatform() and not Globals.isMacPlatform():
        importers.append(
            (UI.PixmapCache.getIcon("chromium.png"), "Chromium", "chromium"))
    importers.append(
        (UI.PixmapCache.getIcon("opera.png"), "Opera", "opera"))
    importers.append(
        (UI.PixmapCache.getIcon("xbel.png"),
         QCoreApplication.translate("BookmarksImporters", "XBEL File"),
         "xbel"))
    importers.append(
        (UI.PixmapCache.getIcon("html.png"),
         QCoreApplication.translate("BookmarksImporters", "HTML File"),
         "html"))
    return importers
    # TODO: importers for Safari, Firefox, IE


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
    elif id in ["chrome", "chromium"]:
        from . import ChromeImporter
        return ChromeImporter.getImporterInfo(id)
    elif id == "opera":
        from . import OperaImporter
        return OperaImporter.getImporterInfo(id)
    else:
        raise ValueError("Invalid importer ID given ({0}).".format(id))

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
    elif id in ["chrome", "chromium"]:
        from . import ChromeImporter
        return ChromeImporter.ChromeImporter(id, parent)
    elif id == "opera":
        from . import OperaImporter
        return OperaImporter.OperaImporter(id, parent)
    else:
        raise ValueError("No importer for ID {0}.".format(id))
