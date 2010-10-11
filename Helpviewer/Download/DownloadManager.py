# -*- coding: utf-8 -*-

"""
Module implementing the download manager class.
"""

from PyQt4.QtCore import pyqtSlot, QModelIndex, QFileInfo
from PyQt4.QtGui import QDialog, QStyle, QFileIconProvider
from PyQt4.QtNetwork import QNetworkRequest
from PyQt4.QtWebKit import QWebSettings

from E5Gui import E5MessageBox

from .Ui_DownloadManager import Ui_DownloadManager

from .DownloadItem import DownloadItem
from .DownloadModel import DownloadModel

import Helpviewer.HelpWindow

from Utilities.AutoSaver import AutoSaver
import Preferences

class DownloadManager(QDialog, Ui_DownloadManager):
    """
    Class implementing the download manager
    """
    RemoveNever               = 0
    RemoveExit                = 1
    RemoveSuccessFullDownload = 2
    
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.__saveTimer = AutoSaver(self, self.save)
        
        self.__model = DownloadModel(self)
        self.__manager = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        
        self.__iconProvider = None
        self.__removePolicy = DownloadManager.RemoveNever
        self.__downloads = []
        self.__downloadDirectory = ""
        self.__loaded = False
        
        self.setDownloadDirectory(Preferences.getUI("DownloadPath"))
        
        self.downloadsView.setShowGrid(False)
        self.downloadsView.verticalHeader().hide()
        self.downloadsView.horizontalHeader().hide()
        self.downloadsView.setAlternatingRowColors(True)
        self.downloadsView.horizontalHeader().setStretchLastSection(True)
        self.downloadsView.setModel(self.__model)
        
        self.__load()
    
    def shutdown(self):
        """
        Public method to stop the download manager.
        """
        self.__saveTimer.changeOccurred()
        self.__saveTimer.saveIfNeccessary()
        self.close()
    
    def activeDownloads(self):
        """
        Public method to get the number of active downloads.
        
        @return number of active downloads (integer)
        """
        count = 0
        
        for download in self.__downloads:
            if download.downloading():
                count += 1
        return count
    
    def allowQuit(self):
        """
        Public method to check, if it is ok to quit.
        
        @return flag indicating allowance to quit (boolean)
        """
        if self.activeDownloads() > 0:
            res = E5MessageBox.yesNo(self,
                self.trUtf8(""),
                self.trUtf8("""There are %n downloads in progress.\n"""
                            """Do you want to quit anyway?""", "", 
                            self.activeDownloads()),
                icon = E5MessageBox.Warning)
            if not res:
                self.show()
                return False
        return True
    
    def download(self, requestOrUrl, requestFileName = False):
        """
        Public method to download a file.
        
        @param requestOrUrl reference to a request object (QNetworkRequest)
            or a URL to be downloaded (QUrl)
        @keyparam requestFileName flag indicating to ask for the 
            download file name (boolean)
        """
        request = QNetworkRequest(requestOrUrl)
        if request.url().isEmpty():
            return
        self.handleUnsupportedContent(self.__manager.get(request), 
            requestFileName = requestFileName, 
            download = True)
    
    def handleUnsupportedContent(self, reply, requestFileName = False, 
                                 webPage = None, download = False):
        if reply is None or reply.url().isEmpty():
            return
        
        size = reply.header(QNetworkRequest.ContentLengthHeader)
        if size == 0:
            return
        
        itm = DownloadItem(reply = reply, requestFilename = requestFileName, 
            webPage = webPage, download = download, parent = self)
        self.__addItem(itm)
        
        if itm.canceledFileSelect():
            return
        
        if not self.isVisible():
            self.show()
        
        self.activateWindow()
        self.raise_()
    
    def __addItem(self, itm):
        """
        Private method to add a download to the list of downloads.
        
        @param itm reference to the download item (DownloadItem)
        """
        itm.statusChanged.connect(self.__updateRow)
        
        row = len(self.__downloads)
        self.__model.beginInsertRows(QModelIndex(), row, row)
        self.__downloads.append(itm)
        self.__model.endInsertRows()
        self.__updateItemCount()
        
        self.downloadsView.setIndexWidget(self.__model.index(row, 0), itm)
        icon = self.style().standardIcon(QStyle.SP_FileIcon)
        itm.setIcon(icon)
        self.downloadsView.setRowHeight(row, itm.sizeHint().height())
        # just in case the download finished before the constructor returned
        self.__updateRow(itm)
    
    def __updateRow(self, itm = None):
        """
        Private slot to update a download item.
        
        @param itm reference to the download item (DownloadItem)
        """
        if itm is None:
            itm = self.sender()
        
        if itm not in self.__downloads:
            return
        
        row = self.__downloads.index(itm)
        
        if self.__iconProvider is None:
            self.__iconProvider = QFileIconProvider()
        
        icon = self.__iconProvider.icon(QFileInfo(itm.fileName()))
        if icon.isNull():
            icon = self.style().standardIcon(QStyle.SP_FileIcon)
        itm.setIcon(icon)
        
        oldHeight = self.downloadsView.rowHeight(row)
        self.downloadsView.setRowHeight(row, 
            max(oldHeight, itm.minimumSizeHint().height()))
        
        remove = False
        globalSettings = QWebSettings.globalSettings()
        if not itm.downloading() and \
           globalSettings.testAttribute(QWebSettings.PrivateBrowsingEnabled):
            remove = True
        
        if itm.downloadedSuccessfully() and \
           self.removePolicy() == DownloadManager.RemoveSuccessFullDownload:
            remove = True
        
        if remove:
            self.__model.removeRow(row)
        
        self.cleanupButton.setEnabled(
            (len(self.__downloads) - self.activeDownloads()) > 0)
    
    def removePolicy(self):
        """
        Public method to get the remove policy.
        
        @return remove policy (integer)
        """
        return self.__removePolicy
    
    def setRemovePolicy(self, policy):
        """
        Public method to set the remove policy.
        
        @param policy policy to be set 
            (DownloadManager.RemoveExit, DownloadManager.RemoveNever, 
             DownloadManager.RemoveSuccessFullDownload)
        """
        assert policy in (DownloadManager.RemoveExit, DownloadManager.RemoveNever, 
                          DownloadManager.RemoveSuccessFullDownload)
        
        if policy == self.__removePolicy:
            return
        
        self.__removePolicy = policy
        self.__saveTimer.changeOccurred()
    
    def save(self):
        """
        Public method to save the download settings.
        """
        if not self.__loaded:
            return
        
        Preferences.setHelp("DownloadManagerRemovePolicy", self.__removePolicy)
        Preferences.setHelp("DownloadManagerSize", self.size())
        Preferences.setHelp("DownloadManagerPosition", self.pos())
        if self.__removePolicy == DownloadManager.RemoveExit:
            return
        
        downloads = []
        for download in self.__downloads:
            downloads.append(download.getData())
        Preferences.setHelp("DownloadManagerDownloads", downloads)
    
    def __load(self):
        """
        Public method to load the download settings.
        """
        if self.__loaded:
            return
        
        self.__removePolicy = Preferences.getHelp("DownloadManagerRemovePolicy")
        size = Preferences.getHelp("DownloadManagerSize")
        if size.isValid():
            self.resize(size)
        pos = Preferences.getHelp("DownloadManagerPosition")
        self.move(pos)
        
        downloads = Preferences.getHelp("DownloadManagerDownloads")
        for download in downloads:
            if not download[0].isEmpty() and \
               download[1] != "":
                itm = DownloadItem(parent = self)
                itm.setData(download)
                self.__addItem(itm)
        self.cleanupButton.setEnabled(
            (len(self.__downloads) - self.activeDownloads()) > 0)
        
        self.__loaded = True
    
    def cleanup(self):
        """
        Public slot to cleanup the downloads.
        """
        self.on_cleanupButton_clicked()
    
    @pyqtSlot()
    def on_cleanupButton_clicked(self):
        """
        Private slot cleanup the downloads.
        """
        if len(self.__downloads) == 0:
            return
        
        self.__model.removeRows(0, len(self.__downloads))
        self.__updateItemCount()
        if len(self.__downloads) == 0 and \
           self.__iconProvider is not None:
               self.__iconProvider = None
        
        self.__saveTimer.changeOccurred()
    
    def __updateItemCount(self):
        """
        Private method to update the count label.
        """
        count = len(self.__downloads)
        self.countLabel.setText(self.trUtf8("%n Download(s)", "", count))
    
    def setDownloadDirectory(self, directory):
        """
        Public method to set the current download directory.
        
        @param directory current download directory (string)
        """
        self.__downloadDirectory = directory
        if self.__downloadDirectory != "":
            self.__downloadDirectory += "/"
    
    def downloadDirectory(self):
        """
        Public method to get the current download directory.
        
        @return current download directory (string)
        """
        return self.__downloadDirectory
    
    def count(self):
        """
        Public method to get the number of downloads.
        
        @return number of downloads (integer)
        """
        return len(self.__downloads)
    
    def downloads(self):
        """
        Public method to get a reference to the downloads.
        
        @return reference to the downloads (list of DownloadItem)
        """
        return self.__downloads
    
    def changeOccurred(self):
        """
        Public method to signal a change.
        """
        self.__saveTimer.changeOccurred()
