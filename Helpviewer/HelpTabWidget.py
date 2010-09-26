# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the central widget showing the web pages.
"""

import os

from PyQt4.QtCore import pyqtSignal, Qt, QUrl
from PyQt4.QtGui import QWidget, QHBoxLayout, QMenu, QToolButton, QPrinter, \
    QPrintDialog, QDialog, QIcon

from E5Gui.E5TabWidget import E5TabWidget
from E5Gui import E5MessageBox

from .HelpTabBar import HelpTabBar
from .HelpBrowserWV import HelpBrowser

import UI.PixmapCache

import Preferences

from eric5config import getConfig

class HelpTabWidget(E5TabWidget):
    """
    Class implementing the central widget showing the web pages.
    """
    sourceChanged = pyqtSignal(QUrl)
    titleChanged = pyqtSignal(str)
    showMessage = pyqtSignal(str)
    
    def __init__(self, parent):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        E5TabWidget.__init__(self, parent, dnd = True)
        self.setCustomTabBar(True, HelpTabBar(self))
        
        self.__mainWindow = parent
        
        self.__tabContextMenuIndex = -1
##        self.currentChanged[int].connect(self.__currentChanged)
        self.setTabContextMenuPolicy(Qt.CustomContextMenu)
        self.customTabContextMenuRequested.connect(self.__showContextMenu)
        
        self.__rightCornerWidget = QWidget(self)
        self.__rightCornerWidgetLayout = QHBoxLayout(self.__rightCornerWidget)
        self.__rightCornerWidgetLayout.setMargin(0)
        self.__rightCornerWidgetLayout.setSpacing(0)
        
        self.__navigationMenu = QMenu(self)
        self.__navigationMenu.aboutToShow.connect(self.__showNavigationMenu)
        self.__navigationMenu.triggered.connect(self.__navigationMenuTriggered)
        
        self.__navigationButton = QToolButton(self)
        self.__navigationButton.setIcon(UI.PixmapCache.getIcon("1downarrow.png"))
        self.__navigationButton.setToolTip(self.trUtf8("Show a navigation menu"))
        self.__navigationButton.setPopupMode(QToolButton.InstantPopup)
        self.__navigationButton.setMenu(self.__navigationMenu)
        self.__navigationButton.setEnabled(False)
        self.__rightCornerWidgetLayout.addWidget(self.__navigationButton)
        
        if Preferences.getUI("SingleCloseButton") or \
           not hasattr(self, 'setTabsClosable'):
            self.__closeButton = QToolButton(self)
            self.__closeButton.setIcon(UI.PixmapCache.getIcon("close.png"))
            self.__closeButton.setToolTip(self.trUtf8("Close the current help window"))
            self.__closeButton.setEnabled(False)
            self.__closeButton.clicked[bool].connect(self.closeBrowser)
            self.__rightCornerWidgetLayout.addWidget(self.__closeButton)
        else:
            self.setTabsClosable(True)
            self.tabCloseRequested.connect(self.closeBrowserAt)
            self.__closeButton = None
        
        self.setCornerWidget(self.__rightCornerWidget, Qt.TopRightCorner)
        
        self.__newTabButton = QToolButton(self)
        self.__newTabButton.setIcon(UI.PixmapCache.getIcon("tabNew.png"))
        self.__newTabButton.setToolTip(self.trUtf8("Open a new help window tab"))
        self.setCornerWidget(self.__newTabButton, Qt.TopLeftCorner)
        self.__newTabButton.clicked[bool].connect(self.newBrowser)
        
        self.__initTabContextMenu()
    
    def __initTabContextMenu(self):
        """
        Private mezhod to create the tab context menu.
        """
        self.__tabContextMenu = QMenu(self)
        self.tabContextNewAct = \
            self.__tabContextMenu.addAction(UI.PixmapCache.getIcon("tabNew.png"),
            self.trUtf8('New Tab'), self.newBrowser)
        self.__tabContextMenu.addSeparator()
        self.leftMenuAct = \
            self.__tabContextMenu.addAction(UI.PixmapCache.getIcon("1leftarrow.png"),
            self.trUtf8('Move Left'), self.__tabContextMenuMoveLeft)
        self.rightMenuAct = \
            self.__tabContextMenu.addAction(UI.PixmapCache.getIcon("1rightarrow.png"),
            self.trUtf8('Move Right'), self.__tabContextMenuMoveRight)
        self.__tabContextMenu.addSeparator()
        self.tabContextCloneAct = \
            self.__tabContextMenu.addAction(self.trUtf8("Duplicate Page"), 
                self.__tabContextMenuClone)
        self.__tabContextMenu.addSeparator()
        self.tabContextCloseAct = \
            self.__tabContextMenu.addAction(UI.PixmapCache.getIcon("tabClose.png"),
                self.trUtf8('Close'), self.__tabContextMenuClose)
        self.tabContextCloseOthersAct = \
            self.__tabContextMenu.addAction(UI.PixmapCache.getIcon("tabCloseOther.png"),
                self.trUtf8("Close Others"), self.__tabContextMenuCloseOthers)
        self.__tabContextMenu.addAction(self.trUtf8('Close All'), 
            self.closeAllBrowsers)
        self.__tabContextMenu.addSeparator()
        self.__tabContextMenu.addAction(UI.PixmapCache.getIcon("printPreview.png"),
            self.trUtf8('Print Preview'), self.__tabContextMenuPrintPreview)
        self.__tabContextMenu.addAction(UI.PixmapCache.getIcon("print.png"),
            self.trUtf8('Print'), self.__tabContextMenuPrint)
        self.__tabContextMenu.addAction(UI.PixmapCache.getIcon("printPdf.png"),
            self.trUtf8('Print as PDF'), self.__tabContextMenuPrintPdf)
        self.__tabContextMenu.addSeparator()
        self.__tabContextMenu.addAction(self.trUtf8('Bookmark All Tabs'), 
            self.__mainWindow.bookmarkAll)
    
    def __showContextMenu(self, coord, index):
        """
        Private slot to show the tab context menu.
        
        @param coord the position of the mouse pointer (QPoint)
        @param index index of the tab the menu is requested for (integer)
        """
        self.__tabContextMenuIndex = index
        self.leftMenuAct.setEnabled(index > 0)
        self.rightMenuAct.setEnabled(index < self.count() - 1)
        
        self.tabContextCloseOthersAct.setEnabled(self.count() > 1)
        
        coord = self.mapToGlobal(coord)
        self.__tabContextMenu.popup(coord)
    
    def __tabContextMenuMoveLeft(self):
        """
        Private method to move a tab one position to the left.
        """
        self.moveTab(self.__tabContextMenuIndex, self.__tabContextMenuIndex - 1)
    
    def __tabContextMenuMoveRight(self):
        """
        Private method to move a tab one position to the right.
        """
        self.moveTab(self.__tabContextMenuIndex, self.__tabContextMenuIndex + 1)
    
    def __tabContextMenuClone(self):
        """
        Private method to clone the selected tab.
        """
        idx = self.__tabContextMenuIndex
        if idx < 0:
            idx = self.currentIndex()
        if idx < 0 or idx > self.count():
            return
        
        self.newBrowser(self.widget(idx).url())
    
    def __tabContextMenuClose(self):
        """
        Private method to close the selected tab.
        """
        self.closeBrowserAt(self.__tabContextMenuIndex)
    
    def __tabContextMenuCloseOthers(self):
        """
        Private slot to close all other tabs.
        """
        index = self.__tabContextMenuIndex
        for i in list(range(self.count() - 1, index, -1)) + \
                 list(range(index - 1, -1, -1)):
            self.closeBrowserAt(i)
    
    def __tabContextMenuPrint(self):
        """
        Private method to print the selected tab.
        """
        browser = self.widget(self.__tabContextMenuIndex)
        self.printBrowser(browser)
    
    def __tabContextMenuPrintPdf(self):
        """
        Private method to print the selected tab as PDF.
        """
        browser = self.widget(self.__tabContextMenuIndex)
        self.printBrowserPdf(browser)
    
    def __tabContextMenuPrintPreview(self):
        """
        Private method to show a print preview of the selected tab.
        """
        browser = self.widget(self.__tabContextMenuIndex)
        self.printPreviewBrowser(browser)
    
    def newBrowser(self, link = None):
        """
        Public method to create a new web browser tab.
        
        @param link link to be shown (string or QUrl)
        """
        if link is None:
            linkName = ""
        elif isinstance(link, QUrl):
            linkName = link.toString()
        else:
            linkName = link
        
        browser = HelpBrowser(self.__mainWindow, self)
        
        browser.sourceChanged.connect(self.__sourceChanged)
        browser.titleChanged.connect(self.__titleChanged)
        browser.highlighted.connect(self.showMessage)
        browser.backwardAvailable.connect(self.__mainWindow.setBackwardAvailable)
        browser.forwardAvailable.connect(self.__mainWindow.setForwardAvailable)
        browser.loadStarted.connect(self.__loadStarted)
        browser.loadFinished.connect(self.__loadFinished)
        browser.iconChanged.connect(self.__iconChanged)
        browser.search.connect(self.newBrowser)
        browser.page().windowCloseRequested.connect(self.__windowCloseRequested)
        browser.page().printRequested.connect(self.__printRequested)
        
        index = self.addTab(browser, self.trUtf8("..."))
        self.setCurrentIndex(index)
        
        self.__mainWindow.closeAct.setEnabled(True)
        self.__mainWindow.closeAllAct.setEnabled(True)
        self.__closeButton and self.__closeButton.setEnabled(True)
        self.__navigationButton.setEnabled(True)
        
        if not linkName and Preferences.getHelp("StartupBehavior") == 0:
            linkName = Preferences.getHelp("HomePage")
        
        if linkName:
            browser.setSource(QUrl(linkName))
            if not browser.documentTitle():
                self.setTabText(index, self.__elide(linkName, Qt.ElideMiddle))
                self.setTabToolTip(index, linkName)
            else:
                self.setTabText(index, 
                    self.__elide(browser.documentTitle().replace("&", "&&")))
                self.setTabToolTip(index, browser.documentTitle())
    
    def __showNavigationMenu(self):
        """
        Private slot to show the navigation button menu.
        """
        self.__navigationMenu.clear()
        for index in range(self.count()):
            act = self.__navigationMenu.addAction(
                self.tabIcon(index), self.tabText(index))
            act.setData(index)
    
    def __navigationMenuTriggered(self, act):
        """
        Private slot called to handle the navigation button menu selection.
        
        @param act reference to the selected action (QAction)
        """
        index = act.data()
        if index is not None:
            self.setCurrentIndex(index)
    
    def __windowCloseRequested(self):
        """
        Private slot to handle the windowCloseRequested signal of a browser.
        """
        page = self.sender()
        if page is None:
            return
        
        browser = page.view()
        if browser is None:
            return
        
        index = self.indexOf(browser)
        self.closeBrowserAt(index)
    
    def closeBrowser(self):
        """
        Public slot called to handle the close action.
        """
        self.closeBrowserAt(self.currentIndex())
    
    def closeAllBrowsers(self):
        """
        Public slot called to handle the close all action.
        """
        for index in range(self.count() - 1, -1, -1):
            self.closeBrowserAt(index)
    
    def closeBrowserAt(self, index):
        """
        Public slot to close a browser based on it's index.
        
        @param index index of browser to close (integer)
        """
        browser = self.widget(index)
        self.removeTab(index)
        del browser
        if self.count() == 0:
            self.newBrowser()
        else:
            self.currentChanged[int].emit(self.currentIndex())
    
    def currentBrowser(self):
        """
        Public method to get a reference to the current browser.
        
        @return reference to the current browser (HelpBrowser)
        """
        return self.currentWidget()
    
    def browserAt(self, index):
        """
        Public method to get a reference to the browser with the given index.
        
        @param index index of the browser to get (integer)
        @return reference to the indexed browser (HelpBrowser)
        """
        return self.widget(index)
    
    def browsers(self):
        """
        Public method to get a list of references to all browsers.
        
        @return list of references to browsers (list of HelpBrowser)
        """
        l = []
        for index in range(self.count()):
            l.append(self.widget(index))
        return l
    
    def printBrowser(self, browser = None):
        """
        Public slot called to print the displayed page.
        
        @param browser reference to the browser to be printed (HelpBrowser)
        """
        if browser is None:
            browser = self.currentBrowser()
        
        self.__printRequested(browser.page().mainFrame())
    
    def __printRequested(self, frame):
        """
        Private slot to handle a print request.
        
        @param frame reference to the frame to be printed (QWebFrame)
        """
        printer = QPrinter(mode = QPrinter.HighResolution)
        if Preferences.getPrinter("ColorMode"):
            printer.setColorMode(QPrinter.Color)
        else:
            printer.setColorMode(QPrinter.GrayScale)
        if Preferences.getPrinter("FirstPageFirst"):
            printer.setPageOrder(QPrinter.FirstPageFirst)
        else:
            printer.setPageOrder(QPrinter.LastPageFirst)
        printer.setPrinterName(Preferences.getPrinter("PrinterName"))
        
        printDialog = QPrintDialog(printer, self)
        if printDialog.exec_() == QDialog.Accepted:
            try:
                frame.print_(printer)
            except AttributeError:
                E5MessageBox.critical(self,
                    self.trUtf8("Eric Web Browser"),
                    self.trUtf8("""<p>Printing is not available due to a bug in PyQt4."""
                                """Please upgrade.</p>"""))
                return
    
    def printBrowserPdf(self, browser = None):
        """
        Public slot called to print the displayed page to PDF.
        
        @param browser reference to the browser to be printed (HelpBrowser)
        """
        if browser is None:
            browser = self.currentBrowser()
        
        self.__printPdfRequested(browser.page().mainFrame())
    
    def __printPdfRequested(self, frame):
        """
        Private slot to handle a print to PDF request.
        
        @param frame reference to the frame to be printed (QWebFrame)
        """
        printer = QPrinter(mode = QPrinter.HighResolution)
        if Preferences.getPrinter("ColorMode"):
            printer.setColorMode(QPrinter.Color)
        else:
            printer.setColorMode(QPrinter.GrayScale)
        printer.setPrinterName(Preferences.getPrinter("PrinterName"))
        printer.setOutputFormat(QPrinter.PdfFormat)
        name = frame.url().path().rsplit('/', 1)[-1]
        if name:
            name = name.rsplit('.', 1)[0]
            name += '.pdf'
            printer.setOutputFileName(name)
        
        printDialog = QPrintDialog(printer, self)
        if printDialog.exec_() == QDialog.Accepted:
            try:
                frame.print_(printer)
            except AttributeError:
                E5MessageBox.critical(self,
                    self.trUtf8("Eric Web Browser"),
                    self.trUtf8("""<p>Printing is not available due to a bug in PyQt4."""
                                """Please upgrade.</p>"""))
                return
    
    def printPreviewBrowser(self, browser = None):
        """
        Public slot called to show a print preview of the displayed file.
        
        @param browser reference to the browser to be printed (HelpBrowserWV)
        """
        from PyQt4.QtGui import QPrintPreviewDialog
        
        if browser is None:
            browser = self.currentBrowser()
        
        printer = QPrinter(mode = QPrinter.HighResolution)
        if Preferences.getPrinter("ColorMode"):
            printer.setColorMode(QPrinter.Color)
        else:
            printer.setColorMode(QPrinter.GrayScale)
        if Preferences.getPrinter("FirstPageFirst"):
            printer.setPageOrder(QPrinter.FirstPageFirst)
        else:
            printer.setPageOrder(QPrinter.LastPageFirst)
        printer.setPrinterName(Preferences.getPrinter("PrinterName"))
        
        self.__printPreviewBrowser = browser
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(self.__printPreview)
        preview.exec_()
    
    def __printPreview(self, printer):
        """
        Private slot to generate a print preview.
        
        @param printer reference to the printer object (QPrinter)
        """
        try:
            self.__printPreviewBrowser.print_(printer)
        except AttributeError:
            E5MessageBox.critical(self,
                self.trUtf8("Eric Web Browser"),
                self.trUtf8("""<p>Printing is not available due to a bug in PyQt4."""
                            """Please upgrade.</p>"""))
            return
    
    def __sourceChanged(self, url):
        """
        Private slot to handle a change of a browsers source.
        
        @param url URL of the new site (QUrl)
        """
        self.sourceChanged.emit(url)
    
    def __titleChanged(self, title):
        """
        Private slot to handle a change of a browsers title.
        
        @param title new title (string)
        """
        if title == "":
            title = self.currentBrowser().url().toString()
        
        self.setTabText(self.currentIndex(), self.__elide(title.replace("&", "&&")))
        self.setTabToolTip(self.currentIndex(), title)
        
        self.titleChanged.emit(title)
    
    def __elide(self, txt, mode = Qt.ElideRight, length = 40):
        """
        Private method to elide some text.
        
        @param txt text to be elided (string)
        @keyparam mode elide mode (Qt.TextElideMode)
        @keyparam length amount of characters to be used (integer)
        @return the elided text (string)
        """
        if mode == Qt.ElideNone or len(txt) < length:
            return txt
        elif mode == Qt.ElideLeft:
            return "...{0}".format(txt[-length:])
        elif mode == Qt.ElideMiddle:
            return "{0}...{1}".format(txt[:length // 2], txt[-(length // 2):])
        elif mode == Qt.ElideRight:
            return "{0}...".format(txt[:length])
        else:
            # just in case
            return txt
    
    def preferencesChanged(self):
        """
        Public slot to handle a change of preferences.
        """
        for browser in self.browsers():
            browser.preferencesChanged()
    
    def __loadStarted(self):
        """
        Private method to handle the loadStarted signal.
        """
        browser = self.sender()
        
        if browser is not None:
            index = self.indexOf(browser)
            anim = self.animationLabel(
                index, os.path.join(getConfig("ericPixDir"), "loading.gif"))
            if not anim:
                loading = QIcon(os.path.join(getConfig("ericPixDir"), "loading.gif"))
                self.setTabIcon(index, loading)
            self.showMessage.emit(self.trUtf8("Loading..."))
            
            self.__mainWindow.setLoadingActions(True)
    
    def __loadFinished(self, ok):
        """
        Private method to handle the loadFinished signal.
        
        @param ok flag indicating the result (boolean)
        """
        browser = self.sender()
        
        if browser is not None:
            index = self.indexOf(browser)
            self.resetAnimation(index)
            self.setTabIcon(index, browser.icon())
            if ok:
                self.showMessage.emit(self.trUtf8("Finished loading"))
            else:
                self.showMessage.emit(self.trUtf8("Failed to load"))
            
            self.__mainWindow.setLoadingActions(False)
    
    def __iconChanged(self):
        """
        Private slot to handle the icon change.
        """
        browser = self.sender()
        
        if browser is not None:
            self.__mainWindow.iconChanged(browser.icon())
            self.setTabIcon(self.indexOf(browser), browser.icon())
    
    def getSourceFileList(self):
        """
        Public method to get a list of all opened source files.
        
        @return dictionary with tab id as key and host/namespace as value
        """
        sourceList = {}
        for i in range(self.count()):
            browser = self.widget(i)
            if browser is not None and \
               browser.source().isValid():
                sourceList[i] = browser.source().host()
        
        return sourceList
    
    def shallShutDown(self):
        """
        Public method to check, if the application should be shut down.
        
        @return flag indicating a shut down (boolean)
        """
        if self.count() > 1:
            mb = E5MessageBox.E5MessageBox(E5MessageBox.Information, 
                self.trUtf8("Are you sure you want to close the window?"),
                self.trUtf8("""Are you sure you want to close the window?\n""" 
                            """You have %n tab(s) open.""", "", self.count()),
                modal = True,
                parent = self)
            if self.__mainWindow.fromEric:
                quitButton = mb.addButton(self.trUtf8("&Close"), E5MessageBox.AcceptRole)
                quitButton.setIcon(UI.PixmapCache.getIcon("close.png"))
            else:
                quitButton = mb.addButton(self.trUtf8("&Quit"), E5MessageBox.AcceptRole)
                quitButton.setIcon(UI.PixmapCache.getIcon("exit.png"))
            closeTabButton = mb.addButton(self.trUtf8("C&lose Current Tab"), 
                E5MessageBox.AcceptRole)
            closeTabButton.setIcon(UI.PixmapCache.getIcon("tabClose.png"))
            mb.addButton(E5MessageBox.Cancel)
            mb.exec_()
            if mb.clickedButton() == quitButton:
                return True
            else:
                if mb.clickedButton() == closeTabButton:
                    self.closeBrowser()
                return False
        
        return True