# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a scheme access handler for FTP.
"""

from PyQt4.QtNetwork import QNetworkAccessManager

from .SchemeAccessHandler import SchemeAccessHandler
from .FtpReply import FtpReply


class FtpAccessHandler(SchemeAccessHandler):
    """
    Class implementing a scheme access handler for FTP.
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
        if op == QNetworkAccessManager.GetOperation:
            return FtpReply(request.url(), self.parent())
        else:
            return None
