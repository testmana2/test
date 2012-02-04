# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#


"""
Module implementing the helpbrowser using QWebView.
"""

from PyQt4.QtCore import pyqtSlot, pyqtSignal, QObject, QT_TRANSLATE_NOOP, QUrl, \
    QBuffer, QIODevice, QByteArray, QFileInfo, Qt, QTimer, QEvent, QRect
from PyQt4.QtGui import qApp, QDesktopServices, QStyle, QMenu, QApplication, \
    QInputDialog, QLineEdit, QClipboard, QMouseEvent, QLabel, QToolTip, QColor, \
    QPalette, QFrame, QPrinter, QPrintDialog, QDialog
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
import UI.PixmapCache

from .Bookmarks.AddBookmarkDialog import AddBookmarkDialog
from .JavaScriptResources import fetchLinks_js
from .HTMLResources import notFoundPage_html
try:
    from .SslInfoDialog import SslInfoDialog
    from PyQt4.QtNetwork import QSslCertificate
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False
import Helpviewer.HelpWindow
from .HelpLanguagesDialog import HelpLanguagesDialog

from .Network.NetworkAccessManagerProxy import NetworkAccessManagerProxy

from .OpenSearch.OpenSearchEngineAction import OpenSearchEngineAction
from .OpenSearch.OpenSearchEngine import OpenSearchEngine

##########################################################################################


