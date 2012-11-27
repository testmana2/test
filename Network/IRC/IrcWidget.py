# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the IRC window.
"""

import re
import logging

from PyQt4.QtCore import pyqtSlot, Qt, QByteArray
from PyQt4.QtGui import QWidget, QToolButton, QLabel
from PyQt4.QtNetwork import QTcpSocket, QAbstractSocket

from E5Gui import E5MessageBox

from .Ui_IrcWidget import Ui_IrcWidget

from .IrcNetworkManager import IrcNetworkManager
from .IrcChannelWidget import IrcChannelWidget
from .IrcNetworkListDialog import IrcNetworkListDialog

import Preferences
import UI.PixmapCache


class IrcWidget(QWidget, Ui_IrcWidget):
    """
    Class implementing the IRC window.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.__ircNetworkManager = IrcNetworkManager(self)
        
        self.__leaveButton = QToolButton(self)
        self.__leaveButton.setIcon(UI.PixmapCache.getIcon("ircCloseChannel.png"))
        self.__leaveButton.setToolTip(self.trUtf8("Press to leave the current channel"))
        self.__leaveButton.clicked[()].connect(self.__leaveChannel)
        self.__leaveButton.setEnabled(False)
        self.channelsWidget.setCornerWidget(self.__leaveButton, Qt.BottomRightCorner)
        self.channelsWidget.setTabsClosable(False)
        
        self.networkWidget.initialize(self.__ircNetworkManager)
        self.networkWidget.connectNetwork.connect(self.__connectNetwork)
        self.networkWidget.editNetwork.connect(self.__editNetwork)
        self.networkWidget.joinChannel.connect(self.__joinChannel)
        self.networkWidget.nickChanged.connect(self.__changeNick)
        
        self.__channelList = []
        self.__channelTypePrefixes = ""
        self.__userName = ""
        self.__nickIndex = -1
        self.__nickName = ""
        self.__server = None
        self.__registering = False
        
        self.__buffer = ""
        self.__userPrefix = {}
        
        # create TCP socket
        self.__socket = QTcpSocket(self)
        self.__socket.hostFound.connect(self.__hostFound)
        self.__socket.connected.connect(self.__hostConnected)
        self.__socket.disconnected.connect(self.__hostDisconnected)
        self.__socket.readyRead.connect(self.__readyRead)
        self.__socket.error.connect(self.__tcpError)
        
        self.__patterns = [
            # :foo.bar.net COMMAND some message
            (re.compile(r""":([^ ]+)\s+([A-Z]+)\s+(.+)"""), self.__handleNamedMessage),
            # :foo.bar.net 123 * :info
            (re.compile(r""":([^ ]+)\s+(\d{3})\s+(.+)"""), self.__handleNumericMessage),
            # PING :ping message
            (re.compile(r"""PING\s+:(.*)"""), self.__ping),
        ]
        self.__prefixRe = re.compile(r""".*\sPREFIX=\((.*)\)([^ ]+).*""")
        self.__chanTypesRe = re.compile(r""".*\sCHANTYPES=([^ ]+).*""")
        
        ircPic = UI.PixmapCache.getPixmap("irc128.png")
        self.__emptyLabel = QLabel()
        self.__emptyLabel.setPixmap(ircPic)
        self.__emptyLabel.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.channelsWidget.addTab(self.__emptyLabel, "")
        
    
    def shutdown(self):
        """
        Public method to shut down the widget.
        
        @return flag indicating successful shutdown (boolean)
        """
        if self.__server:
            ok = E5MessageBox.yesNo(self,
                self.trUtf8("Disconnect from Server"),
                self.trUtf8("""<p>Do you really want to disconnect from"""
                            """ <b>{0}</b>?</p><p>All channels will be closed.</p>""")\
                    .format(self.__server.getServer()))
            if ok:
                self.__socket.blockSignals(True)
                
                self.__send("QUIT :" + self.trUtf8("IRC for eric IDE"))
                self.__socket.close()
                self.__socket.deleteLater()
        else:
            ok = True
        
        if ok:
            self.__ircNetworkManager.close()
        return ok
    
    def __connectNetwork(self, name, connect):
        """
        Private slot to connect to or disconnect from the given network.
        
        @param name name of the network to connect to (string)
        @param connect flag indicating to connect (boolean)
        """
        if connect:
            network = self.__ircNetworkManager.getNetwork(name)
            if network:
                self.__server = self.__ircNetworkManager.getServer(
                    network.getServerName())
                self.__userName = network.getIdentityName()
                if self.__server:
                    self.networkWidget.addServerMessage(self.trUtf8("Info"),
                        self.trUtf8("Looking for server {0} (port {1})...").format(
                            self.__server.getServer(), self.__server.getPort()))
                    self.__socket.connectToHost(self.__server.getServer(),
                                                self.__server.getPort())
        else:
            ok = E5MessageBox.yesNo(self,
                self.trUtf8("Disconnect from Server"),
                self.trUtf8("""<p>Do you really want to disconnect from"""
                            """ <b>{0}</b>?</p><p>All channels will be closed.</p>""")\
                    .format(self.__server.getServer()))
            if ok:
                self.networkWidget.addServerMessage(self.trUtf8("Info"),
                    self.trUtf8("Disconnecting from server {0}...").format(
                        self.__server.getServer()))
                while self.__channelList:
                    channel = self.__channelList.pop()
                    self.channelsWidget.removeTab(self.channelsWidget.indexOf(channel))
                    channel.deleteLater()
                    channel = None
                self.__send("QUIT :" + self.trUtf8("IRC for eric IDE"))
                self.__socket.close()
    
    def __editNetwork(self, name):
        """
        Private slot to edit the network configuration.
        
        @param name name of the network to edit (string)
        """
        # TODO: implement this
        dlg = IrcNetworkListDialog(self.__ircNetworkManager, self)
        dlg.exec_()
    
    def __joinChannel(self, name):
        """
        Private slot to join a channel.
        
        @param name name of the channel (string)
        """
        # step 1: check, if this channel is already joined
        for channel in self.__channelList:
            if channel.name() == name:
                return
        
        channel = IrcChannelWidget(self)
        channel.setName(name)
        channel.setUserName(self.__nickName)
        channel.setPartMessage(self.trUtf8("IRC for eric IDE"))
        channel.setUserPrivilegePrefix(self.__userPrefix)
        
        channel.sendData.connect(self.__send)
        channel.channelClosed.connect(self.__closeChannel)
        
        self.channelsWidget.addTab(channel, name)
        self.__channelList.append(channel)
        
        self.__send("JOIN " + name)
        self.__send("MODE " + name)
        
        emptyIndex = self.channelsWidget.indexOf(self.__emptyLabel)
        if emptyIndex > -1:
            self.channelsWidget.removeTab(emptyIndex)
            self.__leaveButton.setEnabled(True)
        self.channelsWidget.setTabsClosable(True)
    
    @pyqtSlot()
    def __leaveChannel(self):
        """
        Private slot to leave a channel and close the associated tab.
        """
        channel = self.channelsWidget.currentWidget()
        channel.requestLeave()
    
    def __closeChannel(self, name):
        """
        Private slot handling the closing of a channel.
        
        @param name name of the closed channel (string) 
        """
        for channel in self.__channelList:
            if channel.name() == name:
                self.channelsWidget.removeTab(self.channelsWidget.indexOf(channel))
                self.__channelList.remove(channel)
                channel.deleteLater()
        
        if self.channelsWidget.count() == 0:
            self.channelsWidget.addTab(self.__emptyLabel, "")
            self.__leaveButton.setEnabled(False)
            self.channelsWidget.setTabsClosable(False)
    
    @pyqtSlot(int)
    def on_channelsWidget_tabCloseRequested(self, index):
        """
        Private slot to close a channel by pressing the close button of
        the channels widget.
        
        @param index index of the tab to be closed (integer)
        """
        channel = self.channelsWidget.widget(index)
        channel.requestLeave()
    
    def __send(self, data):
        """
        Private slot to send data to the IRC server.
        
        @param data data to be sent (string)
        """
        self.__socket.write(QByteArray("{0}\r\n".format(data).encode("utf-8")))
    
    def __hostFound(self):
        """
        Private slot to indicate the host was found.
        """
        self.networkWidget.addServerMessage(self.trUtf8("Info"),
            self.trUtf8("Server found,connecting..."))
    
    def __hostConnected(self):
        """
        Private slot to log in to the server after the connection was established.
        """
        self.networkWidget.addServerMessage(self.trUtf8("Info"),
            self.trUtf8("Connected,logging in..."))
        self.networkWidget.setConnected(True)
        
        self.__registering = True
        serverPassword = self.__server.getPassword()
        if serverPassword:
            self.__send("PASS " + serverPassword)
        nick = self.networkWidget.getNickname()
        if not nick:
            self.__nickIndex = 0
            try:
                nick = self.__ircNetworkManager.getIdentity(self.__userName)\
                    .getNickNames()[self.__nickIndex]
            except IndexError:
                nick = ""
        if not nick:
            nick = self.__userName
        self.__nickName = nick
        self.networkWidget.setNickName(nick)
        self.__send("NICK " + nick)
        self.__send("USER " + self.__userName + " 0 * :eric IDE chat")
    
    def __hostDisconnected(self):
        """
        Private slot to indicate the host was disconnected.
        """
        self.networkWidget.addServerMessage(self.trUtf8("Info"),
            self.trUtf8("Server disconnected."))
        self.networkWidget.setConnected(False)
        self.__server = None
        self.__nickName = ""
        self.__nickIndex = -1
        self.__channelTypePrefixes = ""
    
    def __readyRead(self):
        """
        Private slot to read data from the socket.
        """
        self.__buffer += str(self.__socket.readAll(),
                Preferences.getSystem("IOEncoding"),
                'replace')
        if self.__buffer.endswith("\r\n"):
            for line in self.__buffer.splitlines():
                line = line.strip()
                if line:
                    logging.debug("<IRC> " + line)
                    handled = False
                    # step 1: give channels a chance to handle the message
                    for channel in self.__channelList:
                        handled = channel.handleMessage(line)
                        if handled:
                            break
                    else:
                        # step 2: try to process the message ourselves
                        for patternRe, patternFunc in self.__patterns:
                            match = patternRe.match(line)
                            if match is not None:
                                if patternFunc(match):
                                    break
                        else:
                            # Oops, the message wasn't handled
                            self.networkWidget.addErrorMessage(
                                self.trUtf8("Message Error"),
                                self.trUtf8("Unknown message received from server:"
                                            "<br/>{0}").format(line))
            
            self.__updateUsersCount()
            self.__buffer = ""
    
    def __handleNamedMessage(self, match):
        """
        Private method to handle a server message containing a message name.
        
        @param reference to the match object
        @return flag indicating, if the message was handled (boolean)
        """
        name = match.group(2)
        if name == "NOTICE":
            try:
                msg = match.group(3).split(":", 1)[1]
            except IndexError:
                msg = match.group(3)
            if "!" in match.group(1):
                name = match.group(1).split("!", 1)[0]
                msg = "-{0}- {1}".format(name, msg)
            self.networkWidget.addServerMessage(self.trUtf8("Notice"), msg)
            return True
        elif name == "MODE":
            self.__registering = False
            if ":" in match.group(3):
                # :detlev_ MODE detlev_ :+i
                name, modes = match.group(3).split(" :")
                sourceNick = match.group(1)
                if not self.__isChannelName(name):
                    if name == self.__nickName:
                        if sourceNick == self.__nickName:
                            msg = self.trUtf8(
                                "You have set your personal modes to <b>[{0}]</b>")\
                                .format(modes)
                        else:
                            msg = self.trUtf8(
                                "{0} has changed your personal modes to <b>[{1}]</b>")\
                                .format(sourceNick, modes)
                        self.networkWidget.addServerMessage(
                            self.trUtf8("Mode"), msg, filterMsg=False)
                        return True
        elif name == "PART":
            nick = match.group(1).split("!", 1)[0]
            if nick == self.__nickName:
                channel = match.group(3).split(None, 1)[0]
                self.networkWidget.addMessage(
                    self.trUtf8("You have left channel {0}.").format(channel))
                return True
        elif name == "NICK":
            # :foo_!n=foo@foohost.bar.net NICK :newnick
            oldNick = match.group(1).split("!", 1)[0]
            newNick = match.group(3).split(":", 1)[1]
            if oldNick == self.__nickName:
                self.networkWidget.addMessage(
                    self.trUtf8("You are now known as {0}.").format(newNick))
                self.__nickName = newNick
                self.networkWidget.setNickName(newNick)
            else:
                self.networkWidget.addMessage(
                    self.trUtf8("User {0} is now known as {1}.").format(
                    oldNick, newNick))
            return True
        
        return False
    
    def __handleNumericMessage(self, match):
        """
        Private method to handle a server message containing a numeric code.
        
        @param reference to the match object
        @return flag indicating, if the message was handled (boolean)
        """
        code = int(match.group(2))
        if code < 400:
            return self.__handleServerReply(code, match.group(1), match.group(3))
        else:
            return self.__handleServerError(code, match.group(1), match.group(3))
    
    def __handleServerError(self, code, server, message):
        """
        Private slot to handle a server error reply.
        
        @param code numerical code sent by the server (integer)
        @param server name of the server (string)
        @param message message sent by the server (string)
        @return flag indicating, if the message was handled (boolean)
        """
        if code == 433:
            if self.__registering:
                self.__handleNickInUseLogin()
            else:
                self.__handleNickInUse()
        else:
            self.networkWidget.addServerMessage(self.trUtf8("Error"), message)
        
        return True
    
    def __handleServerReply(self, code, server, message):
        """
        Private slot to handle a server reply.
        
        @param code numerical code sent by the server (integer)
        @param server name of the server (string)
        @param message message sent by the server (string)
        @return flag indicating, if the message was handled (boolean)
        """
        # determine message type
        if code in [1, 2, 3, 4]:
            msgType = self.trUtf8("Welcome")
        elif code == 5:
            msgType = self.trUtf8("Support")
        elif code in [250, 251, 252, 253, 254, 255, 265, 266]:
            msgType = self.trUtf8("User")
        elif code in [372, 375, 376]:
            msgType = self.trUtf8("MOTD")
        else:
            msgType = self.trUtf8("Info ({0})").format(code)
        
        # special treatment for some messages
        if code == 375:
            message = self.trUtf8("Message of the day")
        elif code == 376:
            message = self.trUtf8("End of message of the day")
        elif code == 4:
            parts = message.strip().split()
            message = self.trUtf8("Server {0} (Version {1}), User-Modes: {2},"
                " Channel-Modes: {3}").format(parts[1], parts[2], parts[3], parts[4])
        elif code == 265:
            parts = message.strip().split()
            message = self.trUtf8("Current users on {0}: {1}, max. {2}").format(
                server, parts[1], parts[2])
        elif code == 266:
            parts = message.strip().split()
            message = self.trUtf8("Current users on the network: {0}, max. {1}").format(
                parts[1], parts[2])
        else:
            first, message = message.split(None, 1)
            if message.startswith(":"):
                message = message[1:]
            else:
                message = message.replace(":", "", 1)
        
        self.networkWidget.addServerMessage(msgType, message)
        
        if code == 1:
            # register with services after the welcome message
            self.__registerWithServices()
        elif code == 5:
            # extract the user privilege prefixes
            # ... PREFIX=(ov)@+ ...
            m = self.__prefixRe.match(message)
            if m:
                self.__setUserPrivilegePrefix(m.group(1), m.group(2))
            # extract the channel type prefixes
            # ... CHANTYPES=# ...
            m = self.__chanTypesRe.match(message)
            if m:
                self.__setChannelTypePrefixes(m.group(1))
        
        return True
    
    def __registerWithServices(self):
        """
        Private method to register to services.
        """
        identity = self.__ircNetworkManager.getIdentity(self.__userName)
        service = identity.getName()
        password = identity.getPassword()
        if service and password:
            self.__send("PRIVMSG " + service + " :identify " + password)
    
    def __tcpError(self, error):
        """
        Private slot to handle errors reported by the TCP socket.
        
        @param error error code reported by the socket
            (QAbstractSocket.SocketError)
        """
        if error == QAbstractSocket.RemoteHostClosedError:
            # ignore this one, it's a disconnect
            pass
        elif error == QAbstractSocket.HostNotFoundError:
            self.networkWidget.addErrorMessage(self.trUtf8("Socket Error"),
                self.trUtf8("The host was not found. Please check the host name"
                            " and port settings."))
        elif error == QAbstractSocket.ConnectionRefusedError:
            self.networkWidget.addErrorMessage(self.trUtf8("Socket Error"),
                self.trUtf8("The connection was refused by the peer. Please check the"
                            " host name and port settings."))
        else:
            self.networkWidget.addErrorMessage(self.trUtf8("Socket Error"),
                self.trUtf8("The following network error occurred:<br/>{0}").format(
                self.__socket.errorString()))
    
    def __setUserPrivilegePrefix(self, prefix1, prefix2):
        """
        Private method to set the user privilege prefix.
        
        @param prefix1 first part of the prefix (string)
        @param prefix2 indictors the first part gets mapped to (string)
        """
        # PREFIX=(ov)@+
        # o = @ -> @ircbot , channel operator
        # v = + -> +userName , voice operator
        for i in range(len(prefix1)):
            self.__userPrefix["+" + prefix1[i]] = prefix2[i]
            self.__userPrefix["-" + prefix1[i]] = ""
    
    def __ping(self, match):
        """
        Private method to handle a PING message.
        
        @param reference to the match object
        @return flag indicating, if the message was handled (boolean)
        """
        self.__send("PONG " + match.group(1))
        return True
    
    def __updateUsersCount(self):
        """
        Private method to update the users count on the channel tabs.
        """
        for channel in self.__channelList:
            index = self.channelsWidget.indexOf(channel)
            self.channelsWidget.setTabText(index,
                self.trUtf8("{0} ({1})", "channel name, users count").format(
                channel.name(), channel.getUsersCount()))
    
    def __handleNickInUseLogin(self):
        """
        Private method to handle a 443 server error at login.
        """
        self.__nickIndex += 1
        try:
            nick = self.__ircNetworkManager.getIdentity(self.__userName)\
                .getNickNames()[self.__nickIndex]
            self.__nickName = nick
        except IndexError:
            self.networkWidget.addServerMessage(self.trUtf8("Critical"),
                self.trUtf8("No nickname acceptable to the server configured"
                            " for <b>{0}</b>. Disconnecting...").format(self.__userName))
            self.__connectNetwork("", False)
            self.__nickName = ""
            self.__nickIndex = -1
            return
        
        self.networkWidget.setNickName(nick)
        self.__send("NICK " + nick)
    
    def __handleNickInUse(self):
        """
        Private method to handle a 443 server error.
        """
        self.networkWidget.addServerMessage(self.trUtf8("Critical"),
            self.trUtf8("The given nickname is already in use."))
    
    def __changeNick(self, nick):
        """
        Private slot to use a new nick name.
        
        @param nick nick name to use (str)
        """
        self.__send("NICK " + nick)
    
    def __setChannelTypePrefixes(self, prefixes):
        """
        Private method to set the channel type prefixes.
        
        @param prefixes channel prefix characters (string)
        """
        self.__channelTypePrefixes = prefixes
    
    def __isChannelName(self, name):
        """
        Private method to check, if the given name is a channel name.
        
        @return flag indicating a channel name (boolean)
        """
        if not name:
            return False
        
        if self.__channelTypePrefixes:
            return name[0] in self.__channelTypePrefixes
        else:
            return name[0] in "#&"
