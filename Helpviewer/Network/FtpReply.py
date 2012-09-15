# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a network reply class for FTP resources.
"""

import ftplib
import socket
import errno

from PyQt4.QtCore import QByteArray, QIODevice, Qt, QUrl, QTimer, QBuffer, QDate, QTime, \
    QDateTime, QCoreApplication
from PyQt4.QtGui import QPixmap
from PyQt4.QtNetwork import QNetworkReply, QNetworkRequest, QUrlInfo
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
    Monthnames2Int = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }
    
    def __init__(self, url, parent=None):
        """
        Constructor
        
        @param url requested FTP URL (QUrl)
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__manager = parent
        
        self.__ftp = ftplib.FTP()
        
        self.__items = []
        self.__content = QByteArray()
        self.__units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
        
        if url.path() == "":
            url.setPath("/")
        self.setUrl(url)
        
        self.__loggingIn = False
        
        QTimer.singleShot(0, self.__doFtpCommands)
    
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
    
    def __doFtpCommands(self):
        """
        Private slot doing the sequence of FTP commands to get the requested result.
        """
        try:
            self.__ftp.connect(self.url().host(), timeout=10)
            self.__ftp.login(self.url().userName(), self.url().password())
            self.__ftp.retrlines("LIST " + self.url().path(), self.__dirCallback)
            if len(self.__items) == 1 and \
               self.__items[0].isFile():
                self.__setContent()
                self.__ftp.retrbinary("RETR " + self.url().path(), self.__retrCallback)
                self.__content.append(512 * b' ')
                self.readyRead.emit()
            else:
                self.__setListContent()
            self.__ftp.quit()
        except ftplib.all_errors as err:
            if isinstance(err, socket.gaierror):
                errCode = QNetworkReply.HostNotFoundError
            elif isinstance(err, socket.error) and err.errno == errno.ECONNREFUSED:
                errCode = QNetworkReply.ConnectionRefusedError
            else:
                errCode = QNetworkReply.ProtocolFailure
            self.setError(errCode, str(err))
            self.error.emit(errCode)
        self.finished.emit()
    
    def __dirCallback(self, line):
        """
        Private slot handling the receipt of directory listings.
        
        @param line the received line of the directory listing (string)
        """
        words = line.split(None, 8)
        if len(words) < 6:
            # skip short lines
            return
        filename = words[-1].lstrip()
        i = filename.find(" -> ")
        if i >= 0:
            filename = filename[:i]
        infostuff = words[-5:-1]
        mode = words[0].strip()
        
        info = QUrlInfo()
        # 1. type of item
        if mode[0] == "d":
            info.setDir(True)
            info.setFile(False)
        elif mode[0] == "l":
            info.setSymLink(True)
        elif mode[0] == "-":
            info.setDir(False)
            info.setFile(True)
        # 2. name
        info.setName(filename.strip())
        # 3. size
        if mode[0] == "-":
            info.setSize(int(infostuff[0]))
        # 4. last modified
        if infostuff[1] in self.Monthnames2Int:
            month = self.Monthnames2Int[infostuff[1]]
        else:
            month = 1
        if ":" in infostuff[3]:
            # year is current year
            year = QDate.currentDate().year()
            timeStr = infostuff[3]
        else:
            year = int(infostuff[3])
            timeStr = "00:00"
        date = QDate(year, month, int(infostuff[2]))
        time = QTime.fromString(timeStr, "hh:mm")
        lastModified = QDateTime(date, time)
        info.setLastModified(lastModified)
        
        self.__items.append(info)
        
        QCoreApplication.processEvents()
    
    def __retrCallback(self, data):
        """
        Private slot handling the reception of data.
        
        @param data data received from the FTP server (bytes)
        """
        self.__content += QByteArray(data)
        
        QCoreApplication.processEvents()
    
    def __setContent(self):
        """
        Private method to finish the setup of the data.
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
        self.__content.append(512 * b' ')
        
        self.open(QIODevice.ReadOnly | QIODevice.Unbuffered)
        self.setHeader(QNetworkRequest.ContentTypeHeader, "text/html; charset=UTF-8")
        self.setHeader(QNetworkRequest.ContentLengthHeader, self.__content.size())
        self.setAttribute(QNetworkRequest.HttpStatusCodeAttribute, 200)
        self.setAttribute(QNetworkRequest.HttpReasonPhraseAttribute, "Ok")
        self.metaDataChanged.emit()
        self.downloadProgress.emit(self.__content.size(), self.__content.size())
        self.readyRead.emit()
