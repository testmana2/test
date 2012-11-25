# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the network part of the IRC widget.
"""

from PyQt4.QtCore import pyqtSlot, pyqtSignal
from PyQt4.QtGui import QWidget

from .Ui_IrcNetworkWidget import Ui_IrcNetworkWidget

from .IrcUtilities import ircFilter, ircTimestamp

import UI.PixmapCache
import Preferences


class IrcNetworkWidget(QWidget, Ui_IrcNetworkWidget):
    """
    Class implementing the network part of the IRC widget.
    
    @signal connectNetwork(str,bool) emitted to connect or disconnect from a network
    @signal editNetwork(str) emitted to edit a network configuration
    @signal joinChannel(str) emitted to join a channel
    @signal nickChanged(str) emitted to change the nick name
    """
    connectNetwork = pyqtSignal(str, bool)
    editNetwork = pyqtSignal(str)
    joinChannel = pyqtSignal(str)
    nickChanged = pyqtSignal(str)
    
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.connectButton.setIcon(UI.PixmapCache.getIcon("ircConnect.png"))
        self.editButton.setIcon(UI.PixmapCache.getIcon("ircConfigure.png"))
        self.joinButton.setIcon(UI.PixmapCache.getIcon("ircJoinChannel.png"))
        
        self.__manager = None
        self.__connected = False
    
    def initialize(self, manager):
        """
        Public method to initialize the widget.
        
        @param manager reference to the network manager (IrcNetworkManager)
        """
        self.__manager = manager
        
        self.networkCombo.addItems(self.__manager.getNetworkNames())
    
    @pyqtSlot()
    def on_connectButton_clicked(self):
        """
        Private slot to connect to a network.
        """
        network = self.networkCombo.currentText()
        self.connectNetwork.emit(network, not self.__connected)
    
    @pyqtSlot()
    def on_editButton_clicked(self):
        """
        Private slot to edit a network.
        """
        network = self.networkCombo.currentText()
        self.editNetwork.emit(network)
    
    @pyqtSlot(str)
    def on_channelCombo_editTextChanged(self, txt):
        """
        Private slot to react upon changes of the channel.
        
        @param txt current text of the channel combo (string)
        """
        on = bool(txt)
        self.joinButton.setEnabled(on)
    
    @pyqtSlot()
    def on_joinButton_clicked(self):
        """
        Private slot to join a channel.
        """
        channel = self.channelCombo.currentText()
        self.joinChannel.emit(channel)
    
    @pyqtSlot(str)
    def on_networkCombo_currentIndexChanged(self, networkName):
        """
        Private slot to handle selections of a network.
        
        @param networkName selected network name (string)
        """
        network = self.__manager.getNetwork(networkName)
        self.channelCombo.clear()
        if network:
            channels = network.getChannels()
            self.channelCombo.addItems(channels)
            self.channelCombo.setEnabled(True)
            identity = self.__manager.getIdentity(
                network.getIdentityName())
            if identity:
                self.nickCombo.addItems(identity.getNickNames())
        else:
            self.channelCombo.setEnabled(False)
    
    @pyqtSlot(str)
    def on_nickCombo_activated(self, nick):
        """
        Private slot to use another nick name.
        
        @param nick nick name to use (string)
        """
        if self.__connected:
            self.nickChanged.emit(self.nickCombo.currentText())
    
    def getNickname(self):
        """
        Public method to get the currently selected nick name.
        
        @return selected nick name (string)
        """
        return self.nickCombo.currentText()
    
    def setNickName(self, nick):
        """
        Public slot to set the nick name in use.
        
        @param nick nick name in use (string)
        """
        self.nickCombo.blockSignals(True)
        self.nickCombo.setEditText(nick)
        self.nickCombo.blockSignals(False)
    
    def addMessage(self, msg):
        """
        Public method to add a message.
        
        @param msg message to be added (string)
        """
        s = '<font color="{0}">{1} {2}</font>'.format(
            Preferences.getIrc("NetworkMessageColour"),
            ircTimestamp(),
            msg
        )
        self.messages.append(s)
    
    def addServerMessage(self, msgType, msg, filterMsg=True):
        """
        Public method to add a server message.
        
        @param msgType txpe of the message (string)
        @param msg message to be added (string)
        @keyparam filterMsg flag indicating to filter the message (boolean)
        """
        if filterMsg:
            msg = ircFilter(msg)
        s = '<font color="{0}">{1} <b>[</b>{2}<b>]</b> {3}</font>'.format(
            Preferences.getIrc("ServerMessageColour"),
            ircTimestamp(),
            msgType,
            msg
        )
        self.messages.append(s)
    
    def addErrorMessage(self, msgType, msg):
        """
        Public method to add an error message.
        
        @param msgType txpe of the message (string)
        @param msg message to be added (string)
        """
        s = '<font color="{0}">{1} <b>[</b>{2}<b>]</b> {3}</font>'.format(
            Preferences.getIrc("ErrorMessageColour"),
            ircTimestamp(),
            msgType,
            msg
        )
        self.messages.append(s)
    
    def setConnected(self, connected):
        """
        Public slot to set the connection state.
        
        @param connected flag indicating the connection state (boolean)
        """
        self.__connected = connected
        if self.__connected:
            self.connectButton.setIcon(UI.PixmapCache.getIcon("ircDisconnect.png"))
        else:
            self.connectButton.setIcon(UI.PixmapCache.getIcon("ircConnect.png"))
