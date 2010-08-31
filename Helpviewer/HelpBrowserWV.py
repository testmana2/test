# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#


"""
Module implementing the helpbrowser using QWebView.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtWebKit
from PyQt4.QtWebKit import QWebView, QWebPage, QWebSettings
try:
    from PyQt4.QtWebKit import QWebElement
except ImportError:
    pass
from PyQt4.QtNetwork import QNetworkReply, QNetworkRequest
import sip

from E5Gui import E5MessageBox

import Preferences

from .DownloadDialog import DownloadDialog
from .Bookmarks.AddBookmarkDialog import AddBookmarkDialog
from .JavaScriptResources import fetchLinks_js
from .HTMLResources import notFoundPage_html
import Helpviewer.HelpWindow

from .Network.NetworkAccessManagerProxy import NetworkAccessManagerProxy

from .OpenSearch.OpenSearchEngineAction import OpenSearchEngineAction
from .OpenSearch.OpenSearchEngine import OpenSearchEngine

##########################################################################################

class JavaScriptExternalObject(QObject):
    """
    Class implementing an external javascript object to add search providers.
    """
    def __init__(self, mw, parent = None):
        """
        Constructor
        
        @param mw reference to the main window 8HelpWindow)
        @param parent reference to the parent object (QObject)
        """
        QObject.__init__(self, parent)
        
        self.__mw = mw
    
    @pyqtSlot(str)
    def AddSearchProvider(self, url):
        """
        Public slot to add a search provider.
        
        @param url url of the XML file defining the search provider (string)
        """
        self.__mw.openSearchManager().addEngine(QUrl(url));

class LinkedResource(object):
    """
    Class defining a data structure for linked resources.
    """
    def __init__(self):
        """
        Constructor
        """
        self.rel = ""
        self.type_ = ""
        self.href = ""
        self.title = ""

##########################################################################################

class JavaScriptEricObject(QObject):
    """
    Class implementing an external javascript object to search via the startpage.
    """
    # these must be in line with the strings used by the javascript part of the start page
    translations = [
        QT_TRANSLATE_NOOP("JavaScriptEricObject", "Welcome to Eric Web Browser!"), 
        QT_TRANSLATE_NOOP("JavaScriptEricObject", "Eric Web Browser"), 
        QT_TRANSLATE_NOOP("JavaScriptEricObject", "Search!"), 
        QT_TRANSLATE_NOOP("JavaScriptEricObject", "About Eric"), 
    ]
    
    def __init__(self, mw, parent = None):
        """
        Constructor
        
        @param mw reference to the main window 8HelpWindow)
        @param parent reference to the parent object (QObject)
        """
        QObject.__init__(self, parent)
        
        self.__mw = mw
    
    @pyqtSlot(str, result = str)
    def translate(self, trans):
        """
        Public method to translate the given string.
        
        @param trans string to be translated (string)
        @return translation (string)
        """
        if trans == "QT_LAYOUT_DIRECTION":
            # special handling to detect layout direction
            if qApp.isLeftToRight():
                return "LTR"
            else:
                return "RTL"
        
        return self.trUtf8(trans)
    
    @pyqtSlot(result = str)
    def providerString(self):
        """
        Public method to get a string for the search provider.
        
        @return string for the search provider (string)
        """
        return self.trUtf8("Search results provided by {0}")\
            .format(self.__mw.openSearchManager().currentEngineName())
    
    @pyqtSlot(str, result = str)
    def searchUrl(self, searchStr):
        """
        Public method to get the search URL for the given search term.
        
        @param searchStr search term (string)
        @return search URL (string)
        """
        return bytes(
            self.__mw.openSearchManager().currentEngine()\
            .searchUrl(searchStr).toEncoded()).decode()

##########################################################################################

class HelpWebPage(QWebPage):
    """
    Class implementing an enhanced web page.
    """
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent parent widget of this window (QWidget)
        """
        QWebPage.__init__(self, parent)
        
        self.__lastRequest = None
        self.__lastRequestType = QWebPage.NavigationTypeOther
        
        self.__proxy = NetworkAccessManagerProxy(self)
        self.__proxy.setWebPage(self)
        self.__proxy.setPrimaryNetworkAccessManager(
            Helpviewer.HelpWindow.HelpWindow.networkAccessManager())
        self.setNetworkAccessManager(self.__proxy)
    
    def acceptNavigationRequest(self, frame, request, type_):
        """
        Protected method to determine, if a request may be accepted.
        
        @param frame reference to the frame sending the request (QWebFrame)
        @param request reference to the request object (QNetworkRequest)
        @param type_ type of the navigation request (QWebPage.NavigationType)
        @return flag indicating acceptance (boolean)
        """
        self.__lastRequest = request
        self.__lastRequestType = type_
        
        return QWebPage.acceptNavigationRequest(self, frame, request, type_)
    
    def populateNetworkRequest(self, request):
        """
        Public method to add data to a network request.
        
        @param request reference to the network request object (QNetworkRequest)
        """
        request.setAttribute(QNetworkRequest.User + 100, self)
        request.setAttribute(QNetworkRequest.User + 101, self.__lastRequestType)
    
    def pageAttributeId(self):
        """
        Public method to get the attribute id of the page attribute.
        
        @return attribute id of the page attribute (integer)
        """
        return QNetworkRequest.User + 100
    
    def supportsExtension(self, extension):
        """
        Public method to check the support for an extension.
        
        @param extension extension to test for (QWebPage.Extension)
        @return flag indicating the support of extension (boolean)
        """
        try:
            if extension == QWebPage.ErrorPageExtension:
                return True
        except AttributeError:
            pass
        
        return QWebPage.supportsExtension(self, extension)
    
    def extension(self, extension, option, output):
        """
        Public method to implement a specific extension.
        
        @param extension extension to be executed (QWebPage.Extension)
        @param option provides input to the extension (QWebPage.ExtensionOption)
        @param output stores the output results (QWebPage.ExtensionReturn)
        @return flag indicating a successful call of the extension (boolean)
        """
        try:
            if extension == QWebPage.ErrorPageExtension:
                info = sip.cast(option, QWebPage.ErrorPageExtensionOption)
                errorPage = sip.cast(output, QWebPage.ErrorPageExtensionReturn)
                urlString = bytes(info.url.toEncoded()).decode()
                html = notFoundPage_html
                title = self.trUtf8("Error loading page: {0}").format(urlString)
                pixmap = qApp.style()\
                         .standardIcon(QStyle.SP_MessageBoxWarning, None, self.parent())\
                         .pixmap(32, 32)
                imageBuffer = QBuffer()
                imageBuffer.open(QIODevice.ReadWrite)
                if pixmap.save(imageBuffer, "PNG"):
                    html = html.replace("IMAGE_BINARY_DATA_HERE", 
                                 str(imageBuffer.buffer().toBase64(), encoding="ascii"))
                errorPage.content = QByteArray(html.format(
                    title, 
                    info.errorString, 
                    self.trUtf8("When connecting to: {0}.").format(urlString), 
                    self.trUtf8("Check the address for errors such as "
                                "<b>ww</b>.example.org instead of "
                                "<b>www</b>.example.org"), 
                    self.trUtf8("If the address is correct, try checking the network "
                                "connection."), 
                    self.trUtf8("If your computer or network is protected by a firewall "
                                "or proxy, make sure that the browser is permitted to "
                                "access the network.")
                ).encode("utf8"))
                return True
        except AttributeError:
            pass
        
        return QWebPage.extension(self, extension, option, output)
    
    def userAgent(self, resolveEmpty = False):
        """
        Public method to get the current user agent setting.
        
        @param resolveEmpty flag indicating to resolve an empty 
            user agent (boolean)
        @return user agent string (string)
        """
        agent = Preferences.getHelp("UserAgent")
        if agent == "" and resolveEmpty:
            agent = self.userAgentForUrl(QUrl())
        return agent
    
    def setUserAgent(self, agent):
        """
        Public method to set the current user agent string.
        
        @param agent new current user agent string (string)
        """
        Preferences.setHelp("UserAgent", agent)
    
    def userAgentForUrl(self, url):
        """
        Protected method to determine the user agent for the given URL.
        
        @param url URL to determine user agent for (QUrl)
        @return user agent string (string)
        """
        agent = Preferences.getHelp("UserAgent")
        if agent == "":
            agent = QWebPage.userAgentForUrl(self, url)
        return agent