class JavaScriptExternalObject(QObject):
    """
    Class implementing an external javascript object to add search providers.
    """
    def __init__(self, mw, parent=None):
        """
        Constructor
        
        @param mw reference to the main window 8HelpWindow)
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__mw = mw
    
    @pyqtSlot(str)
    def AddSearchProvider(self, url):
        """
        Public slot to add a search provider.
        
        @param url url of the XML file defining the search provider (string)
        """
        self.__mw.openSearchManager().addEngine(QUrl(url))


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
        QT_TRANSLATE_NOOP("JavaScriptEricObject", "Welcome to eric5 Web Browser!"),
        QT_TRANSLATE_NOOP("JavaScriptEricObject", "eric5 Web Browser"),
        QT_TRANSLATE_NOOP("JavaScriptEricObject", "Search!"),
        QT_TRANSLATE_NOOP("JavaScriptEricObject", "About eric5"),
    ]
    
    def __init__(self, mw, parent=None):
        """
        Constructor
        
        @param mw reference to the main window 8HelpWindow)
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__mw = mw
    
    @pyqtSlot(str, result=str)
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
    
    @pyqtSlot(result=str)
    def providerString(self):
        """
        Public method to get a string for the search provider.
        
        @return string for the search provider (string)
        """
        return self.trUtf8("Search results provided by {0}")\
            .format(self.__mw.openSearchManager().currentEngineName())
    
    @pyqtSlot(str, result=str)
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
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent parent widget of this window (QWidget)
        """
        super().__init__(parent)
        
        self.__lastRequest = None
        self.__lastRequestType = QWebPage.NavigationTypeOther
        
        self.__proxy = NetworkAccessManagerProxy(self)
        self.__proxy.setWebPage(self)
        self.__proxy.setPrimaryNetworkAccessManager(
            Helpviewer.HelpWindow.HelpWindow.networkAccessManager())
        self.setNetworkAccessManager(self.__proxy)
        
        self.__sslConfiguration = None
        self.__proxy.finished.connect(self.__managerFinished)
    
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
        
        scheme = request.url().scheme()
        if scheme == "mailto":
            QDesktopServices.openUrl(request.url())
            return False
        
        if type_ == QWebPage.NavigationTypeFormResubmitted:
            res = E5MessageBox.yesNo(self.view(),
                self.trUtf8("Resending POST request"),
                self.trUtf8("""In order to display the site, the request along with"""
                            """ all the data must be sent once again, which may lead"""
                            """ to some unexpected behaviour of the site e.g. the"""
                            """ same action might be performed once again. Do you want"""
                            """ to continue anyway?"""),
                icon=E5MessageBox.Warning)
            if not res:
                return False
        
        return QWebPage.acceptNavigationRequest(self, frame, request, type_)
    
    def populateNetworkRequest(self, request):
        """
        Public method to add data to a network request.
        
        @param request reference to the network request object (QNetworkRequest)
        """
        try:
            request.setAttribute(QNetworkRequest.User + 100, self)
            request.setAttribute(QNetworkRequest.User + 101, self.__lastRequestType)
        except TypeError:
            pass
    
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
                if info.error == 102:
                    # this is something of a hack; hopefully it will work in the future
                    return False
                
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
                                "access the network."),
                    self.trUtf8("If your cache policy is set to offline browsing,"
                                "only pages in the local cache are available.")
                ).encode("utf8"))
                return True
        except AttributeError:
            pass
        
        return QWebPage.extension(self, extension, option, output)
    
    def userAgent(self, resolveEmpty=False):
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
    
    def __managerFinished(self, reply):
        """
        Private slot to handle a finished reply.
        
        This slot is used to get SSL related information for a reply.
        
        @param reply reference to the finished reply (QNetworkReply)
        """
        try:
            frame = reply.request().originatingObject()
        except AttributeError:
            frame = None
        
        mainFrameRequest = frame == self.mainFrame()
        
        if mainFrameRequest and \
           self.__sslConfiguration is not None and \
           reply.url() == self.mainFrame().url():
            self.__sslConfiguration = None
        
        if reply.error() == QNetworkReply.NoError and \
           mainFrameRequest and \
           self.__sslConfiguration is None and \
           reply.url().scheme().lower() == "https" and \
           reply.url() == self.mainFrame().url():
            self.__sslConfiguration = reply.sslConfiguration()
            self.__sslConfiguration.url = QUrl(reply.url())
    
    def getSslInfo(self):
        """
        Public method to get a reference to the SSL info object.
        
        @return reference to the SSL info (QSslCertificate)
        """
        if self.__sslConfiguration is None:
            return None
        
        sslInfo = self.__sslConfiguration.peerCertificate()
        sslInfo.url = QUrl(self.__sslConfiguration.url)
        return sslInfo
    
    def showSslInfo(self):
        """
        Public slot to show some SSL information for the loaded page.
        """
        if SSL_AVAILABLE and self.__sslConfiguration is not None:
            dlg = SslInfoDialog(self.getSslInfo(), self.view())
            dlg.exec_()
        else:
            E5MessageBox.warning(self.view(),
                self.trUtf8("SSL Certificate Info"),
                self.trUtf8("""There is no SSL Certificate Info available."""))
    
    def hasValidSslInfo(self):
        """
        Public method to check, if the page has a valid SSL certificate.
        
        @return flag indicating a valid SSL certificate (boolean)
        """
        if self.__sslConfiguration is None:
            return False
        
        certList = self.__sslConfiguration.peerCertificateChain()
        if not certList:
            return False
        
        certificateDict = Preferences.toDict(
                Preferences.Prefs.settings.value("Help/CaCertificatesDict"))
        for server in certificateDict:
            localCAList = QSslCertificate.fromData(certificateDict[server])
            for cert in certList:
                if cert in localCAList:
                    return True
        
        for cert in certList:
            if not cert.isValid():
                return False
        
        return True

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
    
    def __init__(self, mainWindow, parent=None, name=""):
        """
        Constructor
        
        @param mainWindow reference to the main window (HelpWindow)
        @param parent parent widget of this window (QWidget)
        @param name name of this window (string)
        """
        super().__init__(parent)
        self.setObjectName(name)
        self.setWhatsThis(self.trUtf8(
                """<b>Help Window</b>"""
                """<p>This window displays the selected help information.</p>"""
        ))
        
        self.__page = HelpWebPage(self)
        self.setPage(self.__page)
        
        self.mw = mainWindow
        self.ctrlPressed = False
        self.__isLoading = False
        self.__progress = 0
        
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
        
        self.setAcceptDrops(True)
        
        if hasattr(QtWebKit, 'QWebElement'):
            self.__enableAccessKeys = Preferences.getHelp("AccessKeysEnabled")
            self.__accessKeysPressed = False
            self.__accessKeyLabels = []
            self.__accessKeyNodes = {}
            
            self.page().loadStarted.connect(self.__hideAccessKeys)
            self.page().scrollRequested.connect(self.__hideAccessKeys)
        
        self.__rss = []
        
        self.__clickedFrame = None
        
        self.grabGesture(Qt.PinchGesture)
    
    def __addExternalBinding(self, frame=None):
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
            if isinstance(frame, HelpWebPage):
                frame = frame.mainFrame()
            if frame.url().scheme() == "pyrc" and frame.url().path() == "home":
                if self.__javaScriptEricObject is None:
                    self.__javaScriptEricObject = JavaScriptEricObject(self.mw, self)
                frame.addToJavaScriptWindowObject("eric", self.__javaScriptEricObject)
        else:
            # called from QWebPage.frameCreated
            frame.javaScriptWindowObjectCleared.connect(self.__addExternalBinding)
        frame.addToJavaScriptWindowObject("external", self.__javaScriptBinding)
    
    def linkedResources(self, relation=""):
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
                title = m["title"]
                
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
                    self.trUtf8("eric5 Web Browser"),
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
                        self.trUtf8("eric5 Web Browser"),
                        self.trUtf8("""<p>Could not start a viewer"""
                        """ for file <b>{0}</b>.</p>""").format(name.path()))
                return
        elif name.scheme() in ["mailto"]:
            started = QDesktopServices.openUrl(name)
            if not started:
                E5MessageBox.critical(self,
                    self.trUtf8("eric5 Web Browser"),
                    self.trUtf8("""<p>Could not start an application"""
                    """ for URL <b>{0}</b>.</p>""").format(name.toString()))
            return
        elif name.scheme() == "javascript":
            scriptSource = QUrl.fromPercentEncoding(name.toString(
                QUrl.FormattingOptions(QUrl.TolerantMode | QUrl.RemoveScheme)))
            self.page().mainFrame().evaluateJavaScript(scriptSource)
            return
        else:
            if name.toString().endswith(".pdf") or \
               name.toString().endswith(".PDF") or \
               name.toString().endswith(".chm") or \
               name.toString().endswith(".CHM"):
                started = QDesktopServices.openUrl(name)
                if not started:
                    E5MessageBox.critical(self,
                        self.trUtf8("eric5 Web Browser"),
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
        
        frameAtPos = self.page().frameAt(evt.pos())
        hit = self.page().mainFrame().hitTestContent(evt.pos())
        if not hit.linkUrl().isEmpty():
            menu.addAction(UI.PixmapCache.getIcon("openNewTab.png"),
                self.trUtf8("Open Link in New Tab\tCtrl+LMB"),
                self.__openLinkInNewTab).setData(hit.linkUrl())
            menu.addSeparator()
            menu.addAction(UI.PixmapCache.getIcon("download.png"),
                self.trUtf8("Save Lin&k"), self.__downloadLink)
            menu.addAction(UI.PixmapCache.getIcon("bookmark22.png"),
                self.trUtf8("Bookmark this Link"), self.__bookmarkLink)\
                .setData(hit.linkUrl())
            menu.addSeparator()
            menu.addAction(UI.PixmapCache.getIcon("editCopy.png"),
                self.trUtf8("Copy Link to Clipboard"), self.__copyLink)
            menu.addAction(UI.PixmapCache.getIcon("mailSend.png"),
                self.trUtf8("Send Link"), self.__sendLink).setData(hit.linkUrl())
            if Preferences.getHelp("VirusTotalEnabled") and \
               Preferences.getHelp("VirusTotalServiceKey") != "":
                menu.addAction(UI.PixmapCache.getIcon("virustotal.png"),
                    self.trUtf8("Scan Link with VirusTotal"), self.__virusTotal)\
                    .setData(hit.linkUrl())
        
        if not hit.imageUrl().isEmpty():
            if not menu.isEmpty():
                menu.addSeparator()
            menu.addAction(UI.PixmapCache.getIcon("openNewTab.png"),
                self.trUtf8("Open Image in New Tab"),
                self.__openLinkInNewTab).setData(hit.imageUrl())
            menu.addSeparator()
            menu.addAction(UI.PixmapCache.getIcon("download.png"),
                self.trUtf8("Save Image"), self.__downloadImage)
            menu.addAction(self.trUtf8("Copy Image to Clipboard"), self.__copyImage)
            menu.addAction(UI.PixmapCache.getIcon("editCopy.png"),
                self.trUtf8("Copy Image Location to Clipboard"),
                self.__copyImageLocation).setData(hit.imageUrl().toString())
            menu.addAction(UI.PixmapCache.getIcon("mailSend.png"),
                self.trUtf8("Send Image Link"), self.__sendLink).setData(hit.imageUrl())
            menu.addSeparator()
            menu.addAction(UI.PixmapCache.getIcon("adBlockPlus.png"),
                self.trUtf8("Block Image"), self.__blockImage)\
                .setData(hit.imageUrl().toString())
            if Preferences.getHelp("VirusTotalEnabled") and \
               Preferences.getHelp("VirusTotalServiceKey") != "":
                menu.addAction(UI.PixmapCache.getIcon("virustotal.png"),
                    self.trUtf8("Scan Image with VirusTotal"), self.__virusTotal)\
                    .setData(hit.imageUrl())
        
        element = hit.element()
        if not element.isNull() and \
           element.tagName().lower() in ["input", "textarea", "video", "audio"]:
            if menu.isEmpty():
                self.page().createStandardContextMenu().exec_(evt.globalPos())
                return
        
        if not menu.isEmpty():
            menu.addSeparator()
        menu.addAction(self.mw.newTabAct)
        menu.addAction(self.mw.newAct)
        menu.addSeparator()
        menu.addAction(self.mw.saveAsAct)
        menu.addSeparator()
        
        if frameAtPos and self.page().mainFrame() != frameAtPos:
            self.__clickedFrame = frameAtPos
            fmenu = QMenu(self.trUtf8("This Frame"))
            frameUrl = self.__clickedFrame.url()
            if frameUrl.isValid():
                fmenu.addAction(self.trUtf8("Show &only this frame"),
                    self.__loadClickedFrame)
                fmenu.addAction(UI.PixmapCache.getIcon("openNewTab.png"),
                    self.trUtf8("Show in new &tab"),
                    self.__openLinkInNewTab).setData(self.__clickedFrame.url())
                fmenu.addSeparator()
            fmenu.addAction(UI.PixmapCache.getIcon("print.png"),
                self.trUtf8("&Print"), self.__printClickedFrame)
            fmenu.addAction(UI.PixmapCache.getIcon("printPreview.png"),
                self.trUtf8("Print Preview"), self.__printPreviewClickedFrame)
            fmenu.addAction(UI.PixmapCache.getIcon("printPdf.png"),
                self.trUtf8("Print as PDF"), self.__printPdfClickedFrame)
            fmenu.addSeparator()
            fmenu.addAction(UI.PixmapCache.getIcon("zoomIn.png"),
                self.trUtf8("Zoom &in"), self.__zoomInClickedFrame)
            fmenu.addAction(UI.PixmapCache.getIcon("zoomReset.png"),
                self.trUtf8("Zoom &reset"), self.__zoomResetClickedFrame)
            fmenu.addAction(UI.PixmapCache.getIcon("zoomOut.png"),
                self.trUtf8("Zoom &out"), self.__zoomOutClickedFrame)
            fmenu.addSeparator()
            fmenu.addAction(self.trUtf8("Show frame so&urce"),
                self.__showClickedFrameSource)
            
            menu.addMenu(fmenu)
            menu.addSeparator()
        
        menu.addAction(UI.PixmapCache.getIcon("bookmark22.png"),
            self.trUtf8("Bookmark this Page"), self.addBookmark)
        menu.addAction(UI.PixmapCache.getIcon("mailSend.png"),
            self.trUtf8("Send Page Link"), self.__sendLink).setData(self.url())
        menu.addSeparator()
        menu.addAction(self.mw.backAct)
        menu.addAction(self.mw.forwardAct)
        menu.addAction(self.mw.homeAct)
        menu.addSeparator()
        menu.addAction(self.mw.zoomInAct)
        menu.addAction(self.mw.zoomResetAct)
        menu.addAction(self.mw.zoomOutAct)
        menu.addSeparator()
        if self.selectedText():
            menu.addAction(self.mw.copyAct)
            menu.addAction(UI.PixmapCache.getIcon("mailSend.png"),
                self.trUtf8("Send Text"), self.__sendLink).setData(self.selectedText())
        menu.addAction(self.mw.findAct)
        menu.addSeparator()
        if self.selectedText():
            self.__searchMenu = menu.addMenu(self.trUtf8("Search with..."))
            
            engineNames = self.mw.openSearchManager().allEnginesNames()
            for engineName in engineNames:
                engine = self.mw.openSearchManager().engine(engineName)
                self.__searchMenu.addAction(
                    OpenSearchEngineAction(engine, self.__searchMenu).setData(engineName))
            self.__searchMenu.triggered.connect(self.__searchRequested)
            
            menu.addSeparator()
            
            languages = Preferences.toList(
                Preferences.Prefs.settings.value("Help/AcceptLanguages",
                    HelpLanguagesDialog.defaultAcceptLanguages()))
            if languages:
                language = languages[0]
                langCode = language.split("[")[1][:2]
                googleTranslatorUrl = QUrl(
                    "http://translate.google.com/#auto|{0}|{1}".format(
                        langCode, self.selectedText()))
                menu.addAction(UI.PixmapCache.getIcon("translate.png"),
                    self.trUtf8("Google Translate"), self.__openLinkInNewTab)\
                    .setData(googleTranslatorUrl)
                wiktionaryUrl = QUrl(
                    "http://{0}.wiktionary.org/wiki/Special:Search?search={1}".format(
                        langCode, self.selectedText()))
                menu.addAction(UI.PixmapCache.getIcon("wikipedia.png"),
                    self.trUtf8("Dictionary"), self.__openLinkInNewTab)\
                    .setData(wiktionaryUrl)
                menu.addSeparator()
            
            guessedUrl = QUrl.fromUserInput(self.selectedText().strip())
            if self.__isUrlValid(guessedUrl):
                menu.addAction(self.trUtf8("Go to web address"), self.__openLinkInNewTab)\
                    .setData(guessedUrl)
                menu.addSeparator()
        
        if hasattr(QtWebKit, 'QWebElement'):
            element = hit.element()
            if not element.isNull() and \
               element.tagName().lower() == "input" and \
               element.attribute("type", "text") == "text":
                menu.addAction(self.trUtf8("Add to web search toolbar"),
                               self.__addSearchEngine).setData(element)
                menu.addSeparator()
        
        menu.addAction(UI.PixmapCache.getIcon("webInspector.png"),
            self.trUtf8("Web Inspector..."), self.__webInspector)
        
        menu.exec_(evt.globalPos())
    
    def __isUrlValid(self, url):
        """
        Private method to check a URL for validity.
        
        @param url URL to be checked (QUrl)
        @return flag indicating a valid URL (boolean)
        """
        return url.isValid() and \
               bool(url.host()) and \
               bool(url.scheme()) and \
               "." in url.host()
    
    def __openLinkInNewTab(self):
        """
        Private method called by the context menu to open a link in a new window.
        """
        act = self.sender()
        url = act.data()
        if url.isEmpty():
            return
        
        self.ctrlPressed = True
        self.setSource(url)
        self.ctrlPressed = False
    
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
    
    def __sendLink(self):
        """
        Private slot to send a link via email.
        """
        act = self.sender()
        data = act.data()
        if isinstance(data, QUrl) and data.isEmpty():
            return
        
        if isinstance(data, QUrl):
            data = data.toString()
        QDesktopServices.openUrl(QUrl("mailto:?body=" + data))
    
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
    
    def __virusTotal(self):
        """
        Private slot to scan the selected URL with VirusTotal.
        """
        act = self.sender()
        url = act.data()
        self.mw.requestVirusTotalScan(url)
    
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
            E5MessageBox.warning(self,
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
    
    def addBookmark(self):
        """
        Public slot to bookmark the current page.
        """
        dlg = AddBookmarkDialog()
        dlg.setUrl(bytes(self.url().toEncoded()).decode())
        dlg.setTitle(self.title())
        dlg.exec_()
    
    def dragEnterEvent(self, evt):
        """
        Protected method called by a drag enter event.
        
        @param evt reference to the drag enter event (QDragEnterEvent)
        """
        evt.acceptProposedAction()
    
    def dragMoveEvent(self, evt):
        """
        Protected method called by a drag move event.
        
        @param evt reference to the drag move event (QDragMoveEvent)
        """
        evt.ignore()
        if evt.source() != self:
            if len(evt.mimeData().urls()) > 0:
                evt.acceptProposedAction()
            else:
                url = QUrl(evt.mimeData().text())
                if url.isValid():
                    evt.acceptProposedAction()
        
        if not evt.isAccepted():
            super().dragMoveEvent(evt)
    
    def dropEvent(self, evt):
        """
        Protected method called by a drop event.
        
        @param evt reference to the drop event (QDropEvent)
        """
        super().dropEvent(evt)
        if not evt.isAccepted() and \
           evt.source() != self and \
           evt.possibleActions() & Qt.CopyAction:
            url = QUrl()
            if len(evt.mimeData().urls()) > 0:
                url = evt.mimeData().urls()[0]
            if not url.isValid():
                url = QUrl(evt.mimeData().text())
            if url.isValid():
                self.setSource(url)
                evt.acceptProposedAction()
    
    def mousePressEvent(self, evt):
        """
        Protected method called by a mouse press event.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        self.mw.setEventMouseButtons(evt.buttons())
        self.mw.setEventKeyboardModifiers(evt.modifiers())
        
        if evt.button() == Qt.XButton1:
            self.pageAction(QWebPage.Back).trigger()
        elif evt.button() == Qt.XButton2:
            self.pageAction(QWebPage.Forward).trigger()
        else:
            super().mousePressEvent(evt)
    
    def mouseReleaseEvent(self, evt):
        """
        Protected method called by a mouse release event.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        accepted = evt.isAccepted()
        self.__page.event(evt)
        if not evt.isAccepted() and \
           self.mw.eventMouseButtons() & Qt.MidButton:
            url = QUrl(QApplication.clipboard().text(QClipboard.Selection))
            if not url.isEmpty() and \
               url.isValid() and \
               url.scheme() != "":
                self.mw.setEventMouseButtons(Qt.NoButton)
                self.mw.setEventKeyboardModifiers(Qt.NoModifier)
                self.setSource(url)
        evt.setAccepted(accepted)
    
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
        
        if evt.modifiers() & Qt.ShiftModifier:
            if evt.delta() < 0:
                self.backward()
            else:
                self.forward()
            evt.accept()
            return
        
        super().wheelEvent(evt)
    
    def keyPressEvent(self, evt):
        """
        Protected method called by a key press.
        
        @param evt reference to the key event (QKeyEvent)
        """
        if hasattr(QtWebKit, 'QWebElement'):
            if self.__enableAccessKeys:
                self.__accessKeysPressed = (
                    evt.modifiers() == Qt.ControlModifier and \
                    evt.key() == Qt.Key_Control)
                if not self.__accessKeysPressed:
                    if self.__checkForAccessKey(evt):
                        self.__hideAccessKeys()
                        evt.accept()
                        return
                    self.__hideAccessKeys()
                else:
                    QTimer.singleShot(300, self.__accessKeyShortcut)
        
        self.ctrlPressed = (evt.key() == Qt.Key_Control)
        super().keyPressEvent(evt)
    
    def keyReleaseEvent(self, evt):
        """
        Protected method called by a key release.
        
        @param evt reference to the key event (QKeyEvent)
        """
        if hasattr(QtWebKit, 'QWebElement'):
            if self.__enableAccessKeys:
                self.__accessKeysPressed = evt.key() == Qt.Key_Control
        
        self.ctrlPressed = False
        super().keyReleaseEvent(evt)
    
    def focusOutEvent(self, evt):
        """
        Protected method called by a focus out event.
        
        @param evt reference to the focus event (QFocusEvent)
        """
        if hasattr(QtWebKit, 'QWebElement'):
            if self.__accessKeysPressed:
                self.__hideAccessKeys()
                self.__accessKeysPressed = False
        
        super().focusOutEvent(evt)
    
    def event(self, evt):
        """
        Protected method handling events.
        
        @param evt reference to the event (QEvent)
        @return flag indicating, if the event was handled (boolean)
        """
        if evt.type() == QEvent.Gesture:
            self.gestureEvent(evt)
            return True
        
        return super().event(evt)
    
    def gestureEvent(self, evt):
        """
        Protected method handling gesture events.
        
        @param evt reference to the gesture event (QGestureEvent
        """
        pinch = evt.gesture(Qt.PinchGesture)
        if pinch:
            if pinch.state() == Qt.GestureStarted:
                pinch.setScaleFactor(self.__currentZoom / 100.0)
            else:
                scaleFactor = pinch.scaleFactor()
                self.__currentZoom = int(scaleFactor * 100)
                self.__applyZoom()
            evt.accept()
    
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
        self.__progress = 0
    
    def __loadProgress(self, progress):
        """
        Private method to handle the loadProgress signal.
        
        @param progress progress value (integer)
        """
        self.__progress = progress
    
    def __loadFinished(self, ok):
        """
        Private method to handle the loadFinished signal.
        
        @param ok flag indicating the result (boolean)
        """
        self.__isLoading = False
        self.__progress = 0
        
        if ok:
            self.mw.adblockManager().page().applyRulesToPage(self.page())
            self.mw.passwordManager().fill(self.page())
    
    def isLoading(self):
        """
        Public method to get the loading state.
        
        @return flag indicating the loading state (boolean)
        """
        return self.__isLoading
    
    def progress(self):
        """
        Public method to get the load progress.
        """
        return self.__progress
    
    def saveAs(self):
        """
        Public method to save the current page to a file.
        """
        url = self.url()
        if url.isEmpty():
            return
        
        self.mw.downloadManager().download(url, True, mainWindow=self.mw)
    
    def __unsupportedContent(self, reply, requestFilename=None, download=False):
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
            if reply.header(QNetworkRequest.ContentTypeHeader):
                self.mw.downloadManager().handleUnsupportedContent(
                    reply, webPage=self.page(), mainWindow=self.mw)
                return
        
        replyUrl = reply.url()
        if replyUrl.isEmpty():
            return
        
        notFoundFrame = self.page().mainFrame()
        if notFoundFrame is None:
            return
        
        if reply.header(QNetworkRequest.ContentTypeHeader):
            data = reply.readAll()
            if contentSniff(data):
                notFoundFrame.setHtml(str(data, encoding="utf-8"), replyUrl)
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
                        "the network."),
            self.trUtf8("If your cache policy is set to offline browsing,"
                        "only pages in the local cache are available.")
        )
        notFoundFrame.setHtml(html, replyUrl)
        self.mw.historyManager().removeHistoryEntry(replyUrl, self.title())
        self.loadFinished.emit(False)
    
    def __downloadRequested(self, request):
        """
        Private slot to handle a download request.
        
        @param request reference to the request object (QNetworkRequest)
        """
        self.mw.downloadManager().download(request, mainWindow=self.mw)
    
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
        
        res = E5MessageBox.yesNo(self,
            self.trUtf8("Web Database Quota"),
            self.trUtf8("""<p>The database quota of <strong>{0}</strong> has"""
                        """ been exceeded while accessing database <strong>{1}"""
                        """</strong>.</p><p>Shall it be changed?</p>""")\
                .format(self.__dataString(securityOrigin.databaseQuota()), databaseName),
            yesDefault=True)
        if res:
            newQuota, ok = QInputDialog.getInteger(
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
    ## Access key related methods below
    ############################################################################
    
    def __accessKeyShortcut(self):
        """
        Private slot to switch the display of access keys.
        """
        if not self.hasFocus() or \
           not self.__accessKeysPressed or \
           not self.__enableAccessKeys:
            return
        
        if self.__accessKeyLabels:
            self.__hideAccessKeys()
        else:
            self.__showAccessKeys()
        
        self.__accessKeysPressed = False
    
    def __checkForAccessKey(self, evt):
        """
        Private method to check the existence of an access key and activate the
        corresponding link.
        
        @param evt reference to the key event (QKeyEvent)
        @return flag indicating, if the event was handled (boolean)
        """
        if not self.__accessKeyLabels:
            return False
        
        text = evt.text()
        if not text:
            return False
        
        key = text[0].upper()
        handled = False
        if key in self.__accessKeyNodes:
            element = self.__accessKeyNodes[key]
            p = element.geometry().center()
            frame = element.webFrame()
            p -= frame.scrollPosition()
            frame = frame.parentFrame()
            while frame and frame != self.page().mainFrame():
                p -= frame.scrollPosition()
                frame = frame.parentFrame()
            pevent = QMouseEvent(QEvent.MouseButtonPress, p, Qt.LeftButton,
                Qt.MouseButtons(Qt.NoButton), Qt.KeyboardModifiers(Qt.NoModifier))
            qApp.sendEvent(self, pevent)
            revent = QMouseEvent(QEvent.MouseButtonRelease, p, Qt.LeftButton,
                Qt.MouseButtons(Qt.NoButton), Qt.KeyboardModifiers(Qt.NoModifier))
            qApp.sendEvent(self, revent)
            handled = True
        
        return handled
    
    def __hideAccessKeys(self):
        """
        Private slot to hide the access key labels.
        """
        if self.__accessKeyLabels:
            for label in self.__accessKeyLabels:
                label.hide()
                label.deleteLater()
            self.__accessKeyLabels = []
            self.__accessKeyNodes = {}
            self.update()
    
    def __showAccessKeys(self):
        """
        Private method to show the access key labels.
        """
        supportedElements = [
            "input", "a", "area", "button", "label", "legend", "textarea",
        ]
        unusedKeys = "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z" \
            " 0 1 2 3 4 5 6 7 8 9".split()
        
        viewport = QRect(self.__page.mainFrame().scrollPosition(),
                         self.__page.viewportSize())
        # Priority first goes to elements with accesskey attributes
        alreadyLabeled = []
        for elementType in supportedElements:
            result = self.page().mainFrame().findAllElements(elementType).toList()
            for element in result:
                geometry = element.geometry()
                if geometry.size().isEmpty() or \
                   not viewport.contains(geometry.topLeft()):
                    continue
                
                accessKeyAttribute = element.attribute("accesskey").upper()
                if not accessKeyAttribute:
                    continue
                
                accessKey = ""
                i = 0
                while i < len(accessKeyAttribute):
                    if accessKeyAttribute[i] in unusedKeys:
                        accessKey = accessKeyAttribute[i]
                        break
                    i += 2
                if accessKey == "":
                    continue
                unusedKeys.remove(accessKey)
                self.__makeAccessLabel(accessKey, element)
                alreadyLabeled.append(element)
        
        # Pick an access key first from the letters in the text and then from the
        # list of unused access keys
        for elementType in supportedElements:
            result = self.page().mainFrame().findAllElements(elementType).toList()
            for element in result:
                geometry = element.geometry()
                if not unusedKeys or \
                   element in alreadyLabeled or \
                   geometry.size().isEmpty() or \
                   not viewport.contains(geometry.topLeft()):
                    continue
                
                accessKey = ""
                text = element.toPlainText().upper()
                for c in text:
                    if c in unusedKeys:
                        accessKey = c
                        break
                if accessKey == "":
                    accessKey = unusedKeys[0]
                unusedKeys.remove(accessKey)
                self.__makeAccessLabel(accessKey, element)
    
    def __makeAccessLabel(self, accessKey, element):
        """
        Private method to generate the access label for an element.
        
        @param accessKey access key to generate the label for (str)
        @param element reference to the web element to create the label for
            (QWebElement)
        """
        label = QLabel(self)
        label.setText("<qt><b>{0}</b></qt>".format(accessKey))
        
        p = QToolTip.palette()
        color = QColor(Qt.yellow).lighter(150)
        color.setAlpha(175)
        p.setColor(QPalette.Window, color)
        label.setPalette(p)
        label.setAutoFillBackground(True)
        label.setFrameStyle(QFrame.Box | QFrame.Plain)
        point = element.geometry().center()
        point -= self.__page.mainFrame().scrollPosition()
        label.move(point)
        label.show()
        point.setX(point.x() - label.width() // 2)
        label.move(point)
        self.__accessKeyLabels.append(label)
        self.__accessKeyNodes[accessKey] = element
    
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
        if hasattr(QtWebKit, 'QWebElement'):
            self.__enableAccessKeys = Preferences.getHelp("AccessKeysEnabled")
            if not self.__enableAccessKeys:
                self.__hideAccessKeys()
        
        self.reload()
    
    ############################################################################
    ## RSS related methods below
    ############################################################################
    
    def checkRSS(self):
        """
        Public method to check, if the loaded page contains feed links.
        
        @return flag indicating the existence of feed links (boolean)
        """
        self.__rss = []
        
        frame = self.page().mainFrame()
        linkElementsList = frame.findAllElements("link").toList()
        
        for linkElement in linkElementsList:
            # only atom+xml and rss+xml will be processed
            if linkElement.attribute("rel") != "alternate" or \
               (linkElement.attribute("type") != "application/rss+xml" and \
                linkElement.attribute("type") != "application/atom+xml"):
                continue
            
            title = linkElement.attribute("title")
            href = linkElement.attribute("href")
            if href == "" or title == "":
                continue
            self.__rss.append((title, href))
        
        return len(self.__rss) > 0
    
    def getRSS(self):
        """
        Public method to get the extracted RSS feeds.
        
        @return list of RSS feeds (list of tuples of two strings)
        """
        return self.__rss
    
    def hasRSS(self):
        """
        Public method to check, if the loaded page has RSS links.
        
        @return flag indicating the presence of RSS links (boolean)
        """
        return len(self.__rss) > 0
    
    ############################################################################
    ## Clicked Frame slots
    ############################################################################
    
    def __loadClickedFrame(self):
        """
        Private slot to load the selected frame only.
        """
        self.setSource(self.__clickedFrame.url())
    
    def __printClickedFrame(self):
        """
        Private slot to print the selected frame.
        """
        printer = QPrinter(mode=QPrinter.HighResolution)
        if Preferences.getPrinter("ColorMode"):
            printer.setColorMode(QPrinter.Color)
        else:
            printer.setColorMode(QPrinter.GrayScale)
        if Preferences.getPrinter("FirstPageFirst"):
            printer.setPageOrder(QPrinter.FirstPageFirst)
        else:
            printer.setPageOrder(QPrinter.LastPageFirst)
        printer.setPageMargins(
            Preferences.getPrinter("LeftMargin") * 10,
            Preferences.getPrinter("TopMargin") * 10,
            Preferences.getPrinter("RightMargin") * 10,
            Preferences.getPrinter("BottomMargin") * 10,
            QPrinter.Millimeter
        )
        printer.setPrinterName(Preferences.getPrinter("PrinterName"))
        
        printDialog = QPrintDialog(printer, self)
        if printDialog.exec_() == QDialog.Accepted:
            try:
                self.__clickedFrame.print_(printer)
            except AttributeError:
                E5MessageBox.critical(self,
                    self.trUtf8("eric5 Web Browser"),
                    self.trUtf8("""<p>Printing is not available due to a bug in PyQt4."""
                                """Please upgrade.</p>"""))
    
    def __printPreviewClickedFrame(self):
        """
        Private slot to show a print preview of the clicked frame.
        """
        from PyQt4.QtGui import QPrintPreviewDialog
        
        printer = QPrinter(mode=QPrinter.HighResolution)
        if Preferences.getPrinter("ColorMode"):
            printer.setColorMode(QPrinter.Color)
        else:
            printer.setColorMode(QPrinter.GrayScale)
        if Preferences.getPrinter("FirstPageFirst"):
            printer.setPageOrder(QPrinter.FirstPageFirst)
        else:
            printer.setPageOrder(QPrinter.LastPageFirst)
        printer.setPageMargins(
            Preferences.getPrinter("LeftMargin") * 10,
            Preferences.getPrinter("TopMargin") * 10,
            Preferences.getPrinter("RightMargin") * 10,
            Preferences.getPrinter("BottomMargin") * 10,
            QPrinter.Millimeter
        )
        printer.setPrinterName(Preferences.getPrinter("PrinterName"))
        
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(self.__generatePrintPreviewClickedFrame)
        preview.exec_()
    
    def __generatePrintPreviewClickedFrame(self, printer):
        """
        Private slot to generate a print preview of the clicked frame.
        
        @param printer reference to the printer object (QPrinter)
        """
        try:
            self.__clickedFrame.print_(printer)
        except AttributeError:
            E5MessageBox.critical(self,
                self.trUtf8("eric5 Web Browser"),
                self.trUtf8("""<p>Printing is not available due to a bug in PyQt4."""
                            """Please upgrade.</p>"""))
            return
    
    def __printPdfClickedFrame(self):
        """
        Private slot to print the selected frame to PDF.
        """
        printer = QPrinter(mode=QPrinter.HighResolution)
        if Preferences.getPrinter("ColorMode"):
            printer.setColorMode(QPrinter.Color)
        else:
            printer.setColorMode(QPrinter.GrayScale)
        printer.setPrinterName(Preferences.getPrinter("PrinterName"))
        printer.setOutputFormat(QPrinter.PdfFormat)
        name = self.__clickedFrame.url().path().rsplit('/', 1)[-1]
        if name:
            name = name.rsplit('.', 1)[0]
            name += '.pdf'
            printer.setOutputFileName(name)
        
        printDialog = QPrintDialog(printer, self)
        if printDialog.exec_() == QDialog.Accepted:
            try:
                self.__clickedFrame.print_(printer)
            except AttributeError:
                E5MessageBox.critical(self,
                    self.trUtf8("eric5 Web Browser"),
                    self.trUtf8("""<p>Printing is not available due to a bug in PyQt4."""
                                """Please upgrade.</p>"""))
                return
    
    def __zoomInClickedFrame(self):
        """
        Private slot to zoom into the clicked frame.
        """
        index = self.__levelForZoom(int(self.__clickedFrame.zoomFactor() * 100))
        if index < len(self.__zoomLevels) - 1:
            self.__clickedFrame.setZoomFactor(self.__zoomLevels[index + 1] / 100)
    
    def __zoomResetClickedFrame(self):
        """
        Private slot to reset the zoom factor of the clicked frame.
        """
        self.__clickedFrame.setZoomFactor(self.__currentZoom / 100)
    
    def __zoomOutClickedFrame(self):
        """
        Private slot to zoom out of the clicked frame.
        """
        index = self.__levelForZoom(int(self.__clickedFrame.zoomFactor() * 100))
        if index > 0:
            self.__clickedFrame.setZoomFactor(self.__zoomLevels[index - 1] / 100)
    
    def __showClickedFrameSource(self):
        """
        Private slot to show the source of the clicked frame.
        """
        from QScintilla.MiniEditor import MiniEditor
        src = self.__clickedFrame.toHtml()
        editor = MiniEditor(parent=self)
        editor.setText(src, "Html")
        editor.setLanguage("dummy.html")
        editor.show()


def contentSniff(data):
    """
    Module function to do some content sniffing to check, if the data is HTML.
    
    @return flag indicating HTML content (boolean)
    """
    if data.contains("<!doctype") or \
       data.contains("<script") or \
       data.contains("<html") or \
       data.contains("<!--") or \
       data.contains("<head") or \
       data.contains("<iframe") or \
       data.contains("<h1") or \
       data.contains("<div") or \
       data.contains("<font") or \
       data.contains("<table") or \
       data.contains("<a") or \
       data.contains("<style") or \
       data.contains("<title") or \
       data.contains("<b") or \
       data.contains("<body") or \
       data.contains("<br") or \
       data.contains("<p"):
        return True
    
    return False
