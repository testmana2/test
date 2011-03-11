# -*- coding: utf-8 -*-

# Copyright (c) 2010 - 2011 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the client of the cooperation package.
"""

import collections

from PyQt4.QtCore import QObject, pyqtSignal, QProcess, QRegExp
from PyQt4.QtNetwork import QHostInfo, QHostAddress, QAbstractSocket

from .CooperationServer import CooperationServer
from .Connection import Connection

import Preferences


class CooperationClient(QObject):
    """
    Class implementing the client of the cooperation package.
    
    @signal newMessage(user, message) emitted after a new message has
            arrived (string, string)
    @signal newParticipant(nickname) emitted after a new participant joined (string)
    @signal participantLeft(nickname) emitted after a participant left (string)
    @signal connectionError(message) emitted when a connection error occurs (string)
    @signal cannotConnect() emitted, if the initial connection fails
    @signal editorCommand(hash, filename, message) emitted when an editor command
            has been received (string, string, string)
    """
    newMessage = pyqtSignal(str, str)
    newParticipant = pyqtSignal(str)
    participantLeft = pyqtSignal(str)
    connectionError = pyqtSignal(str)
    cannotConnect = pyqtSignal()
    editorCommand = pyqtSignal(str, str, str)
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        QObject.__init__(self, parent)
        
        self.__server = CooperationServer(self)
        self.__peers = collections.defaultdict(list)
        
        self.__initialConnection = None
        
        envVariables = ["USERNAME.*", "USER.*", "USERDOMAIN.*",
                        "HOSTNAME.*", "DOMAINNAME.*"]
        environment = QProcess.systemEnvironment()
        found = False
        for envVariable in envVariables:
            for env in environment:
                if QRegExp(envVariable).exactMatch(env):
                    envList = env.split("=")
                    if len(envList) == 2:
                        self.__username = envList[1].strip()
                        found = True
                        break
            
            if found:
                break
        
        if self.__username == "":
            self.__username = self.trUtf8("unknown")
        
        self.__server.newConnection.connect(self.__newConnection)
    
    def server(self):
        """
        Public method to get a reference to the server.
        
        @return reference to the server object (CooperationServer)
        """
        return self.__server
    
    def sendMessage(self, message):
        """
        Public method to send a message.
        
        @param message message to be sent (string)
        """
        if message == "":
            return
        
        for connectionList in self.__peers.values():
            for connection in connectionList:
                connection.sendMessage(message)
    
    def nickName(self):
        """
        Public method to get the nick name.
        
        @return nick name (string)
        """
        return "{0}@{1}:{2}".format(
            self.__username,
            QHostInfo.localHostName(),
            self.__server.serverPort()
        )
    
    def hasConnection(self, senderIp, senderPort=-1):
        """
        Public method to check for an existing connection.
        
        @param senderIp address of the sender (QHostAddress)
        @param senderPort port of the sender (integer)
        @return flag indicating an existing connection (boolean)
        """
        if senderPort == -1:
            return senderIp in self.__peers
        
        if senderIp not in self.__peers:
            return False
        
        for connection in self.__peers[senderIp]:
            if connection.peerPort() == senderPort:
                return True
        
        return False
    
    def hasConnections(self):
        """
        Public method to check, if there are any connections established.
        
        @return flag indicating the presence of connections (boolean)
        """
        for connectionList in self.__peers.values():
            if connectionList:
                return True
        
        return False
    
    def removeConnection(self, connection):
        """
        Public method to remove a connection.
        
        @param connection reference to the connection to be removed (Connection)
        """
        if connection.peerAddress() in self.__peers and \
           connection in self.__peers[connection.peerAddress()]:
            self.__peers[connection.peerAddress()].remove(connection)
            nick = connection.name()
            if nick != "":
                self.participantLeft.emit(nick)
        
        if connection.isValid():
            connection.abort()
    
    def disconnectConnections(self):
        """
        Public slot to disconnect from the chat network.
        """
        for connectionList in self.__peers.values():
            while connectionList:
                self.removeConnection(connectionList[0])
    
    def __newConnection(self, connection):
        """
        Private slot to handle a new connection.
        
        @param connection reference to the new connection (Connection)
        """
        connection.setParent(self)
        connection.setGreetingMessage(self.__username,
                                      self.__server.serverPort())
        
        connection.error.connect(self.__connectionError)
        connection.disconnected.connect(self.__disconnected)
        connection.readyForUse.connect(self.__readyForUse)
        connection.rejected.connect(self.__connectionRejected)
    
    def __connectionRejected(self, msg):
        """
        Private slot to handle the rejection of a connection.
        
        @param msg error message (string)
        """
        self.connectionError.emit(msg)
    
    def __connectionError(self, socketError):
        """
        Private slot to handle a connection error.
        
        @param socketError reference to the error object (QAbstractSocket.SocketError)
        """
        connection = self.sender()
        if socketError != QAbstractSocket.RemoteHostClosedError:
            if connection.peerPort() != 0:
                msg = "* {0}:{1}\n{2}\n".format(
                    connection.peerAddress().toString(),
                    connection.peerPort(),
                    connection.errorString()
                )
            else:
                msg = "* {0}\n".format(connection.errorString())
            self.connectionError.emit(msg)
        if connection == self.__initialConnection:
            self.cannotConnect.emit()
        self.removeConnection(connection)
    
    def __disconnected(self):
        """
        Private slot to handle the disconnection of a chat client.
        """
        connection = self.sender()
        self.removeConnection(connection)
    
    def __readyForUse(self):
        """
        Private slot to handle a connection getting ready for use.
        """
        connection = self.sender()
        if self.hasConnection(connection.peerAddress(), connection.peerPort()):
            return
        
        connection.newMessage.connect(self.newMessage)
        connection.getParticipants.connect(self.__getParticipants)
        connection.editorCommand.connect(self.editorCommand)
        
        self.__peers[connection.peerAddress()].append(connection)
        nick = connection.name()
        if nick != "":
            self.newParticipant.emit(nick)
        
        if connection == self.__initialConnection:
            connection.sendGetParticipants()
            self.__initialConnection = None
    
    def connectToHost(self, host, port):
        """
        Public method to connect to a host.
        
        @param host host to connect to (string)
        @param port port to connect to (integer)
        """
        self.__initialConnection = Connection(self)
        self.__newConnection(self.__initialConnection)
        self.__initialConnection.participants.connect(self.__processParticipants)
        self.__initialConnection.connectToHost(host, port)
    
    def __getParticipants(self):
        """
        Private slot to handle the request for a list of participants.
        """
        reqConnection = self.sender()
        participants = []
        for connectionList in self.__peers.values():
            for connection in connectionList:
                if connection != reqConnection:
                    participants.append("{0}:{1}".format(
                        connection.peerAddress().toString(), connection.serverPort()))
        reqConnection.sendParticipants(participants)
    
    def __processParticipants(self, participants):
        """
        Private slot to handle the receipt of a list of participants.
        
        @param participants list of participants (list of strings of "host:port")
        """
        for participant in participants:
            host, port = participant.split(":")
            port = int(port)
            
            if port == 0:
                msg = self.trUtf8("Illegal address: {0}:{1}\n").format(host, port)
                self.connectionError.emit(msg)
            else:
                if not self.hasConnection(QHostAddress(host), port):
                    connection = Connection(self)
                    self.__newConnection(connection)
                    connection.connectToHost(host, port)
    
    def sendEditorCommand(self, projectHash, filename, message):
        """
        Public method to send an editor command.
        
        @param projectHash hash of the project (string)
        @param filename project relative universal file name of
            the sending editor (string)
        @param message editor command to be sent (string)
        """
        for connectionList in self.__peers.values():
            for connection in connectionList:
                connection.sendEditorCommand(projectHash, filename, message)
    
    def __findConnections(self, nick):
        """
        Public method to get a list of connection given a nick name.
        
        @param nick nick name in the format of self.nickName() (string)
        @return list of references to the connection objects (list of Connection)
        """
        if "@" not in nick or ":" not in nick:
            # nick given in wrong format
            return []
        
        user, host = nick.split(":")[0].split("@")
        senderIp = QHostAddress(host)
        
        if senderIp not in self.__peers:
            return []
        
        return self.__peers[senderIp][:]
    
    def kickUser(self, nick):
        """
        Public method to kick a user by its nick name.
        
        @param nick nick name in the format of self.nickName() (string)
        """
        for connection in self.__findConnections(nick):
            connection.abort()
    
    def banUser(self, nick):
        """
        Public method to ban a user by its nick name.
        
        @param nick nick name in the format of self.nickName() (string)
        """
        Preferences.syncPreferences()
        user = nick.split(":")[0]
        bannedUsers = Preferences.getCooperation("BannedUsers")[:]
        if user not in bannedUsers:
            bannedUsers.append(user)
            Preferences.setCooperation("BannedUsers", bannedUsers)
    
    def banKickUser(self, nick):
        """
        Public method to ban and kick a user by its nick name.
        
        @param nick nick name in the format of self.nickName() (string)
        """
        self.banUser(nick)
        self.kickUser(nick)
