# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a network reply class for an empty reply
(i.e. request was handle other way).
"""

from PyQt4.QtCore import QTimer
from PyQt4.QtNetwork import QNetworkReply, QNetworkAccessManager


class EmptyNetworkReply(QNetworkReply):
    """
    Class implementing an empty network reply.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.setOperation(QNetworkAccessManager.GetOperation)
        self.setError(QNetworkReply.OperationCanceledError, "eric5:No Error")
        
        QTimer.singleShot(0, lambda: self.finished.emit())
    
    def abort(self):
        """
        Public slot to abort the operation.
        """
        # do nothing
        pass
    
    def readData(self, maxlen):
        """
        Protected method to retrieve data from the reply object.
        
        @param maxlen maximum number of bytes to read (integer)
        @return string containing the data (bytes)
        """
        return bytes()
