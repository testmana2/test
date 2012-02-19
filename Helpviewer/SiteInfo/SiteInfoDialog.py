# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show some information about a site.
"""

import os

from PyQt4.QtCore import pyqtSlot, QUrl, Qt, QFile
from PyQt4.QtGui import QDialog, QTreeWidgetItem, QPixmap, QGraphicsScene, QMenu, \
    QCursor, QApplication, QFileDialog
from PyQt4.QtWebKit import QWebSettings

from E5Gui import E5MessageBox, E5FileDialog

from .Ui_SiteInfoDialog import Ui_SiteInfoDialog

from ..Download.DownloadUtilities import dataString

import Helpviewer.HelpWindow

import UI.PixmapCache


class SiteInfoDialog(QDialog, Ui_SiteInfoDialog):
    """
    Class implementing a dialog to show some information about a site.
    """
    okStyle = "QLabel { color : white; background-color : green; }"
    nokStyle = "QLabel { color : white; background-color : red; }"
    
    def __init__(self, browser, parent=None):
        """
        Constructor
        
        @param browser reference to the browser window (HelpBrowser)
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        # put icons
        self.tabWidget.setTabIcon(0, UI.PixmapCache.getIcon("siteinfo-general.png"))
        self.tabWidget.setTabIcon(1, UI.PixmapCache.getIcon("siteinfo-media.png"))
        self.tabWidget.setTabIcon(2, UI.PixmapCache.getIcon("siteinfo-security.png"))
        
        frame = browser.page().mainFrame()
        title = browser.title()
        sslInfo = browser.page().getSslInfo()
        
        # populate General tab
        self.heading.setText("<b>{0}</b>".format(title))
        self.siteAddressLabel.setText(frame.baseUrl().toString())
        self.sizeLabel.setText(dataString(browser.page().totalBytes()))
        encoding = ""
        
        # populate Meta tags
        meta = frame.findAllElements("meta")
        for element in meta:
            content = element.attribute("content")
            name = element.attribute("name")
            if not name:
                name = element.attribute("http-equiv")
            if element.attribute("charset"):
                encoding = element.attribute("charset")
            if "charset=" in content:
                encoding = content[content.index("charset=") + 8:]
            
            if not content or not name:
                continue
            
            QTreeWidgetItem(self.tagsTree, [name, content])
        for col in range(self.tagsTree.columnCount()):
            self.tagsTree.resizeColumnToContents(col)
        
        if not encoding:
            encoding = QWebSettings.globalSettings().defaultTextEncoding()
        self.encodingLabel.setText(encoding)
        
        # populate the Security info and the Security tab
        if sslInfo is not None and sslInfo.isValid():
            self.securityLabel.setStyleSheet(SiteInfoDialog.okStyle)
            self.securityLabel.setText('<b>Connection is encrypted.</b>')
            self.sslWidget.showCertificate(sslInfo)
            self.securityDetailsButton.setEnabled(True)
        else:
            self.securityLabel.setStyleSheet(SiteInfoDialog.nokStyle)
            self.securityLabel.setText('<b>Connection is not encrypted.</b>')
            self.securityDetailsButton.setEnabled(False)
        
        # populate Media tab
        images = frame.findAllElements("img")
        for element in images:
            src = element.attribute("src")
            alt = element.attribute("alt")
            if src and src.startswith("data:"):
                continue
            if not alt:
                if src.find("/") == -1:
                    alt = src
                else:
                    pos = src.find("/")
                    alt = src[pos + 1:]
            
            if not src or not alt:
                continue
            
            QTreeWidgetItem(self.imagesTree, [alt, src])
        for col in range(self.imagesTree.columnCount()):
            self.imagesTree.resizeColumnToContents(col)
        if self.imagesTree.columnWidth(0) > 300:
            self.imagesTree.setColumnWidth(0, 300)
        self.imagesTree.setCurrentItem(self.imagesTree.topLevelItem(0))
        self.imagesTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.imagesTree.customContextMenuRequested.connect(
            self.__imagesTreeContextMenuRequested)
    
    @pyqtSlot()
    def on_securityDetailsButton_clicked(self):
        """
        Private slot to show security details.
        """
        self.tabWidget.setCurrentIndex(2)
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_imagesTree_currentItemChanged(self, current, previous):
        """
        Private slot to show a preview of the selected image.
        
        @param current current image entry (QTreeWidgetItem)
        @param previous old current entry (QTreeWidgetItem)
        """
        if current is None:
            return
        
        imageUrl = QUrl(current.text(1))
        if not imageUrl.host():
            imageUrl.setHost(QUrl(self.siteAddressLabel.text()).host())
            imageUrl.setScheme(QUrl(self.siteAddressLabel.text()).scheme())
        
        cache = Helpviewer.HelpWindow.HelpWindow.networkAccessManager().cache()
        if cache:
            cacheData = cache.data(imageUrl)
        else:
            cacheData = None
        pixmap = QPixmap()
        invalidPixmap = False
        scene = QGraphicsScene(self.imagePreview)
        if not cacheData:
            invalidPixmap = True
        else:
            pixmap.loadFromData(cacheData.readAll())
            if pixmap.isNull():
                invalidPixmap = True
        if invalidPixmap:
            scene.addText(self.trUtf8("Preview not available."))
        else:
            scene.addPixmap(pixmap)
        self.imagePreview.setScene(scene)
    
    def __imagesTreeContextMenuRequested(self, pos):
        """
        Private slot to show a context menu for the images list.
        
        @param pos position for the menu (QPoint)
        """
        itm = self.imagesTree.itemAt(pos)
        if itm is None:
            return
        
        menu = QMenu()
        act = menu.addAction(self.trUtf8("Copy Image Location to Clipboard"),
            self.__copyAction)
        act.setData(itm.text(1))
        act = menu.addAction(self.trUtf8("Copy Image Name to Clipboard"),
            self.__copyAction)
        act.setData(itm.text(0))
        menu.addSeparator()
        act = menu.addAction(self.trUtf8("Save Image"), self.__saveImage)
        act.setData(self.imagesTree.indexOfTopLevelItem(itm))
        menu.exec_(QCursor.pos())
    
    def __copyAction(self):
        """
        Private slot to copy the image URL or the image name to the clipboard.
        """
        act = self.sender()
        QApplication.clipboard().setText(act.data())
    
    def __saveImage(self):
        """
        Private slot to save the selected image to disk.
        """
        act = self.sender()
        index = act.data()
        itm = self.imagesTree.topLevelItem(index)
        if itm is None:
            return
        
        imageUrl = QUrl(itm.text(1))
        if not imageUrl.host():
            imageUrl.setHost(QUrl(self.siteAddressLabel.text()).host())
            imageUrl.setScheme(QUrl(self.siteAddressLabel.text()).scheme())
        
        cache = Helpviewer.HelpWindow.HelpWindow.networkAccessManager().cache()
        if cache:
            cacheData = cache.data(imageUrl)
        else:
            cacheData = None
        if not cacheData:
            E5MessageBox.critical(self,
                self.trUtf8("Save Image"),
                self.trUtf8("""This image is not available."""))
            return
        
        downloadDirectory = Helpviewer.HelpWindow.HelpWindow\
            .downloadManager().downloadDirectory()
        fn = os.path.join(downloadDirectory, os.path.basename(itm.text(1)))
        filename = E5FileDialog.getSaveFileName(
            self,
            self.trUtf8("Save Image"),
            fn,
            self.trUtf8("All Files (*)"),
            QFileDialog.Options(QFileDialog.DontConfirmOverwrite))
        
        if not filename:
            return
        
        f = QFile(filename)
        if not f.open(QFile.WriteOnly):
            E5MessageBox.critical(self,
                self.trUtf8("Save Image"),
                self.trUtf8(
                    """<p>Cannot write to file <b>{0}</b>.</p>""".format(filename)))
            return
        f.write(cacheData.readAll())
        f.close()