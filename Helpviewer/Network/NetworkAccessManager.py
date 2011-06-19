# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a QNetworkAccessManager subclass.
"""

import os

from PyQt4.QtCore import pyqtSignal, QByteArray
from PyQt4.QtGui import QDialog
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
try:
    from PyQt4.QtNetwork import QSslCertificate, QSslConfiguration, QSslSocket, \
        QSslError
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False

from E5Gui import E5MessageBox

from E5Network.E5NetworkProxyFactory import E5NetworkProxyFactory, \
    proxyAuthenticationRequired

from UI.AuthenticationDialog import AuthenticationDialog

from Helpviewer.HelpLanguagesDialog import HelpLanguagesDialog
import Helpviewer.HelpWindow

from .NetworkProtocolUnknownErrorReply import NetworkProtocolUnknownErrorReply
from .NetworkDiskCache import NetworkDiskCache

from .QtHelpAccessHandler import QtHelpAccessHandler
from .PyrcAccessHandler import PyrcAccessHandler
from .AboutAccessHandler import AboutAccessHandler
from .FtpAccessHandler import FtpAccessHandler

from Helpviewer.AdBlock.AdBlockAccessHandler import AdBlockAccessHandler

import Preferences
import Utilities


class NetworkAccessManager(QNetworkAccessManager):
    """
    Class implementing a QNetworkAccessManager subclass.
    
    @signal requestCreated(QNetworkAccessManager.Operation, QNetworkRequest, QNetworkReply)
        emitted after the request has been created
    """
    requestCreated = pyqtSignal(
        QNetworkAccessManager.Operation, QNetworkRequest, QNetworkReply)
    
    def __init__(self, engine, parent=None):
        """
        Constructor
        
        @param engine reference to the help engine (QHelpEngine)
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__adblockNetwork = None
        
        self.__schemeHandlers = {}  # dictionary of scheme handlers
        
        self.__proxyFactory = E5NetworkProxyFactory()
        self.setProxyFactory(self.__proxyFactory)
        
        self.__setDiskCache()
        self.languagesChanged()
        
        if SSL_AVAILABLE:
            caList = self.__getSystemCaCertificates()
            certificateDict = Preferences.toDict(
                    Preferences.Prefs.settings.value("Help/CaCertificatesDict"))
            for server in certificateDict:
                for cert in QSslCertificate.fromData(certificateDict[server]):
                    if cert not in caList:
                        caList.append(cert)
            sslCfg = QSslConfiguration.defaultConfiguration()
            sslCfg.setCaCertificates(caList)
            QSslConfiguration.setDefaultConfiguration(sslCfg)
            
            self.sslErrors.connect(self.__sslErrors)
        
        self.proxyAuthenticationRequired.connect(proxyAuthenticationRequired)
        self.authenticationRequired.connect(self.__authenticationRequired)
        
        # register scheme handlers
        self.setSchemeHandler("qthelp", QtHelpAccessHandler(engine, self))
        self.setSchemeHandler("pyrc", PyrcAccessHandler(self))
        self.setSchemeHandler("about", AboutAccessHandler(self))
        self.setSchemeHandler("abp", AdBlockAccessHandler(self))
        self.setSchemeHandler("ftp", FtpAccessHandler(self))
    
    def setSchemeHandler(self, scheme, handler):
        """
        Public method to register a scheme handler.
        
        @param scheme access scheme (string)
        @param handler reference to the scheme handler object (SchemeAccessHandler)
        """
        self.__schemeHandlers[scheme] = handler
    
    def createRequest(self, op, request, outgoingData=None):
        """
        Protected method to create a request.
        
        @param op the operation to be performed (QNetworkAccessManager.Operation)
        @param request reference to the request object (QNetworkRequest)
        @param outgoingData reference to an IODevice containing data to be sent
            (QIODevice)
        @return reference to the created reply object (QNetworkReply)
        """
        scheme = request.url().scheme()
        if scheme == "https" and (not SSL_AVAILABLE or not QSslSocket.supportsSsl()):
            return NetworkProtocolUnknownErrorReply(scheme, self)
        
        if op == QNetworkAccessManager.PostOperation and outgoingData is not None:
            outgoingDataByteArray = outgoingData.peek(1024 * 1024)
            Helpviewer.HelpWindow.HelpWindow.passwordManager().post(
                request, outgoingDataByteArray)
        
        reply = None
        if scheme in self.__schemeHandlers:
            reply = self.__schemeHandlers[scheme]\
                        .createRequest(op, request, outgoingData)
        if reply is not None:
            return reply
        
        req = QNetworkRequest(request)
        if hasattr(QNetworkRequest, 'HttpPipeliningAllowedAttribute'):
            req.setAttribute(QNetworkRequest.HttpPipeliningAllowedAttribute, True)
        if not self.__acceptLanguage.isEmpty():
            req.setRawHeader("Accept-Language", self.__acceptLanguage)
        
        # set cache policy
        req.setAttribute(QNetworkRequest.CacheLoadControlAttribute,
            Preferences.getHelp("CachePolicy"))
        
        # AdBlock code
        if op == QNetworkAccessManager.GetOperation:
            if self.__adblockNetwork is None:
                self.__adblockNetwork = \
                    Helpviewer.HelpWindow.HelpWindow.adblockManager().network()
            reply = self.__adblockNetwork.block(req)
            if reply is not None:
                reply.setParent(self)
                return reply
        
        reply = QNetworkAccessManager.createRequest(self, op, req, outgoingData)
        self.requestCreated.emit(op, req, reply)
        
        return reply
    
    def __authenticationRequired(self, reply, auth):
        """
        Private slot to handle an authentication request.
        
        @param reply reference to the reply object (QNetworkReply)
        @param auth reference to the authenticator object (QAuthenticator)
        """
        urlRoot = "{0}://{1}"\
            .format(reply.url().scheme(), reply.url().authority())
        if not auth.realm():
            info = self.trUtf8("<b>Enter username and password for '{0}'</b>")\
                .format(urlRoot)
        else:
            info = self.trUtf8("<b>Enter username and password for '{0}', "
                               "realm '{1}'</b>").format(urlRoot, auth.realm())
        
        dlg = AuthenticationDialog(info, auth.user(),
                                   Preferences.getUser("SavePasswords"),
                                   Preferences.getUser("SavePasswords"))
        if Preferences.getUser("SavePasswords"):
            username, password = \
                Helpviewer.HelpWindow.HelpWindow.passwordManager().getLogin(
                    reply.url(), auth.realm())
            if username:
                dlg.setData(username, password)
        if dlg.exec_() == QDialog.Accepted:
            username, password = dlg.getData()
            auth.setUser(username)
            auth.setPassword(password)
            if Preferences.getUser("SavePasswords"):
                Helpviewer.HelpWindow.HelpWindow.passwordManager().setLogin(
                    reply.url(), auth.realm(), username, password)
    
    def __sslErrors(self, reply, errors):
        """
        Private slot to handle SSL errors.
        
        @param reply reference to the reply object (QNetworkReply)
        @param errors list of SSL errors (list of QSslError)
        """
        caMerge = {}
        certificateDict = Preferences.toDict(
                Preferences.Prefs.settings.value("Help/CaCertificatesDict"))
        for server in certificateDict:
            caMerge[server] = QSslCertificate.fromData(certificateDict[server])
        caNew = []
        
        errorStrings = []
        url = reply.url()
        server = url.host()
        if url.port() != -1:
            server += ":{0:d}".format(url.port())
        for err in errors:
            if err.error() == QSslError.NoError:
                continue
            if server in caMerge and err.certificate() in caMerge[server]:
                continue
            errorStrings.append(err.errorString())
            if not err.certificate().isNull():
                cert = err.certificate()
                if cert not in caNew:
                    caNew.append(cert)
        if not errorStrings:
            reply.ignoreSslErrors()
            return
        
        errorString = '.</li><li>'.join(errorStrings)
        ret = E5MessageBox.yesNo(None,
            self.trUtf8("SSL Errors"),
            self.trUtf8("""<p>SSL Errors for <br /><b>{0}</b>"""
                        """<ul><li>{1}</li></ul></p>"""
                        """<p>Do you want to ignore these errors?</p>""")\
                .format(reply.url().toString(), errorString),
            icon=E5MessageBox.Warning)
        
        if ret:
            if len(caNew) > 0:
                certinfos = []
                for cert in caNew:
                    certinfos.append(self.__certToString(cert))
                ret = E5MessageBox.yesNo(None,
                    self.trUtf8("Certificates"),
                    self.trUtf8("""<p>Certificates:<br/>{0}<br/>"""
                                """Do you want to accept all these certificates?</p>""")\
                        .format("".join(certinfos)))
                if ret:
                    if server not in caMerge:
                        caMerge[server] = []
                    for cert in caNew:
                        caMerge[server].append(cert)
                    
                    sslCfg = QSslConfiguration.defaultConfiguration()
                    caList = sslCfg.caCertificates()
                    for cert in caNew:
                        caList.append(cert)
                    sslCfg.setCaCertificates(caList)
                    QSslConfiguration.setDefaultConfiguration(sslCfg)
                    reply.setSslConfiguration(sslCfg)
                    
                    certificateDict = {}
                    for server in caMerge:
                        pems = QByteArray()
                        for cert in caMerge[server]:
                            pems.append(cert.toPem() + '\n')
                        certificateDict[server] = pems
                    Preferences.Prefs.settings.setValue("Help/CaCertificatesDict",
                        certificateDict)
                else:
                    reply.abort()
                    return
            
            reply.ignoreSslErrors()
        
        else:
            reply.abort()
    
    def __certToString(self, cert):
        """
        Private method to convert a certificate to a formatted string.
        
        @param cert certificate to convert (QSslCertificate)
        @return formatted string (string)
        """
        result = "<p>"
        
        result += self.trUtf8("Name: {0}")\
            .format(Utilities.decodeString(
                cert.subjectInfo(QSslCertificate.CommonName)))
        
        result += self.trUtf8("<br/>Organization: {0}")\
            .format(Utilities.decodeString(
                cert.subjectInfo(QSslCertificate.Organization)))
        
        result += self.trUtf8("<br/>Issuer: {0}")\
            .format(Utilities.decodeString(
                cert.issuerInfo(QSslCertificate.CommonName)))
        
        result += self.trUtf8("<br/>Not valid before: {0}<br/>Valid Until: {1}")\
            .format(cert.effectiveDate().toString("yyyy-MM-dd"),
                    cert.expiryDate().toString("yyyy-MM-dd"))
        
        result += "</p>"
        
        return result
    
    def __getSystemCaCertificates(self):
        """
        Private method to get the list of system certificates.
        
        @return list of system certificates (list of QSslCertificate)
        """
        caList = QSslCertificate.fromData(Preferences.toByteArray(
            Preferences.Prefs.settings.value("Help/SystemCertificates")))
        if not caList:
            caList = QSslSocket.systemCaCertificates()
        return caList
    
    def preferencesChanged(self):
        """
        Public slot to signal a change of preferences.
        """
        self.__setDiskCache()
    
    def languagesChanged(self):
        """
        Public slot to (re-)load the list of accepted languages.
        """
        languages = Preferences.toList(
            Preferences.Prefs.settings.value("Help/AcceptLanguages",
                HelpLanguagesDialog.defaultAcceptLanguages()))
        self.__acceptLanguage = HelpLanguagesDialog.httpString(languages)
    
    def __setDiskCache(self):
        """
        Private method to set the disk cache.
        """
        if NetworkDiskCache is not None:
            if Preferences.getHelp("DiskCacheEnabled"):
                diskCache = NetworkDiskCache(self)
                location = os.path.join(Utilities.getConfigDir(), "browser", 'cache')
                size = Preferences.getHelp("DiskCacheSize") * 1024 * 1024
                diskCache.setCacheDirectory(location)
                diskCache.setMaximumCacheSize(size)
            else:
                diskCache = None
            self.setCache(diskCache)
