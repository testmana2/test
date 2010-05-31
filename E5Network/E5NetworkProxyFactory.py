# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a network proxy factory.
"""

import sys
import os

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QMessageBox
from PyQt4.QtNetwork import QNetworkProxyFactory, QNetworkProxy, QNetworkProxyQuery

import Preferences

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
                            if url.scheme() in ["http", "https"]:
                                proxyType = QNetworkProxy.HttpProxy
                            else:
                                proxyType = QNetworkProxy.FtpCachingProxy
                            proxy = QNetworkProxy(proxyType, url.host(), url.port(), 
                                                  url.userName(), url.password())
                            proxyList = [proxy]
                            break
                if proxyList:
                    proxyList[0].setUser(Preferences.getUI("ProxyUser"))
                    proxyList[0].setPassword(Preferences.getUI("ProxyPassword"))
                    return proxyList
                else:
                    return [QNetworkProxy(QNetworkProxy.NoProxy)]
            else:
                host = Preferences.getUI("ProxyHost")
                if not host:
                    QMessageBox.critical(None,
                        self.trUtf8("Proxy Configuration Error"),
                        self.trUtf8("""Proxy usage was activated"""
                                    """ but no proxy host configured."""))
                    return [QNetworkProxy(QNetworkProxy.DefaultProxy)]
                else:
                    pProxyType = Preferences.getUI("ProxyType")
                    if pProxyType == 0:
                        proxyType = QNetworkProxy.HttpProxy
                    elif pProxyType == 1:
                        proxyType = QNetworkProxy.HttpCachingProxy
                    elif pProxyType == 2:
                        proxyType = QNetworkProxy.Socks5Proxy
                    proxy = QNetworkProxy(proxyType, host, 
                        Preferences.getUI("ProxyPort"),
                        Preferences.getUI("ProxyUser"),
                        Preferences.getUI("ProxyPassword"))
                    return [proxy, QNetworkProxy(QNetworkProxy.DefaultProxy)]
        else:
            return [QNetworkProxy(QNetworkProxy.NoProxy)]
