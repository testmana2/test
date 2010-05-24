# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the download dialog.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import QNetworkReply, QNetworkAccessManager, QNetworkRequest

import Preferences

import Helpviewer.HelpWindow

from .Ui_DownloadDialog import Ui_DownloadDialog

class DownloadDialog(QWidget, Ui_DownloadDialog):
    """
    Class implementing the download dialog.
    
    @signal done() emitted just before the dialog is closed
    """
    done = pyqtSignal()
    
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
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.__windowTitleTemplate = self.trUtf8("Eric5 Download {0}")
        self.setWindowTitle(self.__windowTitleTemplate.format(""))
        
        self.__tryAgainButton = \
            self.buttonBox.addButton(self.trUtf8("Try Again"), 
                                     QDialogButtonBox.ActionRole)
        self.__stopButton = \
            self.buttonBox.addButton(self.trUtf8("Stop"), QDialogButtonBox.ActionRole)
        self.__openButton = self.buttonBox.button(QDialogButtonBox.Open)
        self.__closeButton = self.buttonBox.button(QDialogButtonBox.Close)
        
        self.__tryAgainButton.setEnabled(False)
        self.__closeButton.setEnabled(False)
        self.__openButton.setEnabled(False)
        self.keepOpenCheckBox.setChecked(True)
        
        icon = self.style().standardIcon(QStyle.SP_FileIcon)
        self.fileIcon.setPixmap(icon.pixmap(48, 48))
        
        self.__reply = reply
        self.__requestFilename = requestFilename
        self.__page = webPage
        self.__toDownload = download
        self.__bytesReceived = 0
        self.__downloadTime = QTime()
        self.__output = QFile()
    
    def initialize(self):
        """
        Public method to (re)initialize the dialog.
        
        @return flag indicating success (boolean)
        """
        if self.__reply is None:
            return
        
        self.__startedSaving = False
        self.__downloadFinished = False
        
        self.__url = self.__reply.url()
        self.__reply.setParent(self)
        self.connect(self.__reply, SIGNAL("readyRead()"), self.__readyRead)
        self.connect(self.__reply, SIGNAL("error(QNetworkReply::NetworkError)"), 
                     self.__networkError)
        self.connect(self.__reply, SIGNAL("downloadProgress(qint64, qint64)"), 
                     self.__downloadProgress)
        self.connect(self.__reply, SIGNAL("metaDataChanged()"), 
                     self.__metaDataChanged)
        self.connect(self.__reply, SIGNAL("finished()"), self.__finished)
        
        # reset info
        self.infoLabel.clear()
        self.progressBar.setValue(0)
        if not self.__getFileName():
            return False
        
        # start timer for the download estimation
        self.__downloadTime.start()
        
        if self.__reply.error() != QNetworkReply.NoError:
            self.__networkError()
            self.__finished()
            return False
        
        return True
    
    def __getFileName(self):
        """
        Private method to get the filename to save to from the user.
        
        @return flag indicating success (boolean)
        """
        downloadDirectory = Preferences.getUI("DownloadPath")
        if not downloadDirectory:
            downloadDirectory = \
                QDesktopServices.storageLocation(QDesktopServices.DocumentsLocation)
        if downloadDirectory:
            downloadDirectory += '/'
        
        defaultFileName = self.__saveFileName(downloadDirectory)
        fileName = defaultFileName
        self.__autoOpen = False
        if not self.__toDownload:
            res = QMessageBox.question(None,
                self.trUtf8("Downloading"),
                self.trUtf8("""<p>You are about to download the file <b>{0}</b>.</p>"""
                            """<p>What do you want to do?</p>""").format(fileName),
                QMessageBox.StandardButtons(\
                    QMessageBox.Open | \
                    QMessageBox.Save | \
                    QMessageBox.Cancel))
            if res == QMessageBox.Cancel:
                self.__stop()
                self.close()
                return False
            
            self.__autoOpen = res == QMessageBox.Open
            fileName = QDesktopServices.storageLocation(QDesktopServices.TempLocation) + \
                        '/' + fileName
        
        if not self.__autoOpen and self.__requestFilename:
            fileName = QFileDialog.getSaveFileName(
                None,
                self.trUtf8("Save File"),
                defaultFileName,
                "")
            if not fileName:
                self.__reply.close()
                if not self.keepOpenCheckBox.isChecked():
                    self.close()
                    return False
                else:
                    self.filenameLabel.setText(self.trUtf8("Download canceled: {0}")\
                        .format(QFileInfo(defaultFileName).fileName()))
                    self.__stop()
                    return True
        
        self.__output.setFileName(fileName)
        self.filenameLabel.setText(QFileInfo(self.__output.fileName()).fileName())
        if self.__requestFilename:
            self.__readyRead()
        
        return True
    
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
            name = directory + baseName + ('-%d' % i)
            if endName:
                name += '.' + endName
            i += 1
        return name
    
    @pyqtSlot(QAbstractButton)
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.
        
        @param button button that was clicked (QAbstractButton)
        """
        if button == self.__closeButton:
            self.close()
        elif button == self.__openButton:
            self.__open()
        elif button == self.__stopButton:
            self.__stop()
        elif button == self.__tryAgainButton:
            self.__tryAgain()
    
    def __stop(self):
        """
        Private slot to stop the download.
        """
        self.__stopButton.setEnabled(False)
        self.__closeButton.setEnabled(True)
        self.__tryAgainButton.setEnabled(True)
        self.__reply.abort()
    
    def __open(self):
        """
        Private slot to open the downloaded file.
        """
        info = QFileInfo(self.__output)
        url = QUrl.fromLocalFile(info.absoluteFilePath())
        QDesktopServices.openUrl(url)
    
    def __tryAgain(self):
        """
        Private slot to retry the download.
        """
        self.__tryAgainButton.setEnabled(False)
        self.__closeButton.setEnabled(False)
        self.__stopButton.setEnabled(True)
        
        if self.__page:
            nam = self.__page.networkAccessManager()
        else:
            nam = QNetworkAccessManager()
        reply = nam.get(QNetworkRequest(self.__url))
        if self.__output.exists():
            self.__output.remove()
        self.__reply = reply
        self.initialize()
    
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
                self.__stopButton.click()
                return
        
        bytesWritten = self.__output.write(self.__reply.readAll())
        if bytesWritten == -1:
            self.infoLabel.setText(self.trUtf8("Error saving: {0}")\
                .format(self.__output.errorString()))
            self.__stopButton.click()
        else:
            size = self.__reply.header(QNetworkRequest.ContentLengthHeader)
            if size == bytesWritten:
                self.__downloadProgress(size, size)
                self.__downloadFinished = True
            self.__startedSaving = True
            if self.__downloadFinished:
                self.__finished()
    
    def __networkError(self):
        """
        Private slot to handle a network error.
        """
        if self.__reply.error() != QNetworkReply.OperationCanceledError:
            self.infoLabel.setText(self.trUtf8("Network Error: {0}")\
                .format(self.__reply.errorString()))
            self.__tryAgainButton.setEnabled(True)
            self.__closeButton.setEnabled(True)
            self.__openButton.setEnabled(False)
    
    def __metaDataChanged(self):
        """
        Private slot to handle a change of the meta data.
        """
        locationHeader = self.__reply.header(QNetworkRequest.LocationHeader)
        if locationHeader.isValid():
            self.__url = locationHeader
            self.__reply = Helpviewer.HelpWindow.HelpWindow.networkAccessManager().get(
                           QNetworkRequest(self.__url))
            self.initialize()
    
    def __downloadProgress(self, received, total):
        """
        Private method show the download progress.
        
        @param received number of bytes received (integer)
        @param total number of total bytes (integer)
        """
        self.__bytesReceived = received
        if total == -1:
            self.progressBar.setMaximum(0)
            self.progressBar.setValue(0)
            self.setWindowTitle(self.__windowTitleTemplate.format(""))
        else:
            self.progressBar.setMaximum(total)
            self.progressBar.setValue(received)
            pc = "{0}%".format(received * 100 // total)
            self.setWindowTitle(self.__windowTitleTemplate.format(pc))
        self.__updateInfoLabel()
    
    def __updateInfoLabel(self):
        """
        Private method to update the info label.
        """
        if self.__reply.error() != QNetworkReply.NoError and \
           self.__reply.error() != QNetworkReply.OperationCanceledError:
            return
        
        bytesTotal = self.progressBar.maximum()
        
        info = ""
        if self.__downloading():
            remaining = ""
            speed = self.__bytesReceived * 1000.0 / self.__downloadTime.elapsed()
            if bytesTotal != 0:
                timeRemaining = int((bytesTotal - self.__bytesReceived) / speed)
                
                if timeRemaining > 60:
                    minutes = int(timeRemaining / 60)
                    seconds = int(timeRemaining % 60)
                    remaining = self.trUtf8("- {0}:{1:02} minutes remaining")\
                            .format(minutes, seconds)
                else:
                    # when downloading, the eta should never be 0
                    if timeRemaining == 0:
                        timeRemaining = 1
                    
                    remaining = self.trUtf8("- {0} seconds remaining")\
                            .format(timeRemaining)
            info = self.trUtf8("{0} of {1} ({2}/sec) {3}")\
                .format(
                    self.__dataString(self.__bytesReceived), 
                    bytesTotal == 0 and self.trUtf8("?") \
                                     or self.__dataString(bytesTotal), 
                    self.__dataString(int(speed)), 
                    remaining)
        else:
            if self.__bytesReceived == bytesTotal:
                info = self.trUtf8("{0} downloaded")\
                    .format(self.__dataString(self.__output.size()))
            else:
                info = self.trUtf8("{0} of {1} - Stopped")\
                    .format(self.__dataString(self.__bytesReceived), 
                            self.__dataString(bytesTotal))
        self.infoLabel.setText(info)
    
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
    
    def __downloading(self):
        """
        Private method to determine, if a download is in progress.
        
        @return flag indicating a download is in progress (boolean)
        """
        return self.__stopButton.isEnabled()
    
    def __finished(self):
        """
        Private slot to handle the download finished.
        """
        self.__downloadFinished = True
        if not self.__startedSaving:
            return
        
        self.__stopButton.setEnabled(False)
        self.__closeButton.setEnabled(True)
        self.__openButton.setEnabled(True)
        self.__output.close()
        self.__updateInfoLabel()
        
        if not self.keepOpenCheckBox.isChecked() and \
           self.__reply.error() == QNetworkReply.NoError:
            self.close()
        
        if self.__autoOpen:
            self.__open()
    
    def closeEvent(self, evt):
        """
        Protected method called when the dialog is closed.
        """
        self.__output.close()
        
        self.disconnect(self.__reply, SIGNAL("readyRead()"), self.__readyRead)
        self.disconnect(self.__reply, SIGNAL("error(QNetworkReply::NetworkError)"), 
                        self.__networkError)
        self.disconnect(self.__reply, SIGNAL("downloadProgress(qint64, qint64)"), 
                        self.__downloadProgress)
        self.disconnect(self.__reply, SIGNAL("metaDataChanged()"), 
                        self.__metaDataChanged)
        self.disconnect(self.__reply, SIGNAL("finished()"), self.__finished)
        self.__reply.close()
        self.__reply.deleteLater()
        
        self.done.emit()
