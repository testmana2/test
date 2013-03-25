# -*- coding: utf-8 -*-

# Copyright (c) 2007 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#


"""
Module implementing a dialog showing the available plugins.
"""

from __future__ import unicode_literals    # __IGNORE_WARNING__

import sys
import os
import zipfile

from PyQt4.QtCore import pyqtSignal, pyqtSlot, Qt, QFile, QIODevice, QUrl, QProcess
from PyQt4.QtGui import QWidget, QDialogButtonBox, QAbstractButton, QTreeWidgetItem, \
    QDialog, QVBoxLayout
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from .Ui_PluginRepositoryDialog import Ui_PluginRepositoryDialog

from E5Gui import E5MessageBox
from E5Gui.E5MainWindow import E5MainWindow
from E5Gui.E5Application import e5App

from E5Network.E5NetworkProxyFactory import proxyAuthenticationRequired
try:
    from E5Network.E5SslErrorHandler import E5SslErrorHandler
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False

import Utilities
import Preferences

import UI.PixmapCache

from eric5config import getConfig

descrRole = Qt.UserRole
urlRole = Qt.UserRole + 1
filenameRole = Qt.UserRole + 2
authorRole = Qt.UserRole + 3


class PluginRepositoryWidget(QWidget, Ui_PluginRepositoryDialog):
    """
    Class implementing a dialog showing the available plugins.
    
    @signal closeAndInstall() emitted when the Close & Install button is pressed
    """
    closeAndInstall = pyqtSignal()
    
    def __init__(self, parent=None, external=False):
        """
        Constructor
        
        @param parent parent of this dialog (QWidget)
        """
        super(PluginRepositoryWidget, self).__init__(parent)
        self.setupUi(self)
        
        self.__updateButton = \
            self.buttonBox.addButton(self.trUtf8("Update"), QDialogButtonBox.ActionRole)
        self.__downloadButton = \
            self.buttonBox.addButton(self.trUtf8("Download"), QDialogButtonBox.ActionRole)
        self.__downloadButton.setEnabled(False)
        self.__downloadInstallButton = \
            self.buttonBox.addButton(self.trUtf8("Download && Install"),
            QDialogButtonBox.ActionRole)
        self.__downloadInstallButton.setEnabled(False)
        self.__downloadCancelButton = \
            self.buttonBox.addButton(self.trUtf8("Cancel"), QDialogButtonBox.ActionRole)
        self.__installButton = \
            self.buttonBox.addButton(self.trUtf8("Close && Install"),
                                     QDialogButtonBox.ActionRole)
        self.__downloadCancelButton.setEnabled(False)
        self.__installButton.setEnabled(False)
        
        self.repositoryUrlEdit.setText(Preferences.getUI("PluginRepositoryUrl5"))
        
        self.repositoryList.headerItem().setText(self.repositoryList.columnCount(), "")
        self.repositoryList.header().setSortIndicator(0, Qt.AscendingOrder)
        
        self.pluginRepositoryFile = \
            os.path.join(Utilities.getConfigDir(), "PluginRepository")
        
        self.__external = external
        
        # attributes for the network objects
        self.__networkManager = QNetworkAccessManager(self)
        self.__networkManager.proxyAuthenticationRequired.connect(
            proxyAuthenticationRequired)
        if SSL_AVAILABLE:
            self.__sslErrorHandler = E5SslErrorHandler(self)
            self.__networkManager.sslErrors.connect(self.__sslErrors)
        self.__replies = []
        
        self.__doneMethod = None
        self.__inDownload = False
        self.__pluginsToDownload = []
        self.__pluginsDownloaded = []
        self.__isDownloadInstall = False
        self.__allDownloadedOk = False
        
        self.__populateList()
    
    @pyqtSlot(QAbstractButton)
    def on_buttonBox_clicked(self, button):
        """
        Private slot to handle the click of a button of the button box.
        """
        if button == self.__updateButton:
            self.__updateList()
        elif button == self.__downloadButton:
            self.__isDownloadInstall = False
            self.__downloadPlugins()
        elif button == self.__downloadInstallButton:
            self.__isDownloadInstall = True
            self.__allDownloadedOk = True
            self.__downloadPlugins()
        elif button == self.__downloadCancelButton:
            self.__downloadCancel()
        elif button == self.__installButton:
            self.closeAndInstall.emit()
    
    def __formatDescription(self, lines):
        """
        Private method to format the description.
        
        @param lines lines of the description (list of strings)
        @return formatted description (string)
        """
        # remove empty line at start and end
        newlines = lines[:]
        if len(newlines) and newlines[0] == '':
            del newlines[0]
        if len(newlines) and newlines[-1] == '':
            del newlines[-1]
        
        # replace empty lines by newline character
        index = 0
        while index < len(newlines):
            if newlines[index] == '':
                newlines[index] = '\n'
            index += 1
        
        # join lines by a blank
        return ' '.join(newlines)
    
    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def on_repositoryList_currentItemChanged(self, current, previous):
        """
        Private slot to handle the change of the current item.
        
        @param current reference to the new current item (QTreeWidgetItem)
        @param previous reference to the old current item (QTreeWidgetItem)
        """
        if self.__repositoryMissing or current is None:
            return
        
        self.urlEdit.setText(current.data(0, urlRole) or "")
        self.descriptionEdit.setPlainText(current.data(0, descrRole) and \
            self.__formatDescription(current.data(0, descrRole)) or "")
        self.authorEdit.setText(current.data(0, authorRole) or "")
    
    def __selectedItems(self):
        """
        Private method to get all selected items without the toplevel ones.
        
        @return list of selected items (list)
        """
        ql = self.repositoryList.selectedItems()
        for index in range(self.repositoryList.topLevelItemCount()):
            ti = self.repositoryList.topLevelItem(index)
            if ti in ql:
                ql.remove(ti)
        return ql
    
    @pyqtSlot()
    def on_repositoryList_itemSelectionChanged(self):
        """
        Private slot to handle a change of the selection.
        """
        self.__downloadButton.setEnabled(len(self.__selectedItems()))
        self.__downloadInstallButton.setEnabled(len(self.__selectedItems()))
    
    def __updateList(self):
        """
        Private slot to download a new list and display the contents.
        """
        url = self.repositoryUrlEdit.text()
        self.__downloadFile(url,
                            self.pluginRepositoryFile,
                            self.__downloadRepositoryFileDone)
    
    def __downloadRepositoryFileDone(self, status, filename):
        """
        Private method called after the repository file was downloaded.
        
        @param status flaging indicating a successful download (boolean)
        @param filename full path of the downloaded file (string)
        """
        self.__populateList()
    
    def __downloadPluginDone(self, status, filename):
        """
        Private method called, when the download of a plugin is finished.
        
        @param status flag indicating a successful download (boolean)
        @param filename full path of the downloaded file (string)
        """
        if status:
            self.__pluginsDownloaded.append(filename)
        if self.__isDownloadInstall:
            self.__allDownloadedOk &= status
        
        del self.__pluginsToDownload[0]
        if len(self.__pluginsToDownload):
            self.__downloadPlugin()
        else:
            self.__downloadPluginsDone()
    
    def __downloadPlugin(self):
        """
        Private method to download the next plugin.
        """
        self.__downloadFile(self.__pluginsToDownload[0][0],
                            self.__pluginsToDownload[0][1],
                            self.__downloadPluginDone)
    
    def __downloadPlugins(self):
        """
        Private slot to download the selected plugins.
        """
        self.__pluginsDownloaded = []
        self.__pluginsToDownload = []
        self.__downloadButton.setEnabled(False)
        self.__downloadInstallButton.setEnabled(False)
        self.__installButton.setEnabled(False)
        for itm in self.repositoryList.selectedItems():
            if itm not in [self.__stableItem, self.__unstableItem, self.__unknownItem]:
                url = itm.data(0, urlRole)
                filename = os.path.join(
                    Preferences.getPluginManager("DownloadPath"),
                    itm.data(0, filenameRole))
                self.__pluginsToDownload.append((url, filename))
        self.__downloadPlugin()
    
    def __downloadPluginsDone(self):
        """
        Private method called, when the download of the plugins is finished.
        """
        self.__downloadButton.setEnabled(len(self.__selectedItems()))
        self.__downloadInstallButton.setEnabled(len(self.__selectedItems()))
        self.__installButton.setEnabled(True)
        self.__doneMethod = None
        if not self.__external:
            ui = e5App().getObject("UserInterface")
        else:
            ui = None
        if ui and ui.notificationsEnabled():
            ui.showNotification(UI.PixmapCache.getPixmap("plugin48.png"),
                self.trUtf8("Download Plugin Files"),
                self.trUtf8("""The requested plugins were downloaded."""))
        
        if self.__isDownloadInstall:
            self.closeAndInstall.emit()
        else:
            if ui is None or not ui.notificationsEnabled():
                E5MessageBox.information(self,
                    self.trUtf8("Download Plugin Files"),
                    self.trUtf8("""The requested plugins were downloaded."""))
            self.downloadProgress.setValue(0)
            
            # repopulate the list to update the refresh icons
            self.__populateList()
    
    def __resortRepositoryList(self):
        """
        Private method to resort the tree.
        """
        self.repositoryList.sortItems(self.repositoryList.sortColumn(),
                                      self.repositoryList.header().sortIndicatorOrder())
    
    def __populateList(self):
        """
        Private method to populate the list of available plugins.
        """
        self.repositoryList.clear()
        self.__stableItem = None
        self.__unstableItem = None
        self.__unknownItem = None
        
        self.downloadProgress.setValue(0)
        self.__doneMethod = None
        
        if os.path.exists(self.pluginRepositoryFile):
            self.__repositoryMissing = False
            f = QFile(self.pluginRepositoryFile)
            if f.open(QIODevice.ReadOnly):
                from E5XML.PluginRepositoryReader import PluginRepositoryReader
                reader = PluginRepositoryReader(f, self)
                reader.readXML()
                self.repositoryList.resizeColumnToContents(0)
                self.repositoryList.resizeColumnToContents(1)
                self.repositoryList.resizeColumnToContents(2)
                self.__resortRepositoryList()
                url = Preferences.getUI("PluginRepositoryUrl5")
                if url != self.repositoryUrlEdit.text():
                    self.repositoryUrlEdit.setText(url)
                    E5MessageBox.warning(self,
                        self.trUtf8("Plugins Repository URL Changed"),
                        self.trUtf8("""The URL of the Plugins Repository has"""
                                    """ changed. Select the "Update" button to get"""
                                    """ the new repository file."""))
            else:
                E5MessageBox.critical(self,
                    self.trUtf8("Read plugins repository file"),
                    self.trUtf8("<p>The plugins repository file <b>{0}</b> "
                                "could not be read. Select Update</p>")\
                        .format(self.pluginRepositoryFile))
        else:
            self.__repositoryMissing = True
            QTreeWidgetItem(self.repositoryList,
                ["",
                 self.trUtf8("No plugin repository file available.\nSelect Update.")
                ])
            self.repositoryList.resizeColumnToContents(1)
    
    def __downloadFile(self, url, filename, doneMethod=None):
        """
        Private slot to download the given file.
        
        @param url URL for the download (string)
        @param filename local name of the file (string)
        @param doneMethod method to be called when done
        """
        self.__updateButton.setEnabled(False)
        self.__downloadButton.setEnabled(False)
        self.__downloadInstallButton.setEnabled(False)
        self.__downloadCancelButton.setEnabled(True)
        
        self.statusLabel.setText(url)
        
        self.__doneMethod = doneMethod
        self.__downloadURL = url
        self.__downloadFileName = filename
        self.__downloadIODevice = QFile(self.__downloadFileName + ".tmp")
        self.__downloadCancelled = False
        
        request = QNetworkRequest(QUrl(url))
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute,
                             QNetworkRequest.AlwaysNetwork)
        reply = self.__networkManager.get(request)
        reply.finished[()].connect(self.__downloadFileDone)
        reply.downloadProgress.connect(self.__downloadProgress)
        self.__replies.append(reply)
    
    def __downloadFileDone(self):
        """
        Private method called, after the file has been downloaded
        from the internet.
        """
        self.__updateButton.setEnabled(True)
        self.__downloadCancelButton.setEnabled(False)
        self.statusLabel.setText("  ")
        
        ok = True
        reply = self.sender()
        if reply in self.__replies:
            self.__replies.remove(reply)
        if reply.error() != QNetworkReply.NoError:
            ok = False
            if not self.__downloadCancelled:
                E5MessageBox.warning(self,
                    self.trUtf8("Error downloading file"),
                    self.trUtf8(
                        """<p>Could not download the requested file from {0}.</p>"""
                        """<p>Error: {1}</p>"""
                    ).format(self.__downloadURL, reply.errorString())
                )
            self.downloadProgress.setValue(0)
            self.__downloadURL = None
            self.__downloadIODevice.remove()
            self.__downloadIODevice = None
            if self.repositoryList.topLevelItemCount():
                if self.repositoryList.currentItem() is None:
                    self.repositoryList.setCurrentItem(
                        self.repositoryList.topLevelItem(0))
                else:
                    self.__downloadButton.setEnabled(len(self.__selectedItems()))
                    self.__downloadInstallButton.setEnabled(len(self.__selectedItems()))
            return
        
        self.__downloadIODevice.open(QIODevice.WriteOnly)
        self.__downloadIODevice.write(reply.readAll())
        self.__downloadIODevice.close()
        if QFile.exists(self.__downloadFileName):
            QFile.remove(self.__downloadFileName)
        self.__downloadIODevice.rename(self.__downloadFileName)
        self.__downloadIODevice = None
        self.__downloadURL = None
        
        if self.__doneMethod is not None:
            self.__doneMethod(ok, self.__downloadFileName)
    
    def __downloadCancel(self):
        """
        Private slot to cancel the current download.
        """
        if self.__replies:
            reply = self.__replies[0]
            self.__downloadCancelled = True
            self.__pluginsToDownload = []
            reply.abort()
    
    def __downloadProgress(self, done, total):
        """
        Private slot to show the download progress.
        
        @param done number of bytes downloaded so far (integer)
        @param total total bytes to be downloaded (integer)
        """
        if total:
            self.downloadProgress.setMaximum(total)
            self.downloadProgress.setValue(done)
    
    def addEntry(self, name, short, description, url, author, version, filename, status):
        """
        Public method to add an entry to the list.
        
        @param name data for the name field (string)
        @param short data for the short field (string)
        @param description data for the description field (list of strings)
        @param url data for the url field (string)
        @param author data for the author field (string)
        @param version data for the version field (string)
        @param filename data for the filename field (string)
        @param status status of the plugin (string [stable, unstable, unknown])
        """
        if status == "stable":
            if self.__stableItem is None:
                self.__stableItem = \
                    QTreeWidgetItem(self.repositoryList, [self.trUtf8("Stable")])
                self.__stableItem.setExpanded(True)
            parent = self.__stableItem
        elif status == "unstable":
            if self.__unstableItem is None:
                self.__unstableItem = \
                    QTreeWidgetItem(self.repositoryList, [self.trUtf8("Unstable")])
                self.__unstableItem.setExpanded(True)
            parent = self.__unstableItem
        else:
            if self.__unknownItem is None:
                self.__unknownItem = \
                    QTreeWidgetItem(self.repositoryList, [self.trUtf8("Unknown")])
                self.__unknownItem.setExpanded(True)
            parent = self.__unknownItem
        itm = QTreeWidgetItem(parent, [name, version, short])
        
        itm.setData(0, urlRole, url)
        itm.setData(0, filenameRole, filename)
        itm.setData(0, authorRole, author)
        itm.setData(0, descrRole, description)
        
        if self.__isUpToDate(filename, version):
            itm.setIcon(1, UI.PixmapCache.getIcon("empty.png"))
        else:
            itm.setIcon(1, UI.PixmapCache.getIcon("download.png"))
    
    def __isUpToDate(self, filename, version):
        """
        Private method to check, if the given archive is up-to-date.
        
        @param filename data for the filename field (string)
        @param version data for the version field (string)
        @return flag indicating up-to-date (boolean)
        """
        archive = os.path.join(Preferences.getPluginManager("DownloadPath"),
                               filename)

        # check, if the archive exists
        if not os.path.exists(archive):
            return False
        
        # check, if the archive is a valid zip file
        if not zipfile.is_zipfile(archive):
            return False
        
        zip = zipfile.ZipFile(archive, "r")
        try:
            aversion = zip.read("VERSION").decode("utf-8")
        except KeyError:
            aversion = ""
        zip.close()
        
        return aversion == version
    
    def __sslErrors(self, reply, errors):
        """
        Private slot to handle SSL errors.
        
        @param reply reference to the reply object (QNetworkReply)
        @param errors list of SSL errors (list of QSslError)
        """
        ignored = self.__sslErrorHandler.sslErrorsReply(reply, errors)[0]
        if ignored == E5SslErrorHandler.NotIgnored:
            self.__downloadCancelled = True
    
    def getDownloadedPlugins(self):
        """
        Public method to get the list of recently downloaded plugin files.
        
        @return list of plugin filenames (list of strings)
        """
        return self.__pluginsDownloaded
    
    @pyqtSlot(bool)
    def on_repositoryUrlEditButton_toggled(self, checked):
        """
        Private slot to set the read only status of the repository URL line edit.
        
        @param checked state of the push button (boolean)
        """
        self.repositoryUrlEdit.setReadOnly(not checked)


