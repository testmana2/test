# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the chat dialog.
"""

from PyQt4.QtCore import Qt, pyqtSlot, QDateTime
from PyQt4.QtGui import QWidget, QColor, QListWidgetItem

from .CooperationClient import CooperationClient

from .Ui_ChatWidget import Ui_ChatWidget

import Preferences
import UI.PixmapCache

class ChatWidget(QWidget, Ui_ChatWidget):
    """
    Class implementing the chat dialog.
    """
    def __init__(self, port = -1, parent = None):
        """
        Constructor
        
        @param port port to be used for the cooperation server (integer)
        @param parent reference to the parent widget (QWidget)
        """
        QWidget.__init__(self, parent)
        self.setupUi(self)
        
        self.__client = CooperationClient()
        self.__myNickName = self.__client.nickName()
        
        self.messageEdit.returnPressed.connect(self.__handleMessage)
        self.sendButton.clicked.connect(self.__handleMessage)
        self.__client.newMessage.connect(self.appendMessage)
        self.__client.newParticipant.connect(self.__newParticipant)
        self.__client.participantLeft.connect(self.__participantLeft)
        self.__client.connectionError.connect(self.__showErrorMessage)
        self.__client.cannotConnect.connect(self.__initialConnectionRefused)
        
        self.serverButton.setText(self.trUtf8("Start Server"))
        self.serverLed.setColor(QColor(Qt.red))
        if port == -1:
            port = Preferences.getCooperation("ServerPort")
        
        self.portSpin.setValue(port)
        self.serverPortSpin.setValue(port)
        
        self.__setConnected(False)
        
        if Preferences.getCooperation("AutoStartServer"):
            self.on_serverButton_clicked()
    
    def __handleMessage(self):
        """
        Private slot handling the Return key pressed in the message edit.
        """
        text = self.messageEdit.text()
        if text == "":
            return
        
        if text.startswith("/"):
            self.__showErrorMessage(
                self.trUtf8("! Unknown command: {0}\n").format(text.split()[0]))
        else:
            self.__client.sendMessage(text)
            self.appendMessage(self.__myNickName, text)
        
        self.messageEdit.clear()
    
    def __newParticipant(self, nick):
        """
        Private slot handling a new participant joining.
        
        @param nick nick name of the new participant (string)
        """
        if nick == "":
            return
        
        color = self.chatEdit.textColor()
        self.chatEdit.setTextColor(Qt.gray)
        self.chatEdit.append(
            QDateTime.currentDateTime().toString(Qt.SystemLocaleLongDate) + ":")
        self.chatEdit.append(self.trUtf8("* {0} has joined.\n").format(nick))
        self.chatEdit.setTextColor(color)
        
        QListWidgetItem(
            UI.PixmapCache.getIcon(
                "chatUser{0}.png".format(1 + self.usersList.count() % 6)), 
            nick, self.usersList)
        
        if not self.__connected:
            self.__setConnected(True)
    
    def __participantLeft(self, nick):
        """
        Private slot handling a participant leaving the session.
        
        @param nick nick name of the participant (string)
        """
        if nick == "":
            return
        
        items = self.usersList.findItems(nick, Qt.MatchExactly)
        for item in items:
            self.usersList.takeItem(self.usersList.row(item))
            del item
            
            color = self.chatEdit.textColor()
            self.chatEdit.setTextColor(Qt.gray)
            self.chatEdit.append(
                QDateTime.currentDateTime().toString(Qt.SystemLocaleLongDate) + ":")
            self.chatEdit.append(self.trUtf8("* {0} has left.\n").format(nick))
            self.chatEdit.setTextColor(color)
        
        if not self.__client.hasConnections():
            self.__setConnected(False)
    
    def appendMessage(self, from_, message):
        """
        Public slot to append a message to the display.
        
        @param from_ originator of the message (string)
        @param message message to be appended (string)
        """
        if from_ == "" or message == "":
            return
        
        self.chatEdit.append(
            QDateTime.currentDateTime().toString(Qt.SystemLocaleLongDate) + \
            " <" + from_ + ">:")
        self.chatEdit.append(message + "\n")
        bar = self.chatEdit.verticalScrollBar()
        bar.setValue(bar.maximum())
    
    @pyqtSlot(str)
    def on_hostEdit_textChanged(self, host):
        """
        Private slot handling the entry of a host to connect to.
        
        @param host host to connect to (string)
        """
        if not self.__connected:
            self.connectButton.setEnabled(host != "")
    
    @pyqtSlot()
    def on_connectButton_clicked(self):
        """
        Private slot initiating the connection.
        """
        if not self.__connected:
            if not self.__client.server().isListening():
                self.on_serverButton_clicked()
            if self.__client.server().isListening():
                self.__client.connectToHost(self.hostEdit.text(), self.portSpin.value())
                self.__setConnected(True)
        else:
            self.__client.disconnectConnections()
            self.__setConnected(False)
    
    @pyqtSlot()
    def on_serverButton_clicked(self):
        """
        Private slot to start the server.
        """
        if self.__client.server().isListening():
            self.__client.server().close()
            self.serverButton.setText(self.trUtf8("Start Server"))
            self.serverPortSpin.setEnabled(True)
            if self.serverPortSpin.value() != Preferences.getCooperation("ServerPort"):
                self.serverPortSpin.setValue(Preferences.getCooperation("ServerPort"))
            self.serverLed.setColor(QColor(Qt.red))
        else:
            res, port = self.__client.server().startListening(self.serverPortSpin.value())
            if res:
                self.serverButton.setText(self.trUtf8("Stop Server"))
                self.serverPortSpin.setValue(port)
                self.serverPortSpin.setEnabled(False)
                self.serverLed.setColor(QColor(Qt.green))
            else:
                self.__showErrorMessage(
                    self.trUtf8("! Server Error: {0}\n").format(
                    self.__client.server().errorString())
                )
    
    def __setConnected(self, connected):
        """
        Private slot to set the connected state.
        
        @param connected new connected state (boolean)
        """
        if connected:
            self.__connected = True
            self.connectButton.setText(self.trUtf8("Disconnect"))
            self.connectButton.setEnabled(True)
            self.hostEdit.setEnabled(False)
            self.portSpin.setEnabled(False)
            self.connectionLed.setColor(QColor(Qt.green))
            self.serverButton.setEnabled(False)
        else:
            self.__connected = False
            self.connectButton.setText(self.trUtf8("Connect"))
            self.connectButton.setEnabled(self.hostEdit.text() != "")
            self.hostEdit.setEnabled(True)
            self.portSpin.setEnabled(True)
            self.connectionLed.setColor(QColor(Qt.red))
            self.serverButton.setEnabled(True)
    
    def __showErrorMessage(self, message):
        """
        Private slot to show an error message.
        
        @param message error message to show (string)
        """
        color = self.chatEdit.textColor()
        self.chatEdit.setTextColor(Qt.red)
        self.chatEdit.append(
            QDateTime.currentDateTime().toString(Qt.SystemLocaleLongDate) + ":")
        self.chatEdit.append(message)
        self.chatEdit.setTextColor(color)
    
    def __initialConnectionRefused(self):
        """
        Private slot to handle the refusal of the initial connection.
        """
        self.__setConnected(False)
    
    def preferencesChanged(self):
        """
        Public slot to handle a change of preferences.
        """
        if not self.__client.server().isListening():
            self.serverPortSpin.setValue(Preferences.getCooperation("ServerPort"))
            if Preferences.getCooperation("AutoStartServer"):
                self.on_serverButton_clicked()
