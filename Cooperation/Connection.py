# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class representing a peer connection.
"""

from PyQt4.QtCore import pyqtSignal, QTimer, QTime, QByteArray
from PyQt4.QtNetwork import QTcpSocket

MaxBufferSize   = 1024 * 1024
TransferTimeout =   30 * 1000
PongTimeout     =   60 * 1000
PingInterval    =    5 * 1000
SeparatorToken  = '|||'


class Connection(QTcpSocket):
    """
    Class representing a peer connection.
    
    @signal readyForUse() emitted when the connection is ready for use
    @signal newMessage(user, message) emitted after a new message has 
            arrived (string, string)
    @signal getParticipants() emitted after a get participants message has arrived
    @signal participants(participants) emitted after the list of participants has
            arrived (list of strings of "host:port")
    """
    WaitingForGreeting  = 0
    ReadingGreeting     = 1
    ReadyForUse         = 2
    
    PlainText       = 0
    Ping            = 1
    Pong            = 2
    Greeting        = 3
    GetParticipants = 4
    Participants    = 5
    Undefined       = 99
    
    ProtocolMessage         = "MESSAGE"
    ProtocolPing            = "PING"
    ProtocolPong            = "PONG"
    ProtocolGreeting        = "GREETING"
    ProtocolGetParticipants = "GET_PARTICIPANTS"
    ProtocolParticipants    = "PARTICIPANTS"
    
    readyForUse     = pyqtSignal()
    newMessage      = pyqtSignal(str, str)
    getParticipants = pyqtSignal()
    participants    = pyqtSignal(list)
    
    def __init__(self, parent = None):
        """
        Constructor
        
        @param parent referenec to the parent object (QObject)
        """
        QTcpSocket.__init__(self, parent)
        
        self.__greetingMessage = self.trUtf8("undefined")
        self.__username = self.trUtf8("unknown")
        self.__serverPort = 0
        self.__state = Connection.WaitingForGreeting
        self.__currentDataType = Connection.Undefined
        self.__numBytesForCurrentDataType = -1
        self.__transferTimerId = 0
        self.__isGreetingMessageSent = False
        self.__pingTimer = QTimer()
        self.__pingTimer.setInterval(PingInterval)
        self.__pongTime = QTime()
        self.__buffer = QByteArray()
        
        self.readyRead.connect(self.__processReadyRead)
        self.disconnected.connect(self.__pingTimer.stop)
        self.__pingTimer.timeout.connect(self.__sendPing)
        self.connected.connect(self.__sendGreetingMessage)
    
    def name(self):
        """
        Public method to get the connection name.
        
        @return connection name (string)
        """
        return self.__username
    
    def serverPort(self):
        """
        Public method to get the server port.
        
        @return server port (integer)
        """
        return self.__serverPort
    
    def setGreetingMessage(self, message, serverPort):
        """
        Public method to set the greeting message.
        
        @param message greeting message (string)
        """
        self.__greetingMessage = "{0}:{1}".format(message, serverPort)
    
    def sendMessage(self, message):
        """
        Public method to send a message.
        
        @param message message to be sent (string)
        @return flag indicating a successful send (boolean)
        """
        if message == "":
            return False
        
        msg = QByteArray(message.encode("utf-8"))
        data = QByteArray("{0}{1}{2}{1}".format(
            Connection.ProtocolMessage, SeparatorToken, msg.size())) + msg
        return self.write(data) == data.size()
    
    def timerEvent(self, evt):
        """
        Protected method to handle timer events.
        
        @param evt reference to the timer event (QTimerEvent)
        """
        if evt.timerId() == self.__transferTimerId:
            self.abort()
            self.killTimer(self.__transferTimerId)
            self.__transferTimerId = 0
    
    def __processReadyRead(self):
        """
        Private slot to handle the readyRead signal.
        """
        if self.__state == Connection.WaitingForGreeting:
            if not self.__readProtocolHeader():
                return
            if self.__currentDataType != Connection.Greeting:
                self.abort()
                return
            self.__state = Connection.ReadingGreeting
        
        if self.__state == Connection.ReadingGreeting:
            if not self.__hasEnoughData():
                return
            
            self.__buffer = QByteArray(self.read(self.__numBytesForCurrentDataType))
            if self.__buffer.size() != self.__numBytesForCurrentDataType:
                self.abort()
                return
            
            user, serverPort = str(self.__buffer, encoding = "utf-8").split(":")
            self.__serverPort = int(serverPort)
            self.__username = "{0}@{1}:{2}".format(
                user, 
                self.peerAddress().toString(), 
                self.peerPort()
            )
            self.__currentDataType = Connection.Undefined
            self.__numBytesForCurrentDataType = 0
            self.__buffer.clear()
            
            if not self.isValid():
                self.abort()
                return
            
            if not self.__isGreetingMessageSent:
                self.__sendGreetingMessage()
            
            self.__pingTimer.start()
            self.__pongTime.start()
            self.__state = Connection.ReadyForUse
            self.readyForUse.emit()
        
        while self.bytesAvailable():
            if self.__currentDataType == Connection.Undefined:
                if not self.__readProtocolHeader():
                    return
            
            if not self.__hasEnoughData():
                return
            
            self.__processData()
    
    def __sendPing(self):
        """
        Private slot to send a ping message.
        """
        if self.__pongTime.elapsed() > PongTimeout:
            self.abort()
            return
        
        self.write("{0}{1}1{1}p".format(Connection.ProtocolPing, SeparatorToken))
    
    def __sendGreetingMessage(self):
        """
        Private slot to send a greeting message.
        """
        greeting = QByteArray(self.__greetingMessage.encode("utf-8"))
        data = QByteArray("{0}{1}{2}{1}".format(
            Connection.ProtocolGreeting, SeparatorToken, greeting.size())) + greeting
        if self.write(data) == data.size():
            self.__isGreetingMessageSent = True
    
    def __readDataIntoBuffer(self, maxSize = MaxBufferSize):
        """
        Private method to read some data into the buffer.
        
        @param maxSize maximum size of data to read (integer)
        @return size of data read (integer)
        """
        if maxSize > MaxBufferSize:
            return 0
        
        numBytesBeforeRead = self.__buffer.size()
        if numBytesBeforeRead == MaxBufferSize:
            self.abort()
            return 0
        
        while self.bytesAvailable() and self.__buffer.size() < maxSize:
            self.__buffer.append(self.read(1))
            if self.__buffer.endsWith(SeparatorToken):
                break
        
        return self.__buffer.size() - numBytesBeforeRead
    
    def __dataLengthForCurrentDataType(self):
        """
        Private method to get the data length for the current data type.
        
        @return data length (integer)
        """
        if self.bytesAvailable() <= 0 or \
           self.__readDataIntoBuffer() <= 0 or \
           not self.__buffer.endsWith(SeparatorToken):
            return 0
        
        self.__buffer.chop(len(SeparatorToken))
        number = self.__buffer.toInt()[0]
        self.__buffer.clear()
        return number
    
    def __readProtocolHeader(self):
        """
        Private method to read the protocol header.
        
        @return flag indicating a successful read (boolean)
        """
        if self.__transferTimerId:
            self.killTimer(self.__transferTimerId)
            self.__transferTimerId = 0
        
        if self.__readDataIntoBuffer() <= 0:
            self.__transferTimerId = self.startTimer(TransferTimeout)
            return False
        
        self.__buffer.chop(len(SeparatorToken))
        if self.__buffer == Connection.ProtocolPing:
            self.__currentDataType = Connection.Ping
        elif self.__buffer == Connection.ProtocolPong:
            self.__currentDataType = Connection.Pong
        elif self.__buffer == Connection.ProtocolMessage:
            self.__currentDataType = Connection.PlainText
        elif self.__buffer == Connection.ProtocolGreeting:
            self.__currentDataType = Connection.Greeting
        elif self.__buffer == Connection.ProtocolGetParticipants:
            self.__currentDataType = Connection.GetParticipants
        elif self.__buffer == Connection.ProtocolParticipants:
            self.__currentDataType = Connection.Participants
        else:
            self.__currentDataType = Connection.Undefined
            self.abort()
            return False
        
        self.__buffer.clear()
        self.__numBytesForCurrentDataType = self.__dataLengthForCurrentDataType()
        return True
    
    def __hasEnoughData(self):
        """
        Private method to check, if enough data is available.
        
        @return flag indicating availability of enough data (boolean)
        """
        if self.__transferTimerId:
            self.killTimer(self.__transferTimerId)
            self.__transferTimerId = 0
        
        if self.__numBytesForCurrentDataType <= 0:
            self.__numBytesForCurrentDataType = self.__dataLengthForCurrentDataType()
        
        if self.bytesAvailable() < self.__numBytesForCurrentDataType or \
           self.__numBytesForCurrentDataType <= 0:
            self.__transferTimerId = self.startTimer(TransferTimeout)
            return False
        
        return True
    
    def __processData(self):
        """
        Private method to process the received data.
        """
        self.__buffer = QByteArray(self.read(self.__numBytesForCurrentDataType))
        if self.__buffer.size() != self.__numBytesForCurrentDataType:
            self.abort()
            return
        
        if self.__currentDataType == Connection.PlainText:
            self.newMessage.emit(self.__username, str(self.__buffer, encoding = "utf-8"))
        elif self.__currentDataType == Connection.Ping:
            self.write("{0}{1}1{1}p".format(Connection.ProtocolPong, SeparatorToken))
        elif self.__currentDataType == Connection.Pong:
            self.__pongTime.restart()
        elif self.__currentDataType == Connection.GetParticipants:
            self.getParticipants.emit()
        elif self.__currentDataType == Connection.Participants:
            msg = str(self.__buffer, encoding = "utf-8")
            if msg == "<empty>":
                participantsList = []
            else:
                participantsList = msg.split(SeparatorToken)
            self.participants.emit(participantsList[:])
        
        self.__currentDataType = Connection.Undefined
        self.__numBytesForCurrentDataType = 0
        self.__buffer.clear()
    
    def sendGetParticipants(self):
        """
        Public method to request a list of participants.
        """
        self.write(
            "{0}{1}1{1}l".format(Connection.ProtocolGetParticipants, SeparatorToken)
        )
    
    def sendParticipants(self, participants):
        """
        Public method to send the list of participants.
        
        @param participants list of participants (list of strings of "host:port")
        """
        if participants:
            message = SeparatorToken.join(participants)
        else:
            message = "<empty>"
        msg = QByteArray(message.encode("utf-8"))
        data = QByteArray("{0}{1}{2}{1}".format(
            Connection.ProtocolParticipants, SeparatorToken, msg.size())) + msg
        self.write(data)
