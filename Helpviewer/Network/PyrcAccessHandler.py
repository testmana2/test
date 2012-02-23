# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a scheme access handler for Python resources.
"""

from PyQt4.QtCore import QFile

from .SchemeAccessHandler import SchemeAccessHandler

from .NetworkReply import NetworkReply
from .NetworkProtocolUnknownErrorReply import NetworkProtocolUnknownErrorReply


class PyrcAccessHandler(SchemeAccessHandler):
    """
    Class implementing a scheme access handler for Python resources.
    """
    def createRequest(self, op, request, outgoingData=None):
        """
        Protected method to create a request.
        
        @param op the operation to be performed (QNetworkAccessManager.Operation)
        @param request reference to the request object (QNetworkRequest)
        @param outgoingData reference to an IODevice containing data to be sent
            (QIODevice)
        @return reference to the created reply object (QNetworkReply)
        """
        if request.url().toString() == "eric:home":
            htmlFile = QFile(":/html/startPage.html")
            htmlFile.open(QFile.ReadOnly)
            html = htmlFile.readAll()
            html = html.replace("@IMAGE@", "qrc:icons/ericWeb32.png")
            html = html.replace("@FAVICON@", "qrc:icons/ericWeb16.png")
            return NetworkReply(request, html, "text/html", self.parent())
        
        return NetworkProtocolUnknownErrorReply("eric", self.parent())
