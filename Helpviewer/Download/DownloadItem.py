# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a widget controlling a download.
"""

from PyQt4.QtCore import pyqtSlot, pyqtSignal, Qt, QTime, QFile, QFileInfo, QUrl, \
    QIODevice
from PyQt4.QtGui import QWidget, QPalette, QStyle, QDesktopServices, QFileDialog
from PyQt4.QtNetwork import QNetworkRequest, QNetworkReply

from E5Gui import E5MessageBox

from .Ui_DownloadItem import Ui_DownloadItem

import Helpviewer.HelpWindow

from .DownloadUtilities import timeString, dataString

import UI.PixmapCache
import Preferences

class DownloadItem(QWidget, Ui_DownloadItem):
    """
    Class implementing a widget controlling a download.
    
    @signal statusChanged() emitted upon a status change of a download
    @signal downloadFinished() emitted when a download finished
    @signal progress(int, int) emitted to signal the download progress
    """
    statusChanged = pyqtSignal()
    downloadFinished = pyqtSignal()
    progress = pyqtSignal(int, int)
    
    def __init__(self, reply = None, requestFilename = False, webPage = None, 
                 download = False, parent = None):
        """
        Constructor
        
        @param reply reference to the network reply object (QNetworkReply)
        @param requestFilename flag indicating to ask the user for a filename (boolean)
        @param webPage reference to the web page object the download originated 
            from (QWebPage)
        @param download flag indicating a download operation (boolean)
        @param parent reference to the parent widget (QWidget)
        """
        QWidget.__init__(self, parent)
        self.setupUi(self)
        
        p = self.infoLabel.palette()
        p.setColor(QPalette.Text, Qt.darkGray)
        self.infoLabel.setPalette(p)
        
        self.progressBar.setMaximum(0)
        
        self.tryAgainButton.setIcon(UI.PixmapCache.getIcon("restart.png"))
        self.tryAgainButton.setEnabled(False)
        self.tryAgainButton.setVisible(False)
        self.stopButton.setIcon(UI.PixmapCache.getIcon("stopLoading.png"))
        self.openButton.setIcon(UI.PixmapCache.getIcon("open.png"))
        self.openButton.setEnabled(False)
        self.openButton.setVisible(False)
        
        icon = self.style().standardIcon(QStyle.SP_FileIcon)
        self.fileIcon.setPixmap(icon.pixmap(48, 48))
        
        self.__reply = reply
        self.__requestFilename = requestFilename
        self.__page = webPage
        self.__pageUrl = webPage and webPage.mainFrame().url() or QUrl()
        self.__toDownload = download
        self.__bytesReceived = 0
        self.__bytesTotal = -1
        self.__downloadTime = QTime()
        self.__output = QFile()
        self.__fileName = ""
        self.__startedSaving = False
        self.__finishedDownloading = False
        self.__gettingFileName = False
        self.__canceledFileSelect = False
        self.__autoOpen = False
        
        if not requestFilename:
            self.__requestFilename = Preferences.getUI("RequestDownloadFilename")
        
        self.__initialize()
    
    def __initialize(self, tryAgain = False):
        """
        Private method to (re)initialize the widget.
        
        @param tryAgain flag indicating a retry (boolean)
        """
        if self.__reply is None:
            return
        
        self.__startedSaving = False
        self.__finishedDownloading = False
        self.__bytesReceived = 0
        self.__bytesTotal = -1
        
        self.openButton.setEnabled(False)
        self.openButton.setVisible(False)
        
        # start timer for the download estimation
        self.__downloadTime.start()
        
        # attach to the reply object
        self.__url = self.__reply.url()
        self.__reply.setParent(self)
        self.__reply.readyRead[()].connect(self.__readyRead)
        self.__reply.error.connect(self.__networkError)
        self.__reply.downloadProgress.connect(self.__downloadProgress)
        self.__reply.metaDataChanged.connect(self.__metaDataChanged)
        self.__reply.finished[()].connect(self.__finished)
        
        # reset info
        self.infoLabel.clear()
        self.progressBar.setValue(0)
        self.__getFileName()
        
        if self.__reply.error() != QNetworkReply.NoError:
            self.__networkError()
            self.__finished()
    
    def __getFileName(self):
        """
        Private method to get the filename to save to from the user.
        
        @return flag indicating success (boolean)
        """
        if self.__gettingFileName:
            return
        
        downloadDirectory = Helpviewer.HelpWindow.HelpWindow\
            .downloadManager().downloadDirectory()
        
        if self.__fileName:
            fileName = self.__fileName
            self.__toDownload = True
            ask = False
        else:
            defaultFileName = self.__saveFileName(downloadDirectory)
            fileName = defaultFileName
            ask = True
        self.__autoOpen = False
        if not self.__toDownload:
            res = E5MessageBox.question(self,
                self.trUtf8("Downloading"),
                self.trUtf8("""<p>You are about to download the file <b>{0}</b>.</p>"""
                            """<p>What do you want to do?</p>""").format(fileName),
                E5MessageBox.StandardButtons(
                    E5MessageBox.Open | \
                    E5MessageBox.Save | \
                    E5MessageBox.Cancel))
            if res == E5MessageBox.Cancel:
                self.progressBar.setVisible(False)
                self.__reply.close()
                self.on_stopButton_clicked()
                self.filenameLabel.setText(self.trUtf8("Download canceled: {0}").format(
                    QFileInfo(defaultFileName).fileName()))
                self.__canceledFileSelect = True
                return
            
            self.__autoOpen = res == E5MessageBox.Open
            fileName = QDesktopServices.storageLocation(QDesktopServices.TempLocation) + \
                        '/' + QFileInfo(fileName).completeBaseName()
        
        if ask and not self.__autoOpen and self.__requestFilename:
            self.__gettingFileName = True
            fileName = QFileDialog.getSaveFileName(
                None,
                self.trUtf8("Save File"),
                defaultFileName,
                "")
            self.__gettingFileName = False
            if not fileName:
                self.progressBar.setVisible(False)
                self.__reply.close()
                self.on_stopButton_clicked()
                self.filenameLabel.setText(self.trUtf8("Download canceled: {0}")\
                    .format(QFileInfo(defaultFileName).fileName()))
                self.__canceledFileSelect = True
                return
        
        fileInfo = QFileInfo(fileName)
        Helpviewer.HelpWindow.HelpWindow.downloadManager().setDownloadDirectory(
            fileInfo.absoluteDir().absolutePath())
        self.filenameLabel.setText(fileInfo.fileName())
        
        self.__output.setFileName(fileName)
        self.__fileName = fileName
        
        # check file path for saving
        saveDirPath = QFileInfo(self.__fileName).dir()
        if not saveDirPath.exists():
            if not saveDirPath.mkpath(saveDirPath.absolutePath()):
                self.progressBar.setVisible(False)
                self.on_stopButton_clicked()
                self.infoLabel.setText(
                    self.trUtf8("Download directory ({0}) couldn't be created.")\
                    .format(saveDirPath.absolutePath()))
                return
        
        self.filenameLabel.setText(QFileInfo(self.__fileName).fileName())
        if self.__requestFilename:
            self.__readyRead()
    
    def __saveFileName(self, directory):
        """
        Private method to calculate a name for the file to download.
        
        @param directory name of the directory to store the file into (string)
        @return proposed filename (string)
        """
        path = ""
        if self.__reply.hasRawHeader("Content-Disposition"):
            header = bytes(self.__reply.rawHeader("Content-Disposition")).decode()
            if header:
                pos = header.find("filename=")
                if pos != -1:
                    path = header[pos + 9:]
                    if path.startswith('"') and path.endswith('"'):
                        path = path[1:-1]
        if not path:
            path = self.__url.path()
        
        info = QFileInfo(path)
        baseName = info.completeBaseName()
        endName = info.suffix()
        
        if not baseName:
            baseName = "unnamed_download"
        
        name = directory + baseName
        if endName:
            name += '.' + endName
        i = 1
        while QFile.exists(name):
            # file exists already, don't overwrite
            name = directory + baseName + ('-{0:d}'.format(i))
            if endName:
                name += '.' + endName
            i += 1
        return name
    
    @pyqtSlot()
    def on_tryAgainButton_clicked(self):
        """
        Private slot to retry the download.
        """
        self.retry()
    
    def retry(self):
        """
        Public slot to retry the download.
        """
        if not self.tryAgainButton.isEnabled():
            return
        
        self.tryAgainButton.setEnabled(False)
        self.tryAgainButton.setVisible(False)
        self.openButton.setEnabled(False)
        self.openButton.setVisible(False)
        self.stopButton.setEnabled(True)
        self.stopButton.setVisible(True)
        self.progressBar.setVisible(True)
        
        if self.__page:
            nam = self.__page.networkAccessManager()
        else:
            nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.get(QNetworkRequest(self.__url))
        if self.__output.exists():
            self.__output.remove()
        self.__output = QFile()
        self.__reply = reply
        self.__initialize(tryAgain = True)
        self.statusChanged.emit()
    
    @pyqtSlot()
    def on_stopButton_clicked(self):
        """
        Private slot to stop the download.
        """
        self.cancelDownload()
    
    def cancelDownload(self):
        """
        Public slot to stop the download.
        """
        self.setUpdatesEnabled(False)
        self.stopButton.setEnabled(False)
        self.stopButton.setVisible(False)
        self.tryAgainButton.setEnabled(True)
        self.tryAgainButton.setVisible(True)
        self.openButton.setEnabled(False)
        self.openButton.setVisible(False)
        self.setUpdatesEnabled(True)
        self.__reply.abort()
        self.downloadFinished.emit()
    
    @pyqtSlot()
    def on_openButton_clicked(self):
        """
        Private slot to open the downloaded file.
        """
        self.openFile()
    
    def openFile(self):
        """
        Public slot to open the downloaded file.
        """
        info = QFileInfo(self.__fileName)
        url = QUrl.fromLocalFile(info.absoluteFilePath())
        QDesktopServices.openUrl(url)
    
    def openFolder(self):
        """
        Public slot to open the folder containing the downloaded file.
        """
        info = QFileInfo(self.__fileName)
        url = QUrl.fromLocalFile(info.absolutePath())
        QDesktopServices.openUrl(url)
    
    def __readyRead(self):
        """
        Private slot to read the available data.
        """
        if self.__requestFilename and not self.__output.fileName():
            return
        
        if not self.__output.isOpen():
            # in case someone else has already put a file there
            if not self.__requestFilename:
                self.__getFileName()
            if not self.__output.open(QIODevice.WriteOnly):
                self.infoLabel.setText(self.trUtf8("Error opening save file: {0}")\
                    .format(self.__output.errorString()))
                self.on_stopButton_clicked()
                self.statusChanged.emit()
                return
            self.statusChanged.emit()
        
        bytesWritten = self.__output.write(self.__reply.readAll())
        if bytesWritten == -1:
            self.infoLabel.setText(self.trUtf8("Error saving: {0}")\
                .format(self.__output.errorString()))
            self.on_stopButton_clicked()
        else:
            self.__startedSaving = True
            if self.__finishedDownloading:
                self.__finished()
    
    def __networkError(self):
        """
        Private slot to handle a network error.
        """
        self.infoLabel.setText(self.trUtf8("Network Error: {0}")\
            .format(self.__reply.errorString()))
        self.tryAgainButton.setEnabled(True)
        self.tryAgainButton.setVisible(True)
        self.downloadFinished.emit()
    
    def __metaDataChanged(self):
        """
        Private slot to handle a change of the meta data.
        """
        locationHeader = self.__reply.header(QNetworkRequest.LocationHeader)
        if locationHeader and locationHeader.isValid():
            self.__url = QUrl(locationHeader)
            self.__reply = Helpviewer.HelpWindow.HelpWindow.networkAccessManager().get(
                           QNetworkRequest(self.__url))
            self.initialize()
    
    def __downloadProgress(self, bytesReceived, bytesTotal):
        """
        Private method to show the download progress.
        
        @param bytesReceived number of bytes received (integer)
        @param bytesTotal number of total bytes (integer)
        """
        self.__bytesReceived = bytesReceived
        self.__bytesTotal = bytesTotal
        currentValue = 0
        totalValue = 0
        if bytesTotal > 0:
            currentValue = bytesReceived * 100 / bytesTotal
            totalValue = 100
        self.progressBar.setValue(currentValue)
        self.progressBar.setMaximum(totalValue)
        
        self.progress.emit(currentValue, totalValue)
        self.__updateInfoLabel()
    
    def bytesTotal(self):
        """
        Public method to get the total number of bytes of the download.
        
        @return total number of bytes (integer)
        """
        if self.__bytesTotal == -1:
            self.__bytesTotal = self.__reply.header(QNetworkRequest.ContentLengthHeader)
            if self.__bytesTotal is None:
                self.__bytesTotal = -1
        return self.__bytesTotal
    
    def bytesReceived(self):
        """
        Public method to get the number of bytes received.
        
        @return number of bytes received (integer)
        """
        return self.__bytesReceived
    
    def remainingTime(self):
        """
        Public method to get an estimation for the remaining time.
        
        @return estimation for the remaining time (float)
        """
        if not self.downloading():
            return -1.0
        
        if self.bytesTotal() == -1:
            return -1.0
        
        timeRemaining = (self.bytesTotal() - self.bytesReceived()) / self.currentSpeed()
        
        # ETA should never be 0
        if timeRemaining == 0:
            timeRemaining = 1
        
        return timeRemaining
    
    def currentSpeed(self):
        """
        Public method to get an estimation for the download speed.
        
        @return estimation for the download speed (float)
        """
        if not self.downloading():
            return -1.0
        
        return self.__bytesReceived * 1000.0 / self.__downloadTime.elapsed()
    
    def __updateInfoLabel(self):
        """
        Private method to update the info label.
        """
        if self.__reply.error() != QNetworkReply.NoError:
            return
        
        bytesTotal = self.bytesTotal()
        running = not self.downloadedSuccessfully()
        
        speed = self.currentSpeed()
        timeRemaining = self.remainingTime()
        
        info = ""
        if running:
            remaining = ""
            
            if bytesTotal > 0:
                remaining = timeString(timeRemaining)
            
            info = self.trUtf8("{0} of {1} ({2}/sec) - {3}")\
                .format(
                    dataString(self.__bytesReceived), 
                    bytesTotal == -1 and self.trUtf8("?") \
                                     or dataString(bytesTotal), 
                    dataString(int(speed)), 
                    remaining)
        else:
            if self.__bytesReceived == bytesTotal or bytesTotal == -1:
                info = self.trUtf8("{0} downloaded")\
                    .format(dataString(self.__output.size()))
            else:
                info = self.trUtf8("{0} of {1} - Stopped")\
                    .format(dataString(self.__bytesReceived), 
                            dataString(bytesTotal))
        self.infoLabel.setText(info)
    
    def downloading(self):
        """
        Public method to determine, if a download is in progress.
        
        @return flag indicating a download is in progress (boolean)
        """
        return self.stopButton.isEnabled()
    
    def downloadedSuccessfully(self):
        """
        Public method to check for a successful download.
        
        @return flag indicating a successful download (boolean)
        """
        return self.stopButton.isHidden() and self.tryAgainButton.isHidden()
    
    def downloadCanceled(self):
        """
        Public method to check, if the download was cancelled.
        
        @return flag indicating a canceled download (boolean)
        """
        return self.tryAgainButton.isEnabled()
    
    def __finished(self):
        """
        Private slot to handle the download finished.
        """
        self.__finishedDownloading = True
        if not self.__startedSaving:
            return
        
        noError = self.__reply.error() == QNetworkReply.NoError
        
        self.progressBar.setVisible(False)
        self.stopButton.setEnabled(False)
        self.stopButton.setVisible(False)
        self.openButton.setEnabled(noError)
        self.openButton.setVisible(noError)
        self.__output.close()
        self.__updateInfoLabel()
        self.statusChanged.emit()
        self.downloadFinished.emit()
        
        if self.__autoOpen:
            self.__open()
    
    def canceledFileSelect(self):
        """
        Public method to check, if the user canceled the file selection.
        
        @return flag indicating cancellation (boolean)
        """
        return self.__canceledFileSelect
    
    def setIcon(self, icon):
        """
        Public method to set the download icon.
        
        @param icon reference to the icon to be set (QIcon)
        """
        self.fileIcon.setPixmap(icon.pixmap(48, 48))
    
    def fileName(self):
        """
        Public method to get the name of the output file.
        
        @return name of the output file (string)
        """
        return self.__fileName
    
    def absoluteFilePath(self):
        """
        Public method to get the absolute path of the output file.
        
        @return absolute path of the output file (string)
        """
        return QFileInfo(self.__fileName).absoluteFilePath()
    
    def getData(self):
        """
        Public method to get the relevant download data.
        
        @return tuple of URL, save location, flag and the
            URL of the related web page (QUrl, string, boolean,QUrl)
        """
        return (self.__url, QFileInfo(self.__fileName).filePath(), 
                self.downloadedSuccessfully(), self.__pageUrl)
    
    def setData(self, data):
        """
        Public method to set the relevant download data.
        
        @param data tuple of URL, save location, flag and the
            URL of the related web page (QUrl, string, boolean, QUrl)
        """
        self.__url = data[0]
        self.__fileName = data[1]
        self.__pageUrl = data[3]
        
        self.filenameLabel.setText(QFileInfo(self.__fileName).fileName())
        self.infoLabel.setText(self.__fileName)
        
        self.stopButton.setEnabled(False)
        self.stopButton.setVisible(False)
        self.openButton.setEnabled(data[2])
        self.openButton.setVisible(data[2])
        self.tryAgainButton.setEnabled(not data[2])
        self.tryAgainButton.setVisible(not data[2])
        self.progressBar.setVisible(False)
    
    def getInfoData(self):
        """
        Public method to get the text of the info label.
        
        @return text of the info label (string)
        """
        return self.infoLabel.text()
    
    def getPageUrl(self):
        """
        Public method to get the URL of the download page.
        
        @return URL of the download page (QUrl)
        """
        return self.__pageUrl