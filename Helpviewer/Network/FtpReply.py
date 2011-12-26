# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a network reply class for FTP resources.
"""

from PyQt4.QtCore import QByteArray, QIODevice, Qt, QUrl, QTimer, QBuffer
from PyQt4.QtGui import QPixmap
from PyQt4.QtNetwork import QFtp, QNetworkReply, QNetworkRequest, QUrlInfo, \
    QNetworkProxyQuery, QNetworkProxy, QAuthenticator
from PyQt4.QtWebKit import QWebSettings

import UI.PixmapCache

ftpListPage_html = """\
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<title>{0}</title>
<style type="text/css">
body {{
  padding: 3em 0em;
  background: -webkit-gradient(linear, left top, left bottom, from(#85784A), to(#FDFDFD), color-stop(0.5, #FDFDFD));
  background-repeat: repeat-x;
}}
#box {{
  background: white;
  border: 1px solid #85784A;
  width: 80%;
  padding: 30px;
  margin: auto;
  -webkit-border-radius: 0.8em;
}}
h1 {{
  font-size: 130%;
  font-weight: bold;
  border-bottom: 1px solid #85784A;
}}
th {{
  background-color: #B8B096;
  color: black;
}}
table {{
  border: solid 1px #85784A;
  margin: 5px 0;
  width: 100%;
}}
tr.odd {{
  background-color: white;
  color: black;
}}
tr.even {{
  background-color: #CEC9B8;
  color: black;
}}
.modified {{
  text-align: left;
  vertical-align: top;
  white-space: nowrap;
}}
.size {{
  text-align: right;
  vertical-align: top;
  white-space: nowrap;
  padding-right: 22px;
}}
.name {{
  text-align: left;
  vertical-align: top;
  white-space: pre-wrap;
  width: 100%
}}
{1}
</style>
</head>
<body>
  <div id="box">
  <h1>{2}</h1>
{3}
  <table align="center" cellspacing="0" width="90%">
{4}
  </table>
  </div>
