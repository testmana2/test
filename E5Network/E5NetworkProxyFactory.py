# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a network proxy factory.
"""

import sys
import os

from PyQt4.QtCore import QUrl, Qt, QCoreApplication
from PyQt4.QtGui import QMessageBox, QDialog
from PyQt4.QtNetwork import QNetworkProxyFactory, QNetworkProxy, QNetworkProxyQuery

from UI.AuthenticationDialog import AuthenticationDialog

import Preferences

def schemeFromProxyType(proxyType):
    """
    Module function to determine the scheme name from the proxy type.
    
    @param proxyType type of the proxy (QNetworkProxy.ProxyType)
    @return scheme (string, one of Http, Https, Ftp)
    """
    scheme = ""
    if proxyType == QNetworkProxy.HttpProxy:
        scheme = "Http"
    elif proxyType == QNetworkProxy.HttpCachingProxy:
        scheme = "Https"
    elif proxyType == QNetworkProxy.FtpCachingProxy:
        scheme = "Ftp"
    elif proxyType == QNetworkProxy.NoProxy:
        scheme = "NoProxy"
    return scheme

def proxyAuthenticationRequired(proxy, auth):
    """
    Module slot to handle a proxy authentication request.
    
    @param proxy reference to the proxy object (QNetworkProxy)
    @param auth reference to the authenticator object (QAuthenticator)
    """
    info = QCoreApplication.translate("E5NetworkProxyFactory", 
        "<b>Connect to proxy '{0}' using:</b>")\
        .format(Qt.escape(proxy.hostName()))
    
    dlg = AuthenticationDialog(info, proxy.user(), True)
    if dlg.exec_() == QDialog.Accepted:
        username, password = dlg.getData()
        auth.setUser(username)
        auth.setPassword(password)
        if dlg.shallSave():
            scheme = schemeFromProxyType(proxy.type())
            if scheme and scheme != "NoProxy":
                Preferences.setUI("ProxyUser/{0}".format(scheme), username)
                Preferences.setUI("ProxyPassword/{0}".format(scheme), password)
            proxy.setUser(username)
            proxy.setPassword(password)

class E5NetworkProxyFactory(QNetworkProxyFactory):
    """
    Class implementing a network proxy factory.
    """
    def __init__(self):
        """
        Constructor
        """
        QNetworkProxyFactory.__init__(self)
    
    def queryProxy(self, query):
        """
        Public method to determine a proxy for a given query.
        
        @param query reference to the query object (QNetworkProxyQuery)
        @return list of proxies in order of preference (list of QNetworkProxy)
        """
        if query.queryType() == QNetworkProxyQuery.UrlRequest and \
           query.protocolTag() in ["http", "https", "ftp"] and \
           Preferences.getUI("UseProxy"):
            if Preferences.getUI("UseSystemProxy"):
                proxyList = QNetworkProxyFactory.systemProxyForQuery(query)
                if sys.platform not in ["darwin", "nt"] and \
                   len(proxyList) == 1 and \
                   proxyList[0].type() == QNetworkProxy.NoProxy:
                    # try it the Python way
                    # scan the environment for variables named <scheme>_proxy
                    # scan over whole environment to make this case insensitive
                    for name, value in os.environ.items():
                        name = name.lower()
                        if value and name[-6:] == '_proxy' and \
                           name[:-6] == query.protocolTag().lower():
                            url = QUrl(value)
                            if url.scheme() == "http":
                                proxyType = QNetworkProxy.HttpProxy
                            elif url.scheme() == "https":
                                proxyType = QNetworkProxy.HttpCachingProxy
                            elif url.scheme() == "ftp":
                                proxyType = QNetworkProxy.FtpCachingProxy
                            else:
                                proxyType = QNetworkProxy.HttpProxy
                            proxy = QNetworkProxy(proxyType, url.host(), url.port(), 
                                                  url.userName(), url.password())
                            proxyList = [proxy]
                            break
                scheme = schemeFromProxyType(proxyList[0].type())
                if scheme == "":
                    scheme = "Http"
                if scheme != "NoProxy":
                    proxyList[0].setUser(
                        Preferences.getUI("ProxyUser/{0}".format(scheme)))
                    proxyList[0].setPassword(
                        Preferences.getUI("ProxyPassword/{0}".format(scheme)))
                return proxyList
            else:
                if Preferences.getUI("UseHttpProxyForAll"):
                    protocol = "Http"
                else:
                    protocol = query.protocolTag().capitalize()
                host = Preferences.getUI("ProxyHost/{0}".format(protocol))
                if not host:
                    QMessageBox.critical(None,
                        QCoreApplication.translate("E5NetworkProxyFactory", 
                            "Proxy Configuration Error"),
                        QCoreApplication.translate("E5NetworkProxyFactory", 
                            """Proxy usage was activated"""
                            """ but no proxy host for protocol"""
                            """ '{0}' configured.""").format(protocol))
                    return [QNetworkProxy(QNetworkProxy.DefaultProxy)]
                else:
                    if protocol == "Http":
                        proxy = QNetworkProxy(QNetworkProxy.HttpProxy, host, 
                            Preferences.getUI("ProxyPort/Http"),
                            Preferences.getUI("ProxyUser/Http"),
                            Preferences.getUI("ProxyPassword/Http"))
                    elif protocol == "Https":
                        proxy = QNetworkProxy(QNetworkProxy.HttpCachingProxy, host, 
                            Preferences.getUI("ProxyPort/Https"),
                            Preferences.getUI("ProxyUser/Https"),
                            Preferences.getUI("ProxyPassword/Https"))
                    elif protocol == "Ftp":
                        proxy = QNetworkProxy(QNetworkProxy.FtpCachingProxy, host, 
                            Preferences.getUI("ProxyPort/Ftp"),
                            Preferences.getUI("ProxyUser/Ftp"),
                            Preferences.getUI("ProxyPassword/Ftp"))
                    else:
                        proxy = QNetworkProxy(QNetworkProxy.DefaultProxy)
                    return [proxy, QNetworkProxy(QNetworkProxy.DefaultProxy)]
        else:
            return [QNetworkProxy(QNetworkProxy.NoProxy)]