class PluginRepositoryDialog(QDialog):
    """
    Class for the dialog variant.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(PluginRepositoryDialog, self).__init__(parent)
        self.setSizeGripEnabled(True)
        
        self.__layout = QVBoxLayout(self)
        self.__layout.setMargin(0)
        self.setLayout(self.__layout)
        
        self.cw = PluginRepositoryWidget(self)
        size = self.cw.size()
        self.__layout.addWidget(self.cw)
        self.resize(size)
        
        self.cw.buttonBox.accepted[()].connect(self.accept)
        self.cw.buttonBox.rejected[()].connect(self.reject)
        self.cw.closeAndInstall.connect(self.__closeAndInstall)
        
    def __closeAndInstall(self):
        """
        Private slot to handle the closeAndInstall signal.
        """
        self.done(QDialog.Accepted + 1)
    
    def getDownloadedPlugins(self):
        """
        Public method to get the list of recently downloaded plugin files.
        
        @return list of plugin filenames (list of strings)
        """
        return self.cw.getDownloadedPlugins()


class PluginRepositoryWindow(E5MainWindow):
    """
    Main window class for the standalone dialog.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(PluginRepositoryWindow, self).__init__(parent)
        self.cw = PluginRepositoryWidget(self, external=True)
        size = self.cw.size()
        self.setCentralWidget(self.cw)
        self.resize(size)
        
        self.setStyle(Preferences.getUI("Style"), Preferences.getUI("StyleSheet"))
        
        self.cw.buttonBox.accepted[()].connect(self.close)
        self.cw.buttonBox.rejected[()].connect(self.close)
        self.cw.closeAndInstall.connect(self.__startPluginInstall)
    
    def __startPluginInstall(self):
        """
        Private slot to start the eric5 plugin installation dialog.
        """
        proc = QProcess()
        applPath = os.path.join(getConfig("ericDir"), "eric5_plugininstall.py")
        
        args = []
        args.append(applPath)
        args += self.cw.getDownloadedPlugins()
        
        if not os.path.isfile(applPath) or not proc.startDetached(sys.executable, args):
            E5MessageBox.critical(self,
                self.trUtf8('Process Generation Error'),
                self.trUtf8(
                    '<p>Could not start the process.<br>'
                    'Ensure that it is available as <b>{0}</b>.</p>'
                ).format(applPath),
                self.trUtf8('OK'))
        
        self.close()
