# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the URL bar widget.
"""

from PyQt4.QtCore import pyqtSlot, Qt, QPointF, QUrl
from PyQt4.QtGui import QColor, QPalette, QApplication, QLinearGradient, QIcon
try:
    from PyQt4.QtNetwork import QSslCertificate     # __IGNORE_EXCEPTION__
except ImportError:
    QSslCertificate = None      # __IGNORE_WARNING__
from PyQt4.QtWebKit import QWebSettings, QWebPage

from E5Gui.E5LineEdit import E5LineEdit
from E5Gui.E5LineEditButton import E5LineEditButton

import Helpviewer.HelpWindow

from .FavIconLabel import FavIconLabel
from .SslLabel import SslLabel
from .BookmarkInfoDialog import BookmarkInfoDialog

import UI.PixmapCache
import Preferences
import Utilities


class UrlBar(E5LineEdit):
    """
    Class implementing a line edit for entering URLs.
    """
    def __init__(self, mainWindow, parent=None):
        """
        Constructor
        
        @param mainWindow reference to the main window (HelpWindow)
        @param parent reference to the parent widget (HelpBrowser)
        """
        E5LineEdit.__init__(self, parent)
        self.setInactiveText(self.trUtf8("Enter the URL here."))
        self.setWhatsThis(self.trUtf8("Enter the URL here."))
        
        self.__mw = mainWindow
        self.__browser = None
        self.__privateMode = QWebSettings.globalSettings().testAttribute(
            QWebSettings.PrivateBrowsingEnabled)
        
        self.__bmActiveIcon = UI.PixmapCache.getIcon("bookmark16.png")
        self.__bmInactiveIcon = QIcon(self.__bmActiveIcon.pixmap(16, 16, QIcon.Disabled))
        
        self.__favicon = FavIconLabel(self)
        self.addWidget(self.__favicon, E5LineEdit.LeftSide)
        
        self.__sslLabel = SslLabel(self)
        self.addWidget(self.__sslLabel, E5LineEdit.LeftSide)
        self.__sslLabel.setVisible(False)
        
        self.__privacyButton = E5LineEditButton(self)
        self.__privacyButton.setIcon(UI.PixmapCache.getIcon("privateBrowsing.png"))
        self.addWidget(self.__privacyButton, E5LineEdit.RightSide)
        self.__privacyButton.setVisible(self.__privateMode)
        
        self.__bookmarkButton = E5LineEditButton(self)
        self.addWidget(self.__bookmarkButton, E5LineEdit.RightSide)
        self.__bookmarkButton.setVisible(False)
        
        self.__clearButton = E5LineEditButton(self)
        self.__clearButton.setIcon(UI.PixmapCache.getIcon("clearLeft.png"))
        self.addWidget(self.__clearButton, E5LineEdit.RightSide)
        self.__clearButton.setVisible(False)
        
        self.__bookmarkButton.clicked[()].connect(self.__showBookmarkInfo)
        self.__privacyButton.clicked[()].connect(self.__privacyClicked)
        self.__clearButton.clicked[()].connect(self.clear)
        self.__mw.privacyChanged.connect(self.__privacyButton.setVisible)
        self.textChanged.connect(self.__textChanged)
        
        Helpviewer.HelpWindow.HelpWindow.bookmarksManager().entryChanged.connect(
            self.__bookmarkChanged)
        Helpviewer.HelpWindow.HelpWindow.bookmarksManager().entryAdded.connect(
            self.__bookmarkChanged)
        Helpviewer.HelpWindow.HelpWindow.bookmarksManager().entryRemoved.connect(
            self.__bookmarkChanged)
    
    def setBrowser(self, browser):
        """
        Public method to set the browser connection.
        
        @param browser reference to the browser widegt (HelpBrowser)
        """
        self.__browser = browser
        self.__favicon.setBrowser(browser)
        
        self.__browser.urlChanged.connect(self.__browserUrlChanged)
        self.__browser.loadProgress.connect(self.update)
        self.__browser.loadFinished.connect(self.__loadFinished)
        self.__browser.loadStarted.connect(self.__loadStarted)
        
        self.__sslLabel.clicked[()].connect(self.__browser.page().showSslInfo)
    
    def browser(self):
        """
        Public method to get the associated browser (HelpBrowser)
        """
        return self.__browser
    
    def __browserUrlChanged(self, url):
        """
        Private slot to handle a URL change of the associated browser.
        
        @param url new URL of the browser (QUrl)
        """
        self.setText(str(url.toEncoded(), encoding="utf-8"))
        self.setCursorPosition(0)
    
    def __loadStarted(self):
        """
        Private slot to perform actions before the page is loaded.
        """
        self.__sslLabel.setVisible(False)
        self.__bookmarkButton.setVisible(False)
    
    def __loadFinished(self, ok):
        """
        Private slot to set some data after the page was loaded.
        
        @param ok flag indicating a successful load (boolean)
        """
        try:
            if self.__browser.url().scheme() in ["pyrc", "about"]:
                self.__bookmarkButton.setVisible(False)
            else:
                if Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
                   .bookmarkForUrl(self.__browser.url()) is None:
                    self.__bookmarkButton.setIcon(self.__bmInactiveIcon)
                else:
                    self.__bookmarkButton.setIcon(self.__bmActiveIcon)
                self.__bookmarkButton.setVisible(True)
            
            if ok and \
               self.__browser.url().scheme() == "https" and \
               QSslCertificate is not None:
                sslInfo = self.__browser.page().getSslInfo()
                if sslInfo is not None:
                    org = Qt.escape(Utilities.decodeString(
                        sslInfo.subjectInfo(QSslCertificate.Organization)))
                    if org == "":
                        cn = Qt.escape(Utilities.decodeString(
                            sslInfo.subjectInfo(QSslCertificate.CommonName)))
                        if cn != "":
                            org = cn.split(".", 1)[1]
                        if org == "":
                            org = self.trUtf8("Unknown")
                    self.__sslLabel.setText(" {0} ".format(org))
                    self.__sslLabel.setVisible(True)
                    self.__sslLabel.setValidity(sslInfo.isValid())
                    return
            
            self.__sslLabel.setVisible(False)
        except RuntimeError:
            pass
    
    def setPrivateMode(self, on):
        """
        Public method to set the private mode.
        
        @param on flag indicating the privacy state (boolean)
        """
        self.__privateMode = on
        self.__privacyButton.setVisible(on)
    
    def __privacyClicked(self):
        """
        Private slot to handle the click of the private mode button.
        """
        self.__mw.setPrivateMode(False)
    
    def __textChanged(self, txt):
        """
        Private slot to handle changes of the text.
        
        @param txt current text (string)
        """
        self.__clearButton.setVisible(txt != "")
    
    def preferencesChanged(self):
        """
        Public slot to handle a change of preferences.
        """
        self.update()
    
    def __showBookmarkInfo(self):
        """
        Private slot to show a dialog with some bookmark info.
        """
        bookmark = Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
           .bookmarkForUrl(self.__browser.url())
        if bookmark is None:
            self.__browser.addBookmark()
        else:
            dlg = BookmarkInfoDialog(bookmark, self.__browser)
            dlg.exec_()
    
    @pyqtSlot()
    def __bookmarkChanged(self):
        """
        Private slot to handle bookmark changes.
        """
        if Helpviewer.HelpWindow.HelpWindow.bookmarksManager()\
           .bookmarkForUrl(self.__browser.url()) is None:
            self.__bookmarkButton.setIcon(self.__bmInactiveIcon)
        else:
            self.__bookmarkButton.setIcon(self.__bmActiveIcon)
    
    def paintEvent(self, evt):
        """
        Protected method handling a paint event.
        
        @param evt reference to the paint event (QPaintEvent)
        """
        if self.__privateMode:
            backgroundColor = QColor(220, 220, 220)     # light gray
            foregroundColor = Qt.black
        else:
            backgroundColor = QApplication.palette().color(QPalette.Base)
            foregroundColor = QApplication.palette().color(QPalette.Text)
        
        if self.__browser is not None:
            p = self.palette()
            progress = self.__browser.progress()
            if progress == 0:
                if self.__browser.url().scheme() == "https":
                    backgroundColor = Preferences.getHelp("SaveUrlColor")
                p.setBrush(QPalette.Base, backgroundColor)
                p.setBrush(QPalette.Text, foregroundColor)
            else:
                if self.__browser.url().scheme() == "https":
                    backgroundColor = Preferences.getHelp("SaveUrlColor")
                highlight = QApplication.palette().color(QPalette.Highlight)
                r = (highlight.red() + 2 * backgroundColor.red()) // 3
                g = (highlight.green() + 2 * backgroundColor.green()) // 3
                b = (highlight.blue() + 2 * backgroundColor.blue()) // 3
                
                loadingColor = QColor(r, g, b)
                if abs(loadingColor.lightness() - backgroundColor.lightness()) < 20:
                    # special handling for special color schemes (e.g Gaia)
                    r = (2 * highlight.red() + backgroundColor.red()) // 3
                    g = (2 * highlight.green() + backgroundColor.green()) // 3
                    b = (2 * highlight.blue() + backgroundColor.blue()) // 3
                    loadingColor = QColor(r, g, b)
                
                gradient = QLinearGradient(QPointF(0, 0), QPointF(self.width(), 0))
                gradient.setColorAt(0, loadingColor)
                gradient.setColorAt(progress / 100 - 0.000001, loadingColor)
                gradient.setColorAt(progress / 100, backgroundColor)
                p.setBrush(QPalette.Base, gradient)
            
            self.setPalette(p)
        
        E5LineEdit.paintEvent(self, evt)
    
    def focusOutEvent(self, evt):
        """
        Protected method to handle focus out event.
        
        @param evt reference to the focus event (QFocusEvent)
        """
        if self.text() == "" and self.__browser is not None:
            self.__browserUrlChanged(self.__browser.url())
        E5LineEdit.focusOutEvent(self, evt)
    
    def mousePressEvent(self, evt):
        """
        Protected method called by a mouse press event.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if evt.button() == Qt.XButton1:
            self.__mw.currentBrowser().pageAction(QWebPage.Back).trigger()
        elif evt.button() == Qt.XButton2:
            self.__mw.currentBrowser().pageAction(QWebPage.Forward).trigger()
        else:
            super().mousePressEvent(evt)
    
    def mouseDoubleClickEvent(self, evt):
        """
        Protected method to handle mouse double click events.
        
        @param evt reference to the mouse event (QMouseEvent)
        """
        if evt.button() == Qt.LeftButton:
            self.selectAll()
        else:
            E5LineEdit.mouseDoubleClickEvent(self, evt)
    
    def keyPressEvent(self, evt):
        """
        Protected method to handle key presses.
        
        @param evt reference to the key press event (QKeyEvent)
        """
        if evt.key() == Qt.Key_Escape and self.__browser is not None:
            self.setText(str(self.__browser.url().toEncoded(), encoding="utf-8"))
            self.selectAll()
            return
        
        currentText = self.text().strip()
        if evt.key() in [Qt.Key_Enter, Qt.Key_Return] and \
           not currentText.lower().startswith("http://"):
            append = ""
            if evt.modifiers() == Qt.KeyboardModifiers(Qt.ControlModifier):
                append = ".com"
            elif evt.modifiers() == \
                    Qt.KeyboardModifiers(Qt.ControlModifier | Qt.ShiftModifier):
                append = ".org"
            elif evt.modifiers() == Qt.KeyboardModifiers(Qt.ShiftModifier):
                append = ".net"
            
            if append != "":
                url = QUrl("http://www." + currentText)
                host = url.host()
                if not host.lower().endswith(append):
                    host += append
                    url.setHost(host)
                    self.setText(url.toString())
        
        E5LineEdit.keyPressEvent(self, evt)
    
    def dragEnterEvent(self, evt):
        """
        Protected method to handle drag enter events.
        
        @param evt reference to the drag enter event (QDragEnterEvent)
        """
        mimeData = evt.mimeData()
        if mimeData.hasUrls() or mimeData.hasText():
            evt.acceptProposedAction()
        
        E5LineEdit.dragEnterEvent(self, evt)
    
    def dropEvent(self, evt):
        """
        Protected method to handle drop events.
        
        @param evt reference to the drop event (QDropEvent)
        """
        mimeData = evt.mimeData()
        
        url = QUrl()
        if mimeData.hasUrls():
            url = mimeData.urls()[0]
        elif mimeData.hasText():
            url = QUrl.fromEncoded(mimeData.text().encode(), QUrl.TolerantMode)
        
        if url.isEmpty() or not url.isValid():
            E5LineEdit.dropEvent(self, evt)
            return
        
        self.setText(str(url.toEncoded(), encoding="utf-8"))
        self.selectAll()
        
        evt.acceptProposedAction()
