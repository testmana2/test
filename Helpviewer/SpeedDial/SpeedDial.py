# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the speed dial.
"""

import os

from PyQt4.QtCore import pyqtSignal, pyqtSlot, QObject, QCryptographicHash, QByteArray, \
    QUrl, qWarning
from PyQt4.QtWebKit import QWebPage

from .PageThumbnailer import PageThumbnailer

import Preferences
import Utilities


class Page(object):
    """
    Class to hold the data for a speed dial page.
    """
    def __init__(self, url="", title="", broken=False):
        """
        Constructor
        
        @param url URL of the page (string)
        @param title title of the page (string)
        """
        self.url = url
        self.title = title
        self.broken = broken
    
    def __eq__(self, other):
        """
        Public method implementing the equality operator.
        
        @param other reference to the other page object (Page)
        @return flag indicating equality (boolean)
        """
        return self.title == other.title and \
               self.url == other.url


class SpeedDial(QObject):
    """
    Class implementing the speed dial.
    
    @signal pagesChanged() emitted after the list of pages changed
    """
    pagesChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__regenerateScript = True
        
        self.__webPages = []
        self.__webFrames = []
        
        self.__initialScript = ""
        self.__thumbnailsDirectory = ""
        
        self.__thumbnailers = []
        
        self.__initialize()
        
        self.pagesChanged.connect(self.__pagesChanged)
    
    def addWebFrame(self, frame):
        """
        Public method to add a web frame.
        
        @param frame reference to the frame to be added (QWebFrame)
        """
        if frame not in self.__webFrames:
            self.__webFrames.append(frame)
    
    def addPage(self, url, title):
        """
        Public method to add a page for the given data.
        
        @param url URL of the page (QUrl)
        @param title title of the page (string)
        """
        if url.isEmpty():
            return
        
        page = Page(url.toString(), title)
        self.__webPages.append(page)
        
        self.pagesChanged.emit()
    
    def removePage(self, url):
        """
        Public method to remove a page.
        
        @param url URL of the page (QUrl)
        """
        page = self.pageForUrl(url)
        if not page.url:
            return
        
        self.removeImageForUrl(page.url)
        self.__webPages.remove(page)
        
        self.pagesChanged.emit()
    
    def __imageFileName(self, url):
        """
        Private method to generate the image file name for a URL.
        
        @param url URL to generate the file name from (string)
        @return name of the image file (string)
        """
        return os.path.join(self.__thumbnailsDirectory, 
            str(QCryptographicHash.hash(QByteArray(url.encode("utf-8")),
                QCryptographicHash.Md5).toHex(), encoding="utf-8") + ".png")
    
    def initialScript(self):
        """
        Public method to get the 'initial' JavaScript script.
        
        @return initial JavaScript script (string)
        """
        if self.__regenerateScript:
            self.__regenerateScript = False
            self.__initialScript = ""
            
            for page in self.__webPages:
                if page.broken:
                    imgSource = "qrc:icons/brokenPage.png"
                else:
                    imgSource = self.__imageFileName(page.url)
                    if not os.path.exists(imgSource):
                        self.loadThumbnail(page.url)
                        imgSource = "qrc:icons/loading.gif"
                        
                        if not page.url:
                            imgSource = ""
                    else:
                        imgSource = QUrl.fromLocalFile(imgSource).toString()
                
                self.__initialScript += "addBox('{0}', '{1}', '{2}');\n".format(
                    page.url, page.title, imgSource)
        
        return self.__initialScript
    
    def __initialize(self):
        """
        Private method to initialize the speed dial.
        """
        allPages = Preferences.Prefs.settings.value("Help/SpeedDial/Pages", "")
        
        if not allPages:
            allPages = \
                'url:"http://eric-ide.python-projects.org/"|title:"Eric Web Site";'\
                'url:"http://www.riverbankcomputing.com/"|title:"PyQt4 Web Site";'\
                'url:"http://qt.nokia.com/"|title:"Qt Web Site";'\
                'url:"http://www.python.org"|title:"Python Language Website";'\
                'url:"http://www.google.com"|title:"Google";'
        self.changed(allPages)
        
        self.__thumbnailsDirectory = os.path.join(
            Utilities.getConfigDir(), "browser", "thumbnails")
        # Create directory if it does not exist yet
        if not os.path.exists(self.__thumbnailsDirectory):
            os.makedirs(self.__thumbnailsDirectory)
    
    def pageForUrl(self, url):
        """
        Public method to get the page for the given URL.
        
        @param url URL to be searched for (QUrl)
        @return page for the URL (Page)
        """
        urlString = url.toString()
        for page in self.__webPages:
            if page.url == urlString:
                return page
        
        return Page()
    
    def urlForShortcut(self, key):
        """
        Public method to get the URL for the given shortcut key.
        
        @param key shortcut key (integer)
        @return URL for the key (QUrl)
        """
        if key < 0 or len(self.__webPages) <= key:
            return QUrl()
        
        return QUrl.fromEncoded(self.__webPages[key].url.encode("utf-8"))
    
    @pyqtSlot(str)
    def changed(self, allPages):
        """
        Public slot to react on changed pages.
        
        @param allPages string giving all pages (string)
        """
        if not allPages:
            return
        
        entries = allPages.split('";')
        self.__webPages = []
        
        for entry in entries:
            if not entry:
                continue
            
            tmp = entry.split('"|')
            if len(tmp) == 2:
                broken = False
            elif len(tmp) == 3:
                broken = "brokenPage" in tmp[2][5:]
            else:
                continue
            
            page = Page(tmp[0][5:], tmp[1][7:], broken)
            self.__webPages.append(page)
        
        self.pagesChanged.emit()
    
    @pyqtSlot(str)
    @pyqtSlot(str, bool)
    def loadThumbnail(self, url, loadTitle=False):
        """
        Public slot to load a thumbnail of the given URL.
        
        @param url URL of the thumbnail (string)
        @param loadTitle flag indicating to get the title for the thumbnail
            from the site (boolean)
        """
        if not url:
            return
        
        thumbnailer = PageThumbnailer(self)
        thumbnailer.setUrl(QUrl.fromEncoded(url.encode("utf-8")))
        thumbnailer.setLoadTitle(loadTitle)
        thumbnailer.thumbnailCreated.connect(self.__thumbnailCreated)
        self.__thumbnailers.append(thumbnailer)
        
        thumbnailer.start()

    @pyqtSlot(str)
    def removeImageForUrl(self, url):
        """
        Public slot to remove the image for a URL.
        
        @param url URL to remove the image for (string)
        """
        fileName = self.__imageFileName(url)
        if os.path.exists(fileName):
            os.remove(fileName)

    @pyqtSlot(str, result=str)
    def urlFromUserInput(self, url):
        """
        Public slot to get the URL from user input.
        
        @param url URL entered by the user (string)
        @return sanitized URL (string)
        """
        return QUrl.fromUserInput(url).toString()

    @pyqtSlot(int)
    def setPagesInRow(self, count):
        """
        Public slot to set the number of pages per row.
        
        @param count number of pages per row (integer)
        """
        Preferences.Prefs.settings.setValue("Help/SpeedDial/PagesPerRow", count)

    def pagesInRow(self):
        """
        Public method to get the number of dials per row.
        
        @return number of dials per row (integer)
        """
        return int(
            Preferences.Prefs.settings.value("Help/SpeedDial/PagesPerRow", 4))
    
    @pyqtSlot(int)
    def setSdSize(self, size):
        """
        Public slot to set the size of the speed dial.
        
        @param size size of the speed dial (integer)
        """
        Preferences.Prefs.settings.setValue("Help/SpeedDial/SpeedDialSize", size)
    
    def sdSize(self):
        """
        Public method to get the speed dial size.
        
        @return speed dial size (integer)
        """
        return int(
            Preferences.Prefs.settings.value("Help/SpeedDial/SpeedDialSize", 231))
    
    def __thumbnailCreated(self, image):
        """
        Private slot to handle the creation of a thumbnail image.
        
        @param image thumbnail image (QPixmap)
        """
        thumbnailer = self.sender()
        if not isinstance(thumbnailer, PageThumbnailer) or \
           thumbnailer not in self.__thumbnailers:
            return
        
        loadTitle = thumbnailer.loadTitle()
        title = thumbnailer.title()
        url = thumbnailer.url().toString()
        fileName = self.__imageFileName(url)
        
        if image.isNull():
            fileName = "qrc:icons/brokenPage.png"
            title = self.trUtf8("Unable to load")
            loadTitle = True
            page = self.pageForUrl(thumbnailer.url())
            page.broken = True
        else:
            if not image.save(fileName):
                qWarning("SpeedDial.__thumbnailCreated: Cannot save thumbnail to {0}"
                         .format(fileName))
            
            fileName = QUrl.fromLocalFile(fileName).toString()
        
        self.__regenerateScript = True
        
        for frame in self.__cleanFrames():
            frame.evaluateJavaScript("setImageToUrl('{0}', '{1}');".format(
                                     url, fileName))
            if loadTitle:
                frame.evaluateJavaScript("setTitleToUrl('{0}', '{1}');".format(
                                         url, title))
        
        thumbnailer.thumbnailCreated.disconnect(self.__thumbnailCreated)
        self.__thumbnailers.remove(thumbnailer)
    
    def __cleanFrames(self):
        """
        Private method to clean all frames.
        
        @return list of speed dial frames (list of QWebFrame)
        """
        frames = []
        
        for frame in self.__webFrames[:]:
            if frame.url().toString() == "eric:speeddial":
                frames.append(frame)
            else:
                self.__webFrames.remove(frame)
        
        return frames
    
    def __pagesChanged(self):
        """
        Private slot to react on a change of the pages configuration.
        """
        # step 1: save the list of pages
        Preferences.Prefs.settings.setValue(
            "Help/SpeedDial/Pages", self.__generateAllPages())
        
        # step 2: update all speed dial pages
        self.__regenerateScript = True
        for frame in self.__cleanFrames():
            frame.page().triggerAction(QWebPage.Reload)
    
    def __generateAllPages(self):
        """
        Private method to generate s string with all pages managed by the speed dial.
        
        @return string with all pages (string)
        """
        allPages = ""
        
        for page in self.__webPages:
            entry = 'url:"{0}"|title:"{1}";'.format(page.url, page.title)
            allPages += entry
        
        return allPages