##########################################################################################

class HelpBrowser(QWebView):
    """
    Class implementing the helpbrowser widget.
    
    This is a subclass of the Qt QWebView to implement an
    interface compatible with the QTextBrowser based variant.
    
    @signal sourceChanged(QUrl) emitted after the current URL has changed
    @signal forwardAvailable(bool) emitted after the current URL has changed
    @signal backwardAvailable(bool) emitted after the current URL has changed
    @signal highlighted(str) emitted, when the mouse hovers over a link
    @signal search(QUrl) emitted, when a search is requested
    """
    sourceChanged = pyqtSignal(QUrl)
    forwardAvailable = pyqtSignal(bool)
    backwardAvailable = pyqtSignal(bool)
    highlighted = pyqtSignal(str)
    search = pyqtSignal(QUrl)
    
    def __init__(self, parent = None, name = ""):
        """
        Constructor
        
        @param parent parent widget of this window (QWidget)
        @param name name of this window (string)
        """
        QWebView.__init__(self, parent)
        self.setObjectName(name)
        self.setWhatsThis(self.trUtf8(
                """<b>Help Window</b>"""
                """<p>This window displays the selected help information.</p>"""
        ))
        
        self.__page = HelpWebPage(self)
        self.setPage(self.__page)
        
        self.mw = parent
        self.ctrlPressed = False
        self.__downloadWindows = []
        self.__isLoading = False
        
        self.__currentZoom = 100
        self.__zoomLevels = [
            30, 50, 67, 80, 90, 
            100, 
            110, 120, 133, 150, 170, 200, 240, 300, 
        ]
        
        self.__javaScriptBinding = None
        self.__javaScriptEricObject = None
        
        self.mw.zoomTextOnlyChanged.connect(self.__applyZoom)
        
        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.linkClicked.connect(self.setSource)
        self.iconChanged.connect(self.__iconChanged)
        
        self.urlChanged.connect(self.__urlChanged)
        self.statusBarMessage.connect(self.__statusBarMessage)
        self.page().linkHovered.connect(self.__linkHovered)
        
        self.loadStarted.connect(self.__loadStarted)
        self.loadProgress.connect(self.__loadProgress)
        self.loadFinished.connect(self.__loadFinished)
        
        self.page().setForwardUnsupportedContent(True)
        self.page().unsupportedContent.connect(self.__unsupportedContent)
        
        self.page().downloadRequested.connect(self.__downloadRequested)
        self.page().frameCreated.connect(self.__addExternalBinding)
        self.__addExternalBinding(self.page().mainFrame())
        
        self.page().databaseQuotaExceeded.connect(self.__databaseQuotaExceeded)
        
        self.mw.openSearchManager().currentEngineChanged.connect(
            self.__currentEngineChanged)
    
    def __addExternalBinding(self, frame = None):
        """
        Private slot to add javascript bindings for adding search providers.
        
        @param frame reference to the web frame (QWebFrame)
        """
        if not hasattr(QtWebKit, 'QWebElement'):
            # test this only for Qt < 4.6.0
            if not QWebSettings.globalSettings()\
                        .testAttribute(QWebSettings.JavascriptEnabled):
                return
        
        self.page().settings().setAttribute(QWebSettings.JavascriptEnabled, True)
        if self.__javaScriptBinding is None:
            self.__javaScriptBinding = JavaScriptExternalObject(self.mw, self)
        
        if frame is None:
            # called from QWebFrame.javaScriptWindowObjectCleared
            frame = self.sender()
            if frame.url().scheme() == "pyrc" and frame.url().path() == "home":
                if self.__javaScriptEricObject is None:
                    self.__javaScriptEricObject = JavaScriptEricObject(self.mw, self)
                frame.addToJavaScriptWindowObject("eric", self.__javaScriptEricObject)
        else:
            # called from QWebPage.frameCreated
            frame.javaScriptWindowObjectCleared.connect(self.__addExternalBinding)
        frame.addToJavaScriptWindowObject("external", self.__javaScriptBinding)
    
    def linkedResources(self, relation = ""):
        """
        Public method to extract linked resources.
        
        @param relation relation to extract (string)
        @return list of linked resources (list of LinkedResource)
        """
        resources = []
        
        if hasattr(QtWebKit, 'QWebElement'):
            baseUrl = self.page().mainFrame().baseUrl()
            
            linkElements = self.page().mainFrame().findAllElements("html > head > link")
            
            for linkElement in linkElements.toList():
                rel = linkElement.attribute("rel")
                href = linkElement.attribute("href")
                type_ = linkElement.attribute("type")
                title = linkElement.attribute("title")
                
                if href == "" or type_ == "":
                    continue
                if relation and rel != relation:
                    continue
                
                resource = LinkedResource()
                resource.rel = rel
                resource.type_ = type_
                resource.href = baseUrl.resolved(QUrl.fromEncoded(href))
                resource.title = title
                
                resources.append(resource)
        else:
            baseUrlString = self.page().mainFrame().evaluateJavaScript("document.baseURI")
            baseUrl = QUrl.fromEncoded(baseUrlString)
            
            lst = self.page().mainFrame().evaluateJavaScript(fetchLinks_js)
            for m in lst:
                rel = m["rel"]
                type_ = m["type"]
                href = m["href"]
                title =  m["title"]
                
                if href == "" or type_ == "":
                    continue
                if relation and rel != relation:
                    continue
                
                resource = LinkedResource()
                resource.rel = rel
                resource.type_ = type_
                resource.href = baseUrl.resolved(QUrl.fromEncoded(href))
                resource.title = title
                
                resources.append(resource)
        
        return resources
    
    def __currentEngineChanged(self):
        """
        Private slot to track a change of the current search engine.
        """
        if self.url().toString() == "pyrc:home":
            self.reload()
    
    def setSource(self, name):
        """
        Public method used to set the source to be displayed.
        
        @param name filename to be shown (QUrl)
        """
        if name is None or not name.isValid():
            return
        
        if self.ctrlPressed:
            # open in a new window
            self.mw.newTab(name)
            self.ctrlPressed = False
            return
        
        if not name.scheme():
            name.setUrl(Preferences.getHelp("DefaultScheme") + name.toString())
        
        if len(name.scheme()) == 1 or \
           name.scheme() == "file":
            # name is a local file
            if name.scheme() and len(name.scheme()) == 1:
                # it is a local path on win os
                name = QUrl.fromLocalFile(name.toString())
            
            if not QFileInfo(name.toLocalFile()).exists():
                E5MessageBox.critical(self,
                    self.trUtf8("Web Browser"),
                    self.trUtf8("""<p>The file <b>{0}</b> does not exist.</p>""")\
                        .format(name.toLocalFile()))
                return

            if name.toLocalFile().endswith(".pdf") or \
               name.toLocalFile().endswith(".PDF") or \
               name.toLocalFile().endswith(".chm") or \
               name.toLocalFile().endswith(".CHM"):
                started = QDesktopServices.openUrl(name)
                if not started:
                    E5MessageBox.critical(self,
                        self.trUtf8("Web Browser"),
                        self.trUtf8("""<p>Could not start a viewer"""
                        """ for file <b>{0}</b>.</p>""").format(name.path()))
                return
        elif name.scheme() in ["mailto"]:
            started = QDesktopServices.openUrl(name)
            if not started:
                E5MessageBox.critical(self,
                    self.trUtf8("Web Browser"),
                    self.trUtf8("""<p>Could not start an application"""
                    """ for URL <b>{0}</b>.</p>""").format(name.toString()))
            return
        elif name.scheme() == "javascript":
            scriptSource = name.toString()[11:]
            res = self.page().mainFrame().evaluateJavaScript(scriptSource)
            if res:
                self.setHtml(res)
            return
        else:
            if name.toString().endswith(".pdf") or \
               name.toString().endswith(".PDF") or \
               name.toString().endswith(".chm") or \
               name.toString().endswith(".CHM"):
                started = QDesktopServices.openUrl(name)
                if not started:
                    E5MessageBox.critical(self,
                        self.trUtf8("Web Browser"),
                        self.trUtf8("""<p>Could not start a viewer"""
                        """ for file <b>{0}</b>.</p>""").format(name.path()))
                return
        
        self.load(name)

    def source(self):
        """
        Public method to return the URL of the loaded page.
        
        @return URL loaded in the help browser (QUrl)
        """
        return self.url()
    
    def documentTitle(self):
        """
        Public method to return the title of the loaded page.
        
        @return title (string)
        """
        return self.title()
    
    def backward(self):
        """
        Public slot to move backwards in history.
        """
        self.triggerPageAction(QWebPage.Back)
        self.__urlChanged(self.history().currentItem().url())
    
    def forward(self):
        """
        Public slot to move forward in history.
        """
        self.triggerPageAction(QWebPage.Forward)
        self.__urlChanged(self.history().currentItem().url())
    
    def home(self):
        """
        Public slot to move to the first page loaded.
        """
        homeUrl = QUrl(Preferences.getHelp("HomePage"))
        self.setSource(homeUrl)
        self.__urlChanged(self.history().currentItem().url())
    
    def reload(self):
        """
        Public slot to reload the current page.
        """
        self.triggerPageAction(QWebPage.Reload)
    
    def copy(self):
        """
        Public slot to copy the selected text.
        """
        self.triggerPageAction(QWebPage.Copy)
    
    def isForwardAvailable(self):
        """
        Public method to determine, if a forward move in history is possible.
        
        @return flag indicating move forward is possible (boolean)
        """
        return self.history().canGoForward()
    
    def isBackwardAvailable(self):
        """
        Public method to determine, if a backwards move in history is possible.
        
        @return flag indicating move backwards is possible (boolean)
        """
        return self.history().canGoBack()
    
    def __levelForZoom(self, zoom):
        """
        Private method determining the zoom level index given a zoom factor.
        
        @param zoom zoom factor (integer)
        @return index of zoom factor (integer)
        """
        try:
            index = self.__zoomLevels.index(zoom)
        except ValueError:
            for index in range(len(self.__zoomLevels)):
                if zoom <= self.__zoomLevels[index]:
                    break
        return index
    
    def __applyZoom(self):
        """
        Private slot to apply the current zoom factor.
        """
        try:
            self.setZoomFactor(self.__currentZoom / 100.0)
        except AttributeError:
            self.setTextSizeMultiplier(self.__currentZoom / 100.0)
    
    def zoomIn(self):
        """
        Public slot to zoom into the page.
        """
        index = self.__levelForZoom(self.__currentZoom)
        if index < len(self.__zoomLevels) - 1:
            self.__currentZoom = self.__zoomLevels[index + 1]
        self.__applyZoom()
    
    def zoomOut(self):
        """
        Public slot to zoom out of the page.
        """
        index = self.__levelForZoom(self.__currentZoom)
        if index > 0:
            self.__currentZoom = self.__zoomLevels[index - 1]
        self.__applyZoom()
    
    def zoomReset(self): 
        """
        Public method to reset the zoom factor.
        """
        self.__currentZoom = 100
        self.__applyZoom()
    
    def wheelEvent(self, evt):
        """
        Protected method to handle wheel events.
        
        @param evt reference to the wheel event (QWheelEvent)
        """
        if evt.modifiers() & Qt.ControlModifier:
            degrees = evt.delta() // 8
            steps = degrees // 15
            self.__currentZoom += steps * 10
            self.__applyZoom()
            evt.accept()
            return
        
        QWebView.wheelEvent(self, evt)
    
    def hasSelection(self):
        """
        Public method to determine, if there is some text selected.
        
        @return flag indicating text has been selected (boolean)
        """
        return self.selectedText() != ""
    
    def findNextPrev(self, txt, case, backwards, wrap, highlightAll):
        """
        Public slot to find the next occurrence of a text.
        
        @param txt text to search for (string)
        @param case flag indicating a case sensitive search (boolean)
        @param backwards flag indicating a backwards search (boolean)
        @param wrap flag indicating to wrap around (boolean)
        @param highlightAll flag indicating to highlight all occurrences (boolean)
        """
        findFlags = QWebPage.FindFlags()
        if case:
            findFlags |= QWebPage.FindCaseSensitively
        if backwards:
            findFlags |= QWebPage.FindBackward
        if wrap:
            findFlags |= QWebPage.FindWrapsAroundDocument
        try:
            if highlightAll:
                findFlags |= QWebPage.HighlightAllOccurrences
        except AttributeError:
            pass
        
        return self.findText(txt, findFlags)
    
    def contextMenuEvent(self, evt):
        """
        Protected method called to create a context menu.
        
        This method is overridden from QWebView.
        
        @param evt reference to the context menu event object (QContextMenuEvent)
        """
        menu = QMenu(self)
        
        hit = self.page().mainFrame().hitTestContent(evt.pos())
        if not hit.linkUrl().isEmpty():
            act = menu.addAction(self.trUtf8("Open Link in New Tab\tCtrl+LMB"),
                self.__openLinkInNewTab)
            act.setData(hit.linkUrl())
            menu.addSeparator()
            menu.addAction(self.trUtf8("Save Lin&k"), self.__downloadLink)
            act = menu.addAction(self.trUtf8("Bookmark this Link"), self.__bookmarkLink)
            act.setData(hit.linkUrl())
            menu.addSeparator()
            menu.addAction(self.trUtf8("Copy Link to Clipboard"), self.__copyLink)
        
        if not hit.imageUrl().isEmpty():
            if not menu.isEmpty():
                menu.addSeparator()
            act = menu.addAction(self.trUtf8("Open Image in New Tab"), 
                self.__openLinkInNewTab)
            act.setData(hit.imageUrl())
            menu.addSeparator()
            menu.addAction(self.trUtf8("Save Image"), self.__downloadImage)
            menu.addAction(self.trUtf8("Copy Image to Clipboard"), self.__copyImage)
            act = menu.addAction(self.trUtf8("Copy Image Location to Clipboard"), 
                self.__copyImageLocation)
            act.setData(hit.imageUrl().toString())
            menu.addSeparator()
            act = menu.addAction(self.trUtf8("Block Image"), self.__blockImage)
            act.setData(hit.imageUrl().toString())
        
        if not menu.isEmpty():
            menu.addSeparator()
        menu.addAction(self.mw.newTabAct)
        menu.addAction(self.mw.newAct)
        menu.addSeparator()
        menu.addAction(self.mw.saveAsAct)
        menu.addSeparator()
        menu.addAction(self.trUtf8("Bookmark this Page"), self.__addBookmark)
        menu.addSeparator()
        menu.addAction(self.mw.backAct)
        menu.addAction(self.mw.forwardAct)
        menu.addAction(self.mw.homeAct)
        menu.addSeparator()
        menu.addAction(self.mw.zoomInAct)
        menu.addAction(self.mw.zoomOutAct)
        menu.addSeparator()
        if self.selectedText():
            menu.addAction(self.mw.copyAct)
        menu.addAction(self.mw.findAct)
        menu.addSeparator()
        if self.selectedText():
            self.__searchMenu = menu.addMenu(self.trUtf8("Search with..."))
            
            engineNames = self.mw.openSearchManager().allEnginesNames()
            for engineName in engineNames:
                engine = self.mw.openSearchManager().engine(engineName)
                act = OpenSearchEngineAction(engine, self.__searchMenu)
                self.__searchMenu.addAction(act)
                act.setData(engineName)
            self.__searchMenu.triggered.connect(self.__searchRequested)
            
            menu.addSeparator()
        
        if hasattr(QtWebKit, 'QWebElement'):
            element = hit.element()
            if not element.isNull() and \
               element.tagName().lower() == "input" and \
               element.attribute("type", "text") == "text":
                act = menu.addAction(self.trUtf8("Add to web search toolbar"), 
                                     self.__addSearchEngine)
                act.setData(element)
                menu.addSeparator()
        
        menu.addAction(self.trUtf8("Web Inspector..."), self.__webInspector)
        
        menu.exec_(evt.globalPos())
    
    def __openLinkInNewTab(self):
        """
        Private method called by the context menu to open a link in a new window.
        """
        act = self.sender()
        url = act.data()
        if url.isEmpty():
            return
        
        oldCtrlPressed = self.ctrlPressed
        self.ctrlPressed = True
        self.setSource(url)
        self.ctrlPressed = oldCtrlPressed
    
    def __bookmarkLink(self):
        """
        Private slot to bookmark a link via the context menu.
        """
        act = self.sender()
        url = act.data()
        if url.isEmpty():
            return
        
        dlg = AddBookmarkDialog()
        dlg.setUrl(bytes(url.toEncoded()).decode())
        dlg.exec_()
    
    def __downloadLink(self):
        """
        Private slot to download a link and save it to disk.
        """
        self.pageAction(QWebPage.DownloadLinkToDisk).trigger()
    
    def __copyLink(self):
        """
        Private slot to copy a link to the clipboard.
        """
        self.pageAction(QWebPage.CopyLinkToClipboard).trigger()
    
    def __downloadImage(self):
        """
        Private slot to download an image and save it to disk.
        """
        self.pageAction(QWebPage.DownloadImageToDisk).trigger()
    
    def __copyImage(self):
        """
        Private slot to copy an image to the clipboard.
        """
        self.pageAction(QWebPage.CopyImageToClipboard).trigger()
    
    def __copyImageLocation(self):
        """
        Private slot to copy an image location to the clipboard.
        """
        act = self.sender()
        url = act.data()
        QApplication.clipboard().setText(url)
    
    def __blockImage(self):
        """
        Private slot to add a block rule for an image URL.
        """
        act = self.sender()
        url = act.data()
        dlg = Helpviewer.HelpWindow.HelpWindow.adblockManager().showDialog()
        dlg.addCustomRule(url)
    
    def __searchRequested(self, act):
        """
        Private slot to search for some text with a selected search engine.
        
        @param act reference to the action that triggered this slot (QAction)
        """
        searchText = self.selectedText()
        
        if not searchText:
            return
        
        engineName = act.data()
        if engineName:
            engine = self.mw.openSearchManager().engine(engineName)
            self.search.connect(engine.searchUrl(searchText))
    
    def __addSearchEngine(self):
        """
        Private slot to add a new search engine.
        """
        act = self.sender()
        if act is None:
            return
        
        element = act.data()
        elementName = element.attribute("name")
        formElement = QWebElement(element)
        while formElement.tagName().lower() != "form":
            formElement = formElement.parent()
        
        if formElement.isNull() or \
           formElement.attribute("action") == "":
            return
        
        method = formElement.attribute("method", "get").lower()
        if method != "get":
            QMessageBox.warning(self,
                self.trUtf8("Method not supported"),
                self.trUtf8("""{0} method is not supported.""").format(method.upper()))
            return
        
        searchUrl = QUrl(self.page().mainFrame().baseUrl().resolved(
            QUrl(formElement.attribute("action"))))
        if searchUrl.scheme() != "http":
            return
        
        searchEngines = {}
        inputFields = formElement.findAll("input")
        for inputField in inputFields.toList():
            type_ = inputField.attribute("type", "text")
            name = inputField.attribute("name")
            value = inputField.evaluateJavaScript("this.value")
            
            if type_ == "submit":
                searchEngines[value] = name
            elif type_ == "text":
                if inputField == element:
                    value = "{searchTerms}"
                searchUrl.addQueryItem(name, value)
            elif type_ == "checkbox" or type_ == "radio":
                if inputField.evaluateJavaScript("this.checked"):
                    searchUrl.addQueryItem(name, value)
            elif type_ == "hidden":
                searchUrl.addQueryItem(name, value)
        
        selectFields = formElement.findAll("select")
        for selectField in selectFields.toList():
            name = selectField.attribute("name")
            selectedIndex = selectField.evaluateJavaScript("this.selectedIndex")
            if selectedIndex == -1:
                continue
            
            options = selectField.findAll("option")
            value = options.at(selectedIndex).toPlainText()
            searchUrl.addQueryItem(name, value)
        
        ok = True
        if len(searchEngines) > 1:
            searchEngine, ok = QInputDialog.getItem(
                self, 
                self.trUtf8("Search engine"), 
                self.trUtf8("Choose the desired search engine"), 
                sorted(searchEngines.keys()), 0, False)
            
            if not ok:
                return
            
            if searchEngines[searchEngine] != "":
                searchUrl.addQueryItem(searchEngines[searchEngine], searchEngine)
        
        engineName = ""
        labels = formElement.findAll('label[for="{0}"]'.format(elementName))
        if labels.count() > 0:
            engineName = labels.at(0).toPlainText()
        
        engineName, ok = QInputDialog.getText(
            self,
            self.trUtf8("Engine name"),
            self.trUtf8("Enter a name for the engine"),
            QLineEdit.Normal,
            engineName)
        if not ok:
            return
        
        engine = OpenSearchEngine()
        engine.setName(engineName)
        engine.setDescription(engineName)
        engine.setSearchUrlTemplate(searchUrl.toString())
        engine.setImage(self.icon().pixmap(16, 16).toImage())
        
        self.mw.openSearchManager().addEngine(engine)
    
    def __webInspector(self):
        """
        Private slot to show the web inspector window.
        """
        self.triggerPageAction(QWebPage.InspectElement)
    
    def __addBookmark(self):
        """
        Private slot to bookmark the current link.
        """
        dlg = AddBookmarkDialog()
        dlg.setUrl(bytes(self.url().toEncoded()).decode())
        dlg.setTitle(self.title())
        dlg.exec_()
    
    def keyPressEvent(self, evt):
        """
        Protected method called by a key press.
        
        This method is overridden from QTextBrowser.
        
        @param evt the key event (QKeyEvent)
        """
        self.ctrlPressed = (evt.key() == Qt.Key_Control)
        QWebView.keyPressEvent(self, evt)
    
    def keyReleaseEvent(self, evt):
        """
        Protected method called by a key release.
        
        This method is overridden from QTextBrowser.
        
        @param evt the key event (QKeyEvent)
        """
        self.ctrlPressed = False
        QWebView.keyReleaseEvent(self, evt)
    
    def clearHistory(self):
        """
        Public slot to clear the history.
        """
        self.history().clear()
        self.__urlChanged(self.history().currentItem().url())
    
    ############################################################################
    ## Signal converters below
    ############################################################################
    
    def __urlChanged(self, url):
        """
        Private slot to handle the urlChanged signal.
        
        @param url the new url (QUrl)
        """
        self.sourceChanged.emit(url)
        
        self.forwardAvailable.emit(self.isForwardAvailable())
        self.backwardAvailable.emit(self.isBackwardAvailable())
    
    def __statusBarMessage(self, text):
        """
        Private slot to handle the statusBarMessage signal.
        
        @param text text to be shown in the status bar (string)
        """
        self.mw.statusBar().showMessage(text)
    
    def __linkHovered(self, link,  title, textContent):
        """
        Private slot to handle the linkHovered signal.
        
        @param link the URL of the link (string)
        @param title the link title (string)
        @param textContent text content of the link (string)
        """
        self.highlighted.emit(link)
    
    ############################################################################
    ## Signal handlers below
    ############################################################################
    
    def __loadStarted(self):
        """
        Private method to handle the loadStarted signal.
        """
        self.__isLoading = True
        self.mw.setLoading(self)
        self.mw.progressBar().show()
    
    def __loadProgress(self, progress):
        """
        Private method to handle the loadProgress signal.
        
        @param progress progress value (integer)
        """
        self.mw.progressBar().setValue(progress)
    
    def __loadFinished(self, ok):
        """
        Private method to handle the loadFinished signal.
        
        @param ok flag indicating the result (boolean)
        """
        self.__isLoading = False
        self.mw.progressBar().hide()
        self.mw.resetLoading(self, ok)
        
        self.__iconChanged()
        
        if ok:
            self.mw.adblockManager().page().applyRulesToPage(self.page())
            self.mw.passwordManager().fill(self.page())
    
    def isLoading(self):
        """
        Public method to get the loading state.
        
        @return flag indicating the loading state (boolean)
        """
        return self.__isLoading
    
    def saveAs(self):
        """
        Public method to save the current page to a file.
        """
        url = self.url()
        if url.isEmpty():
            return
        
        req = QNetworkRequest(url)
        reply = self.mw.networkAccessManager().get(req)
        self.__unsupportedContent(reply, True, True)
    
    def __unsupportedContent(self, reply, requestFilename = None, download = False):
        """
        Private slot to handle the unsupportedContent signal.
        
        @param reply reference to the reply object (QNetworkReply)
        @keyparam requestFilename indicating to ask for a filename 
            (boolean or None). If it is None, the behavior is determined
            by a configuration option.
        @keyparam download flag indicating a download operation (boolean)
        """
        if reply is None:
            return
        
        replyUrl = reply.url()
        
        if replyUrl.scheme() == "abp":
            return
        
        if reply.error() == QNetworkReply.NoError:
            if reply.url().isEmpty():
                return
            size = reply.header(QNetworkRequest.ContentLengthHeader)
            if size == 0:
                return
            
            if requestFilename is None:
                requestFilename = Preferences.getUI("RequestDownloadFilename")
            dlg = DownloadDialog(reply, requestFilename, self.page(), download)
            if dlg.initialize():
                dlg.done[()].connect(self.__downloadDone)
                self.__downloadWindows.append(dlg)
                dlg.show()
            self.setUrl(self.url())
        else:
            replyUrl = reply.url()
            if replyUrl.isEmpty():
                return
            
            html = notFoundPage_html
            urlString = bytes(replyUrl.toEncoded()).decode()
            title = self.trUtf8("Error loading page: {0}").format(urlString)
            pixmap = qApp.style()\
                     .standardIcon(QStyle.SP_MessageBoxWarning, None, self)\
                     .pixmap(32, 32)
            imageBuffer = QBuffer()
            imageBuffer.open(QIODevice.ReadWrite)
            if pixmap.save(imageBuffer, "PNG"):
                html = html.replace("IMAGE_BINARY_DATA_HERE", 
                             str(imageBuffer.buffer().toBase64(), encoding="ascii"))
            html = html.format(
                title, 
                reply.errorString(), 
                self.trUtf8("When connecting to: {0}.").format(urlString), 
                self.trUtf8("Check the address for errors such as <b>ww</b>.example.org "
                            "instead of <b>www</b>.example.org"), 
                self.trUtf8("If the address is correct, try checking the network "
                            "connection."), 
                self.trUtf8("If your computer or network is protected by a firewall or "
                            "proxy, make sure that the browser is permitted to access "
                            "the network.")
            )
            self.setHtml(html, replyUrl)
            self.mw.historyManager().removeHistoryEntry(replyUrl, self.title())
            self.loadFinished.emit(False)
    
    def __downloadDone(self):
        """
        Private slot to handle the done signal of the download dialogs.
        """
        dlg = self.sender()
        if dlg in self.__downloadWindows:
            dlg.done[()].disconnect(self.__downloadDone)
    
    def __downloadRequested(self, request):
        """
        Private slot to handle a download request.
        
        @param request reference to the request object (QNetworkRequest)
        """
        if request.url().isEmpty():
            return
        mgr = self.page().networkAccessManager()
        self.__unsupportedContent(mgr.get(request), download = True)
    
    def __iconChanged(self):
        """
        Private slot to handle the icon change.
        """
        self.mw.iconChanged(self.icon())
    
    def __databaseQuotaExceeded(self, frame, databaseName):
        """
        Private slot to handle the case, where the database quota is exceeded.
        
        @param frame reference to the frame (QWebFrame)
        @param databaseName name of the web database (string)
        """
        securityOrigin = frame.securityOrigin()
        if securityOrigin.databaseQuota() > 0 and \
           securityOrigin.databaseUsage() == 0:
            # cope with a strange behavior of Qt 4.6, if a database is
            # accessed for the first time
            return
        
        res = E5MessageBox.question(self,
            self.trUtf8("Web Database Quota"),
            self.trUtf8("""<p>The database quota of <strong>{0}</strong> has"""
                        """ been exceeded while accessing database <strong>{1}"""
                        """</strong>.</p><p>Shall it be changed?</p>""")\
                .format(self.__dataString(securityOrigin.databaseQuota()), databaseName),
            QMessageBox.StandardButtons(\
                QMessageBox.No | \
                QMessageBox.Yes),
            QMessageBox.Yes)
        if res == QMessageBox.Yes:
            newQuota, ok = QInputDialog.getInteger(\
                self,
                self.trUtf8("New Web Database Quota"),
                self.trUtf8("Enter the new quota in MB (current = {0}, used = {1}; "
                            "step size = 5 MB):"\
                    .format(self.__dataString(securityOrigin.databaseQuota()), 
                            self.__dataString(securityOrigin.databaseUsage()))),
                securityOrigin.databaseQuota() // (1024 * 1024), 0, 2147483647, 5)
            if ok:
                securityOrigin.setDatabaseQuota(newQuota * 1024 * 1024)
    
    def __dataString(self, size):
        """
        Private method to generate a formatted data string.
        
        @param size size to be formatted (integer)
        @return formatted data string (string)
        """
        unit = ""
        if size < 1024:
            unit = self.trUtf8("bytes")
        elif size < 1024 * 1024:
            size /= 1024
            unit = self.trUtf8("kB")
        else:
            size /= 1024 * 1024
            unit = self.trUtf8("MB")
        return "{0:.1f} {1}".format(size, unit)
    
    ############################################################################
    ## Miscellaneous methods below
    ############################################################################
    
    def createWindow(self, windowType):
        """
        Protected method called, when a new window should be created.
        
        @param windowType type of the requested window (QWebPage.WebWindowType)
        """
        self.mw.newTab()
        return self.mw.currentBrowser()
    
    def preferencesChanged(self):
        """
        Public method to indicate a change of the settings.
        """
        self.reload()