</body>
</html>
"""


class FtpReply(QNetworkReply):
    """
    Class implementing a network reply for FTP resources.
    """
    def __init__(self, url, parent=None):
        """
        Constructor
        
        @param url requested FTP URL (QUrl)
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__manager = parent
        
        self.__ftp = QFtp(self)
        self.__ftp.listInfo.connect(self.__processListInfo)
        self.__ftp.readyRead.connect(self.__processData)
        self.__ftp.commandFinished.connect(self.__processCommand)
        self.__ftp.commandStarted.connect(self.__commandStarted)
        self.__ftp.dataTransferProgress.connect(self.downloadProgress)
        
        self.__items = []
        self.__content = QByteArray()
        self.__units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
        
        if url.path() == "":
            url.setPath("/")
        self.setUrl(url)
        # do proxy setup
        query = QNetworkProxyQuery(url)
        proxyList = parent.proxyFactory().queryProxy(query)
        ftpProxy = QNetworkProxy()
        for proxy in proxyList:
            if proxy.type() == QNetworkProxy.NoProxy or \
               proxy.type() == QNetworkProxy.FtpCachingProxy:
                ftpProxy = proxy
                break
        if ftpProxy.type() == QNetworkProxy.DefaultProxy:
            self.setError(QNetworkReply.ProxyNotFoundError,
                          self.trUtf8("No suitable proxy found."))
            QTimer.singleShot(0, self.__errorSignals)
            return
        elif ftpProxy.type() == QNetworkProxy.FtpCachingProxy:
            self.__ftp.setProxy(ftpProxy.hostName(), ftpProxy.port())
        
        self.__loggingIn = False
        
        QTimer.singleShot(0, self.__connectToHost)
    
    def __errorSignals(self):
        """
        Private slot to send signal for errors during initialisation.
        """
        self.error.emit(QNetworkReply.ProxyNotFoundError)
        self.finished.emit()
    
    def abort(self):
        """
        Public slot to abort the operation.
        """
        # do nothing
        pass
    
    def bytesAvailable(self):
        """
        Public method to determined the bytes available for being read.
        
        @return bytes available (integer)
        """
        return self.__content.size()
    
    def isSequential(self):
        """
        Public method to check for sequential access.
        
        @return flag indicating sequential access (boolean)
        """
        return True
    
    def readData(self, maxlen):
        """
        Protected method to retrieve data from the reply object.
        
        @param maxlen maximum number of bytes to read (integer)
        @return string containing the data (bytes)
        """
        if self.__content.size():
            len_ = min(maxlen, self.__content.size())
            buffer = bytes(self.__content[:len_])
            self.__content.remove(0, len_)
            return buffer
    
    def __connectToHost(self):
        """
        Private slot to start the FTP process by connecting to the host.
        """
        self.__ftp.connectToHost(self.url().host())
    
    def __commandStarted(self, id):
        """
        Private slot to handle the start of FTP commands.
        
        @param id id of the command to be processed (integer) (ignored)
        """
        cmd = self.__ftp.currentCommand()
        if cmd == QFtp.Get:
            self.__setContent()
    
    def __processCommand(self, id, error):
        """
        Private slot to handle the end of FTP commands.
        
        @param id id of the command to be processed (integer) (ignored)
        @param error flag indicating an error condition (boolean)
        """
        if error:
            if self.__ftp.error() == QFtp.HostNotFound:
                err = QNetworkReply.HostNotFoundError
            elif self.__ftp.error() == QFtp.ConnectionRefused:
                err = QNetworkReply.ConnectionRefusedError
            else:
                if self.__loggingIn and \
                   self.__ftp.state() == QFtp.Connected:
                    # authentication is required
                    if "anonymous" in self.__ftp.errorString():
                        self.__ftp.login()
                        return
                    
                    newUrl = self.url()
                    auth = QAuthenticator()
                    self.__manager.authenticationRequired.emit(self, auth)
                    if not auth.isNull():
                        if auth.user():
                            newUrl.setUserName(auth.user())
                            newUrl.setPassword(auth.password())
                            self.setUrl(newUrl)
                        else:
                            auth.setUser("anonymous")
                            auth.setPassword("anonymous")
                        if self.__ftp.state() == QFtp.Connected:
                            self.__ftp.login(auth.user(), auth.password())
                            return
                
                err = QNetworkReply.ProtocolFailure
            self.setError(err, self.__ftp.errorString())
            self.error.emit(err)
            self.finished.emit()
            if self.__ftp.state() not in [QFtp.Unconnected, QFtp.Closing]:
                self.__ftp.close()
            return
        
        cmd = self.__ftp.currentCommand()
        if cmd == QFtp.ConnectToHost:
            self.__loggingIn = True
            self.__ftp.login(self.url().userName(), self.url().password())
        elif cmd == QFtp.Login:
            self.__loggingIn = False
            self.__ftp.list(self.url().path())
        elif cmd == QFtp.List:
            if len(self.__items) == 1 and \
               self.__items[0].isFile():
                self.__ftp.get(self.url().path())
            else:
                self.__setListContent()
        elif cmd == QFtp.Get:
            self.finished.emit()
            self.__ftp.close()
    
    def __processListInfo(self, urlInfo):
        """
        Private slot to process list information from the FTP server.
        
        @param urlInfo reference to the information object (QUrlInfo)
        """
        self.__items.append(QUrlInfo(urlInfo))
    
    def __processData(self):
        """
        Private slot to process data from the FTP server.
        """
        self.__content += self.__ftp.readAll()
        self.readyRead.emit()
    
    def __setContent(self):
        """
        Private method to set the finish the setup of the data.
        """
        self.open(QIODevice.ReadOnly | QIODevice.Unbuffered)
        self.setHeader(QNetworkRequest.ContentLengthHeader, self.__items[0].size())
        self.setAttribute(QNetworkRequest.HttpStatusCodeAttribute, 200)
        self.setAttribute(QNetworkRequest.HttpReasonPhraseAttribute, "Ok")
        self.metaDataChanged.emit()
    
    def __cssLinkClass(self, icon, size=32):
        """
        Private method to generate a link class with an icon.
        
        @param icon icon to be included (QIcon)
        @param size size of the icon to be generated (integer)
        @return CSS class string (string)
        """
        cssString = \
            """a.{{0}} {{{{\n"""\
            """  padding-left: {0}px;\n"""\
            """  background: transparent url(data:image/png;base64,{1}) no-repeat center left;\n"""\
            """  font-weight: bold;\n"""\
            """}}}}\n"""
        pixmap = icon.pixmap(size, size)
        imageBuffer = QBuffer()
        imageBuffer.open(QIODevice.ReadWrite)
        if not pixmap.save(imageBuffer, "PNG"):
            # write a blank pixmap on error
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
            imageBuffer.buffer().clear()
            pixmap.save(imageBuffer, "PNG")
        return cssString.format(size + 4,
            str(imageBuffer.buffer().toBase64(), encoding="ascii"))
    
    def __setListContent(self):
        """
        Private method to prepare the content for the reader.
        """
        u = self.url()
        if not u.path().endswith("/"):
            u.setPath(u.path() + "/")
        
        baseUrl = self.url().toString()
        basePath = u.path()
        
        linkClasses = {}
        iconSize = QWebSettings.globalSettings().fontSize(QWebSettings.DefaultFontSize)
        
        parent = u.resolved(QUrl(".."))
        if parent.isParentOf(u):
            icon = UI.PixmapCache.getIcon("up.png")
            linkClasses["link_parent"] = \
                self.__cssLinkClass(icon, iconSize).format("link_parent")
            parentStr = self.trUtf8(
                """  <p><a class="link_parent" href="{0}">"""
                """Change to parent directory</a></p>"""
            ).format(parent.toString())
        else:
            parentStr = ""
        
        row = \
            """    <tr class="{0}">"""\
            """<td class="name"><a class="{1}" href="{2}">{3}</a></td>"""\
            """<td class="size">{4}</td>"""\
            """<td class="modified">{5}</td>"""\
            """</tr>\n"""
        table = self.trUtf8(
            """    <tr>"""
            """<th align="left">Name</th>"""
            """<th>Size</th>"""
            """<th align="left">Last modified</th>"""
            """</tr>\n"""
        )
        
        i = 0
        for item in self.__items:
            name = item.name()
            if item.isDir() and not name.endswith("/"):
                name += "/"
            child = u.resolved(QUrl(name.replace(":", "%3A")))
            
            if item.isFile():
                size = item.size()
                unit = 0
                while size:
                    newSize = size // 1024
                    if newSize and unit < len(self.__units):
                        size = newSize
                        unit += 1
                    else:
                        break
                
                sizeStr = self.trUtf8("{0} {1}", "size unit")\
                    .format(size, self.__units[unit])
                linkClass = "link_file"
                if linkClass not in linkClasses:
                    icon = UI.PixmapCache.getIcon("fileMisc.png")
                    linkClasses[linkClass] = \
                        self.__cssLinkClass(icon, iconSize).format(linkClass)
            else:
                sizeStr = ""
                linkClass = "link_dir"
                if linkClass not in linkClasses:
                    icon = UI.PixmapCache.getIcon("dirClosed.png")
                    linkClasses[linkClass] = \
                        self.__cssLinkClass(icon, iconSize).format(linkClass)
            table += row.format(
                i == 0 and "odd" or "even",
                linkClass,
                child.toString(),
                Qt.escape(item.name()),
                sizeStr,
                item.lastModified().toString("yyyy-MM-dd hh:mm"),
            )
            i = 1 - i
        
        content = ftpListPage_html.format(
            Qt.escape(baseUrl),
            "".join(linkClasses.values()),
            self.trUtf8("Listing of {0}").format(basePath),
            parentStr,
            table
        )
        self.__content = QByteArray(content.encode("utf8"))
        
        self.open(QIODevice.ReadOnly | QIODevice.Unbuffered)
        self.setHeader(QNetworkRequest.ContentTypeHeader, "text/html; charset=UTF-8")
        self.setHeader(QNetworkRequest.ContentLengthHeader, self.__content.size())
        self.setAttribute(QNetworkRequest.HttpStatusCodeAttribute, 200)
        self.setAttribute(QNetworkRequest.HttpReasonPhraseAttribute, "Ok")
        self.metaDataChanged.emit()
        self.downloadProgress.emit(self.__content.size(), self.__content.size())
        self.readyRead.emit()
        self.finished.emit()
        self.__ftp.close()
