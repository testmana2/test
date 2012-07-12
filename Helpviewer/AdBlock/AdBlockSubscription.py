# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the AdBlock subscription class.
"""

import os

from PyQt4.QtCore import pyqtSignal, Qt, QObject, QByteArray, QDateTime, QUrl, \
    QCryptographicHash, QFile, QIODevice, QTextStream
from PyQt4.QtNetwork import QNetworkRequest, QNetworkReply

from E5Gui import E5MessageBox

from .AdBlockRule import AdBlockRule

import Helpviewer.HelpWindow

import Utilities
import Preferences


class AdBlockSubscription(QObject):
    """
    Class implementing the AdBlock subscription.
    
    @signal changed() emitted after the subscription has changed
    @signal rulesChanged() emitted after the subscription's rules have changed
    """
    changed = pyqtSignal()
    rulesChanged = pyqtSignal()
    
    def __init__(self, url, parent=None, default=False):
        """
        Constructor
        
        @param url AdBlock URL for the subscription (QUrl)
        @param parent reference to the parent object (QObject)
        @param default flag indicating a default subscription (Boolean)
        """
        super().__init__(parent)
        
        self.__url = url.toEncoded()
        self.__enabled = False
        self.__downloading = None
        self.__defaultSubscription = default
        
        self.__title = ""
        self.__location = QByteArray()
        self.__lastUpdate = QDateTime()
        
        self.__rules = []   # list containing all AdBlock rules
        
        self.__networkExceptionRules = []
        self.__networkBlockRules = []
        self.__pageRules = []
        
        self.__parseUrl(url)
    
    def __parseUrl(self, url):
        """
        Private method to parse the AdBlock URL for the subscription.
        
        @param url AdBlock URL for the subscription (QUrl)
        """
        if url.scheme() != "abp":
            return
        
        if url.path() != "subscribe":
            return
        
        self.__title = \
            QUrl.fromPercentEncoding(url.encodedQueryItemValue("title"))
        self.__enabled = \
            QUrl.fromPercentEncoding(url.encodedQueryItemValue("enabled")) != "false"
        self.__location = \
            QByteArray(QUrl.fromPercentEncoding(url.encodedQueryItemValue("location")))
        
        lastUpdateByteArray = url.encodedQueryItemValue("lastUpdate")
        lastUpdateString = QUrl.fromPercentEncoding(lastUpdateByteArray)
        self.__lastUpdate = QDateTime.fromString(lastUpdateString, Qt.ISODate)
        
        self.__loadRules()
    
    def url(self):
        """
        Public method to generate the url for this subscription.
        
        @return AdBlock URL for the subscription (QUrl)
        """
        url = QUrl()
        url.setScheme("abp")
        url.setPath("subscribe")
        
        queryItems = []
        queryItems.append(("location", bytes(self.__location).decode()))
        queryItems.append(("title", self.__title))
        if not self.__enabled:
            queryItems.append(("enabled", "false"))
        if self.__lastUpdate.isValid():
            queryItems.append(("lastUpdate",
                               self.__lastUpdate.toString(Qt.ISODate)))
        url.setQueryItems(queryItems)
        return url
    
    def isEnabled(self):
        """
        Public method to check, if the subscription is enabled.
        
        @return flag indicating the enabled status (boolean)
        """
        return self.__enabled
    
    def setEnabled(self, enabled):
        """
        Public method to set the enabled status.
        
        @param enabled flag indicating the enabled status (boolean)
        """
        if self.__enabled == enabled:
            return
        
        self.__enabled = enabled
        self.__populateCache()
        self.changed.emit()
    
    def title(self):
        """
        Public method to get the subscription title.
        
        @return subscription title (string)
        """
        return self.__title
    
    def setTitle(self, title):
        """
        Public method to set the subscription title.
        
        @param title subscription title (string)
        """
        if self.__title == title:
            return
        
        self.__title = title
        self.changed.emit()
    
    def location(self):
        """
        Public method to get the subscription location.
        
        @return URL of the subscription location (QUrl)
        """
        return QUrl.fromEncoded(self.__location)
    
    def setLocation(self, url):
        """
        Public method to set the subscription location.
        
        @param url URL of the subscription location (QUrl)
        """
        if url == self.location():
            return
        
        self.__location = url.toEncoded()
        self.__lastUpdate = QDateTime()
        self.changed.emit()
    
    def lastUpdate(self):
        """
        Public method to get the date and time of the last update.
        
        @return date and time of the last update (QDateTime)
        """
        return self.__lastUpdate
    
    def rulesFileName(self):
        """
        Public method to get the name of the rules file.
        
        @return name of the rules file (string)
        """
        if self.location().scheme() == "file":
            return self.location().toLocalFile()
        
        if self.__location.isEmpty():
            return ""
        
        sha1 = bytes(
            QCryptographicHash.hash(self.__location, QCryptographicHash.Sha1).toHex())\
            .decode()
        dataDir = os.path.join(Utilities.getConfigDir(), "browser", "subscriptions")
        if not os.path.exists(dataDir):
            os.makedirs(dataDir)
        fileName = os.path.join(dataDir, "adblock_subscription_{0}".format(sha1))
        return fileName
    
    def __loadRules(self):
        """
        Private method to load the rules of the subscription.
        """
        fileName = self.rulesFileName()
        f = QFile(fileName)
        if f.exists():
            if not f.open(QIODevice.ReadOnly):
                E5MessageBox.warning(None,
                    self.trUtf8("Load subscription rules"),
                    self.trUtf8("""Unable to open adblock file '{0}' for reading.""")\
                        .format(fileName))
            else:
                textStream = QTextStream(f)
                header = textStream.readLine(1024)
                if not header.startswith("[Adblock"):
                    E5MessageBox.warning(None,
                        self.trUtf8("Load subscription rules"),
                        self.trUtf8("""Adblock file '{0}' does not start"""
                                    """ with [Adblock.""")\
                            .format(fileName))
                    f.close()
                    f.remove()
                    self.__lastUpdate = QDateTime()
                else:
                    self.__rules = []
                    while not textStream.atEnd():
                        line = textStream.readLine()
                        self.__rules.append(AdBlockRule(line))
                    self.__populateCache()
                    self.changed.emit()
        
        self.checkForUpdate()
    
    def checkForUpdate(self):
        """
        Public method to check for an update.
        """
        if not self.__lastUpdate.isValid() or \
           self.__lastUpdate.addDays(Preferences.getHelp("AdBlockUpdatePeriod")) < \
                QDateTime.currentDateTime():
            self.updateNow()
    
    def updateNow(self):
        """
        Public method to update the subscription immediately.
        """
        if self.__downloading is not None:
            return
        
        if not self.location().isValid():
            return
        
        if self.location().scheme() == "file":
            self.__lastUpdate = QDateTime.currentDateTime()
            self.__loadRules()
            self.changed.emit()
            return
        
        request = QNetworkRequest(self.location())
        self.__downloading = \
            Helpviewer.HelpWindow.HelpWindow.networkAccessManager().get(request)
        self.__downloading.finished[()].connect(self.__rulesDownloaded)
    
    def __rulesDownloaded(self):
        """
        Private slot to deal with the downloaded rules.
        """
        reply = self.sender()
        
        response = reply.readAll()
        redirect = reply.attribute(QNetworkRequest.RedirectionTargetAttribute) or QUrl()
        reply.close()
        self.__downloading = None
        
        if reply.error() != QNetworkReply.NoError:
            if not self.__defaultSubscription:
                # don't show error if we try to load the default
                E5MessageBox.warning(None,
                    self.trUtf8("Downloading subscription rules"),
                    self.trUtf8("""<p>Subscription rules could not be downloaded.</p>"""
                                """<p>Error: {0}</p>""").format(reply.errorString()))
            else:
                # reset after first download attempt
                self.__defaultSubscription = False
            return
        
        if redirect.isValid():
            request = QNetworkRequest(redirect)
            self.__downloading = \
                Helpviewer.HelpWindow.HelpWindow.networkAccessManager().get(request)
            self.__downloading.finished[()].connect(self.__rulesDownloaded)
            return
        
        if response.isEmpty():
            E5MessageBox.warning(None,
                self.trUtf8("Downloading subscription rules"),
                self.trUtf8("""Got empty subscription rules."""))
            return
        
        fileName = self.rulesFileName()
        f = QFile(fileName)
        if not f.open(QIODevice.ReadWrite):
            E5MessageBox.warning(None,
                self.trUtf8("Downloading subscription rules"),
                self.trUtf8("""Unable to open adblock file '{0}' for writing.""")\
                    .file(fileName))
            return
        f.write(response)
        self.__lastUpdate = QDateTime.currentDateTime()
        self.__loadRules()
        self.changed.emit()
        self.__downloading = None
    
    def saveRules(self):
        """
        Public method to save the subscription rules.
        """
        fileName = self.rulesFileName()
        if not fileName:
            return
        
        f = QFile(fileName)
        if not f.open(QIODevice.ReadWrite | QIODevice.Truncate):
            E5MessageBox.warning(None,
                self.trUtf8("Saving subscription rules"),
                self.trUtf8("""Unable to open adblock file '{0}' for writing.""")\
                    .format(fileName))
            return
        
        textStream = QTextStream(f)
        textStream << "[Adblock Plus 0.7.1]\n"
        for rule in self.__rules:
            textStream << rule.filter() << "\n"
    
    def pageRules(self):
        """
        Public method to get the page rules of the subscription.
        
        @return list of rule objects (list of AdBlockRule)
        """
        return self.__pageRules[:]
    
    def allow(self, urlString):
        """
        Public method to check, if the given URL is allowed.
        
        @return reference to the rule object or None (AdBlockRule)
        """
        for rule in self.__networkExceptionRules:
            if rule.networkMatch(urlString):
                return rule
        
        return None
    
    def block(self, urlString):
        """
        Public method to check, if the given URL should be blocked.
        
        @return reference to the rule object or None (AdBlockRule)
        """
        for rule in self.__networkBlockRules:
            if rule.networkMatch(urlString):
                return rule
        
        return None
    
    def allRules(self):
        """
        Public method to get the list of rules.
        
        @return list of rules (list of AdBlockRule)
        """
        return self.__rules[:]
    
    def addRule(self, rule):
        """
        Public method to add a rule.
        
        @param rule reference to the rule to add (AdBlockRule)
        """
        self.__rules.append(rule)
        self.__populateCache()
        self.rulesChanged.emit()
    
    def removeRule(self, offset):
        """
        Public method to remove a rule given the offset.
        
        @param offset offset of the rule to remove (integer)
        """
        if offset < 0 or offset > len(self.__rules):
            return
        
        del self.__rules[offset]
        self.__populateCache()
        self.rulesChanged.emit()
    
    def replaceRule(self, rule, offset):
        """
        Public method to replace a rule given the offset.
        
        @param rule reference to the rule to set (AdBlockRule)
        @param offset offset of the rule to remove (integer)
        """
        self.__rules[offset] = rule
        self.__populateCache()
        self.rulesChanged.emit()
    
    def __populateCache(self):
        """
        Private method to populate the various rule caches.
        """
        self.__networkBlockRules = []
        self.__networkExceptionRules = []
        self.__pageRules = []
        if not self.isEnabled():
            return
        
        for rule in self.__rules:
            if not rule.isEnabled():
                continue
            
            if rule.isCSSRule():
                self.__pageRules.append(rule)
            elif rule.isException():
                self.__networkExceptionRules.append(rule)
            else:
                self.__networkBlockRules.append(rule)
