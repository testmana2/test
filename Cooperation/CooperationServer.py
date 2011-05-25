# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the cooperation server.
"""

from PyQt4.QtCore import pyqtSignal
from PyQt4.QtNetwork import QTcpServer, QHostAddress

from .Connection import Connection

import Preferences


class CooperationServer(QTcpServer):
    """
    Class implementing the cooperation server.
    
    @signal newConnection(connection) emitted after a new connection was received
            (Connection)
    """
    newConnection = pyqtSignal(Connection)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        QTcpServer.__init__(self, parent)
    
    def incomingConnection(self, socketDescriptor):
        """
        Protected method handling an incoming connection.
        
        @param socketDescriptor native socket descriptor (integer)
        """
        connection = Connection(self)
        connection.setSocketDescriptor(socketDescriptor)
        self.newConnection.emit(connection)
    
    def startListening(self, port=-1):
        """
        Public method to start listening for new connections.
        
        @param port port to listen on (integer)
        @return tuple giving a flag indicating success (boolean) and
            the port the server listens on
        """
        res = self.listen(QHostAddress.Any, port)
        if Preferences.getCooperation("TryOtherPorts"):
            endPort = port + Preferences.getCooperation("MaxPortsToTry")
            while not res and port < endPort:
                port += 1
                res = self.listen(QHostAddress.Any, port)
        return res, port
