# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the <a href="http://www.virustotal.com">VirusTotal</a>
API class.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

import json

from PyQt5.QtCore import QObject, QUrl, QByteArray, pyqtSignal
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply, \
    QNetworkAccessManager

import Preferences


class VirusTotalAPI(QObject):
    """
    Class implementing the <a href="http://www.virustotal.com">VirusTotal</a>
    API.
    
    @signal checkServiceKeyFinished(bool, str) emitted after the service key
        check has been performed. It gives a flag indicating validity
        (boolean) and an error message in case of a network error (string).
    @signal submitUrlError(str) emitted with the error string, if the URL scan
        submission returned an error.
    @signal urlScanReport(str) emitted with the URL of the URL scan report page
    @signal fileScanReport(str) emitted with the URL of the file scan report
        page
    """
    checkServiceKeyFinished = pyqtSignal(bool, str)
    submitUrlError = pyqtSignal(str)
    urlScanReport = pyqtSignal(str)
    fileScanReport = pyqtSignal(str)
    
    TestServiceKeyScanID = \
        "4feed2c2e352f105f6188efd1d5a558f24aee6971bdf96d5fdb19c197d6d3fad"
    
    ServiceResult_RequestLimitReached = -2
    ServiceResult_InvalidServiceKey = -1
    ServiceResult_ItemNotPresent = 0
    ServiceResult_ItemPresent = 1
    
    GetFileReportPattern = "{0}://www.virustotal.com/api/get_file_report.json"
    ScanUrlPattern = "{0}://www.virustotal.com/api/scan_url.json"
    GetUrlReportPattern = "{0}://www.virustotal.com/api/get_url_report.json"
    
    ReportUrlScanPagePattern = \
        "http://www.virustotal.com/url-scan/report.html?id={0}"
    ReportFileScanPagePattern = \
        "http://www.virustotal.com/file-scan/report.html?id={0}"
    
    SearchUrl = "http://www.virustotal.com/search.html"
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(VirusTotalAPI, self).__init__(parent)
        
        self.__replies = []
        
        self.__loadSettings()
    
    def __loadSettings(self):
        """
        Private method to load the settings.
        """
        if Preferences.getHelp("VirusTotalSecure"):
            protocol = "https"
        else:
            protocol = "http"
        self.GetFileReportUrl = self.GetFileReportPattern.format(protocol)
        self.ScanUrlUrl = self.ScanUrlPattern.format(protocol)
        self.GetUrlReportUrl = self.GetUrlReportPattern.format(protocol)
        
        self.errorMessages = {
            -2: self.tr("Request limit has been reached."),
            -1: self.tr("Invalid key given."),
            0: self.tr("Requested item is not present.")
        }
    
    def preferencesChanged(self):
        """
        Public slot to handle a change of preferences.
        """
        self.__loadSettings()
    
    def checkServiceKeyValidity(self, key, protocol=""):
        """
        Public method to check the validity of the given service key.
        
        @param key service key (string)
        @param protocol protocol used to access VirusTotal (string)
        """
        if protocol == "":
            urlStr = self.GetFileReportUrl
        else:
            urlStr = self.GetFileReportPattern.format(protocol)
        request = QNetworkRequest(QUrl(urlStr))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        params = QByteArray("key={0}&resource={1}".format(
            key, self.TestServiceKeyScanID).encode("utf-8"))
        
        import Helpviewer.HelpWindow
        nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.post(request, params)
        reply.finished.connect(self.__checkServiceKeyValidityFinished)
        self.__replies.append(reply)
    
    def __checkServiceKeyValidityFinished(self):
        """
        Private slot to determine the result of the service key validity check.
        """
        res = False
        msg = ""
        
        reply = self.sender()
        if reply.error() == QNetworkReply.NoError:
            result = json.loads(str(reply.readAll(), "utf-8"))
            if result["result"] != self.ServiceResult_InvalidServiceKey:
                res = True
        else:
            msg = reply.errorString()
        self.__replies.remove(reply)
        
        self.checkServiceKeyFinished.emit(res, msg)
    
    def submitUrl(self, url):
        """
        Public method to submit an URL to be scanned.
        
        @param url url to be scanned (QUrl)
        """
        request = QNetworkRequest(QUrl(self.ScanUrlUrl))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        params = QByteArray("key={0}&url=".format(
            Preferences.getHelp("VirusTotalServiceKey")).encode("utf-8"))\
            .append(QUrl.toPercentEncoding(url.toString()))
        
        import Helpviewer.HelpWindow
        nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.post(request, params)
        reply.finished.connect(self.__submitUrlFinished)
        self.__replies.append(reply)
    
    def __submitUrlFinished(self):
        """
        Private slot to determine the result of the URL scan submission.
        """
        reply = self.sender()
        if reply.error() == QNetworkReply.NoError:
            result = json.loads(str(reply.readAll(), "utf-8"))
            if result["result"] == self.ServiceResult_ItemPresent:
                self.urlScanReport.emit(
                    self.ReportUrlScanPagePattern.format(result["scan_id"]))
                self.__getFileScanReportUrl(result["scan_id"])
            else:
                self.submitUrlError.emit(self.errorMessages[result["result"]])
        else:
            self.submitUrlError.emit(reply.errorString())
        self.__replies.remove(reply)
    
    def __getFileScanReportUrl(self, scanId):
        """
        Private method to get the report URL for a file scan.
        
        @param scanId ID of the scan to get the report URL for (string)
        """
        request = QNetworkRequest(QUrl(self.GetUrlReportUrl))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        params = QByteArray("key={0}&resource={1}".format(
            Preferences.getHelp("VirusTotalServiceKey"), scanId)
            .encode("utf-8"))
        
        import Helpviewer.HelpWindow
        nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.post(request, params)
        reply.finished.connect(self.__getFileScanReportUrlFinished)
        self.__replies.append(reply)
    
    def __getFileScanReportUrlFinished(self):
        """
        Private slot to determine the result of the file scan report URL
        request.
        """
        reply = self.sender()
        if reply.error() == QNetworkReply.NoError:
            result = json.loads(str(reply.readAll(), "utf-8"))
            if "file-report" in result:
                self.fileScanReport.emit(
                    self.ReportFileScanPagePattern.format(
                        result["file-report"]))
        self.__replies.remove(reply)
    
    @classmethod
    def getSearchRequestData(cls, term):
        """
        Class method to assemble the search request data structure.
        
        @param term search term (string)
        @return tuple of network request object, operation and parameters
            (QNetworkRequest, QNetworkAccessManager.Operation, QByteArray)
        """
        request = QNetworkRequest(QUrl(cls.SearchUrl))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        op = QNetworkAccessManager.PostOperation
        params = QByteArray(b"chain=").append(QUrl.toPercentEncoding(term))
        
        return (request, op, params)
