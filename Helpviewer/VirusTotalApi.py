# -*- coding: utf-8 -*-

# Copyright (c) 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the <a href="http://www.virustotal.com">VirusTotal</a> API class.
"""

import json

from PyQt4.QtCore import QObject, QUrl, QByteArray, QCoreApplication, QThread
from PyQt4.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager

import Helpviewer.HelpWindow

import Preferences

class VirusTotalAPI(QObject):
    """
    Class implementing the <a href="http://www.virustotal.com">VirusTotal</a> API.
    """
    TestServiceKeyScanID = \
        "4feed2c2e352f105f6188efd1d5a558f24aee6971bdf96d5fdb19c197d6d3fad"
    
    ServiceResult_RequestLimitReached = -2
    ServiceResult_InvalidServiceKey = -1
    ServiceResult_ItemNotPresent = 0
    ServiceResult_ItemPresent = 1
    
    GetFileReportPattern = "{0}://www.virustotal.com/api/get_file_report.json"
    ScanUrlPattern = "{0}://www.virustotal.com/api/scan_url.json"
    GetUrlReportPattern = "{0}://www.virustotal.com/api/get_url_report.json"
    
    ReportUrlScanPagePattern = "http://www.virustotal.com/url-scan/report.html?id={0}"
    ReportFileScanPagePattern = "http://www.virustotal.com/file-scan/report.html?id={0}"
    
    SearchUrl = "http://www.virustotal.com/search.html"
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        QObject.__init__(self, parent)
        
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
            -2: self.trUtf8("Request limit has been reached."),
            -1: self.trUtf8("Invalid key given."),
             0: self.trUtf8("Requested item is not present.")
        }
    
    def checkServiceKeyValidity(self, key, protocol=""):
        """
        Public method to check the validity of the given service key.
        
        @param key service key (string)
        @param protocol protocol used to access VirusTotal (string)
        @return flag indicating validity (boolean) and an error message in
            case of a network error (string)
        """
        if protocol == "":
            urlStr = self.GetFileReportUrl
        else:
            urlStr = self.GetFileReportPattern.format(protocol)
        request = QNetworkRequest(QUrl(urlStr))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        params = QByteArray("key={0}&resource={1}".format(
            key, self.TestServiceKeyScanID))
        
        nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.post(request, params)
        while not reply.isFinished():
            QCoreApplication.processEvents()
            QThread.msleep(100)
            if QCoreApplication.closingDown():
                reply.abort()
            QCoreApplication.processEvents()
        if reply.error() == QNetworkReply.NoError:
            result = json.loads(str(reply.readAll(), "utf-8"))
            if result["result"] != self.ServiceResult_InvalidServiceKey:
                return True, ""
            else:
                return False, ""
        
        return False, reply.errorString()
    
    def submitUrl(self, url):
        """
        Public method to submit an URL to be scanned.
        
        @param url url to be scanned (QUrl)
        @return flag indicating success (boolean) and the scan ID (string)
        """
        request = QNetworkRequest(QUrl(self.ScanUrlUrl))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        params = QByteArray(
            "key={0}&url=".format(Preferences.getHelp("VirusTotalServiceKey")))\
            .append(QUrl.toPercentEncoding(url.toString()))
        
        nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.post(request, params)
        while not reply.isFinished():
            QCoreApplication.processEvents()
            QThread.msleep(100)
            if QCoreApplication.closingDown():
                reply.abort()
            QCoreApplication.processEvents()
        if reply.error() == QNetworkReply.NoError:
            result = json.loads(str(reply.readAll(), "utf-8"))
            if result["result"] == self.ServiceResult_ItemPresent:
                return True, result["scan_id"]
            else:
                return False, self.errorMessages[result["result"]]
        
        return False, reply.errorString()
    
    def getUrlScanReportUrl(self, scanId):
        """
        Public method to get the report URL for a URL scan.
        
        @param scanId ID of the scan to get the report URL for (string)
        @return URL scan report URL (string)
        """
        return self.ReportUrlScanPagePattern.format(scanId)
        
    def getFileScanReportUrl(self, scanId):
        """
        Public method to get the report URL for a file scan.
        
        @param scanId ID of the scan to get the report URL for (string)
        @return file scan report URL (string)
        """
        fileScanPageUrl = ""    # default value
        
        request = QNetworkRequest(QUrl(self.GetUrlReportUrl))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        params = QByteArray("key={0}&resource={1}".format(
            Preferences.getHelp("VirusTotalServiceKey"), scanId))
        
        nam = Helpviewer.HelpWindow.HelpWindow.networkAccessManager()
        reply = nam.post(request, params)
        while not reply.isFinished():
            QCoreApplication.processEvents()
            QThread.msleep(100)
            if QCoreApplication.closingDown():
                reply.abort()
            QCoreApplication.processEvents()
        if reply.error() == QNetworkReply.NoError:
            result = json.loads(str(reply.readAll(), "utf-8"))
            if "file-report" in result:
                fileScanPageUrl = self.ReportFileScanPagePattern.format(
                    result["file-report"])
        
        return fileScanPageUrl
    
    @classmethod
    def getSearchRequestData(cls, term):
        """
        
        """
        request = QNetworkRequest(QUrl(cls.SearchUrl))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        op = QNetworkAccessManager.PostOperation
        params = QByteArray("chain=").append(QUrl.toPercentEncoding(term))
        
        return (request, op, params)
