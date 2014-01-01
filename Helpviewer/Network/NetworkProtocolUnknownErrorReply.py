# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a QNetworkReply subclass reporting an unknown protocol error.
"""

from PyQt4.QtCore import QTimer
from PyQt4.QtNetwork import QNetworkReply


class NetworkProtocolUnknownErrorReply(QNetworkReply):
    """
    Class implementing a QNetworkReply subclass reporting an unknown protocol error.
    """
    def __init__(self, protocol, parent=None):
        """
        Constructor
        
        @param protocol protocol name (string)
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        self.setError(QNetworkReply.ProtocolUnknownError,
                      self.trUtf8("Protocol '{0}' not supported.").format(protocol))
        QTimer.singleShot(0, self.__fireSignals)
    
    def __fireSignals(self):
        """
        Private method to send some signals to end the connection.
        """
        self.error.emit(QNetworkReply.ProtocolUnknownError)
        self.finished[()].emit()
    
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
        return 0
