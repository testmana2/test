# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the IRC data structures and their manager.
"""

from PyQt4.QtCore import pyqtSignal, QObject

import Utilities
from Utilities.AutoSaver import AutoSaver
from Utilities.crypto import pwConvert
import Preferences


class IrcIdentity(QObject):
    """
    Class implementing the IRC identity object.
    """
    def __init__(self, name, parent=None):
        """
        Constructor
        
        @param name name of the identity (string)
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__name = name
        self.__realName = ""
        self.__nickNames = []
        self.__serviceName = ""
        self.__password = ""
    
    def save(self, settings):
        """
        Public method to save the identity data.
        
        @param settings reference to the settings object (QSettings)
        """
        # no need to save the name because that is the group key
        settings.setValue("RealName", self.__realName)
        settings.setValue("NickNames", self.__nickNames)
        settings.setValue("ServiceName", self.__serviceName)
        settings.setValue("Password", self.__password)
    
    def load(self, settings):
        """
        Public method to load the identity data.
        
        @param settings reference to the settings object (QSettings)
        """
        self.__realName = settings.value("RealName", "")
        self.__nickNames = Preferences.toList(settings.value("NickNames"), [])
        self.__serviceName = settings.value("ServiceName", "")
        self.__password = settings.value("Password", "")
    
    def getName(self):
        """
        Public method to get the identity name.
        
        @return identity name (string)
        """
        return self.__name
    
    def setRealName(self, name):
        """
        Public method to set the real name of the identity.
        
        @param name real name (string)
        """
        self.__realName = name
    
    def getRealName(self):
        """
        Public method to get the real name.
        
        @return real name (string)
        """
        return self.__realName
    
    def setNickNames(self, names):
        """
        Public method to set the nick names of the identity.
        
        @param name nick names (list of string)
        """
        self.__nickNames = names[:]
    
    def getNickNames(self):
        """
        Public method to get the nick names.
        
        @return nick names (list of string)
        """
        return self.__nickNames
    
    def setServiceName(self, name):
        """
        Public method to set the service name of the identity used for identification.
        
        @param name service name (string)
        """
        self.__serviceName = name
    
    def getServiceName(self):
        """
        Public method to get the service name of the identity used for identification.
        
        @return service name (string)
        """
        return self.__serviceName
    
    def setPassword(self, password):
        """
        Public method to set a new password.
        
        @param password password to set (string)
        """
        self.__password = pwConvert(password, encode=True)
    
    def getPassword(self):
        """
        Public method to get the password.
        
        @return password (string)
        """
        return pwConvert(self.__password, encode=False)


class IrcServer(QObject):
    """
    Class implementing the IRC identity object.
    """
    DefaultPort = 6667
    
    def __init__(self, name, parent=None):
        """
        Constructor
        
        @param name name of the server (string)
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__server = name
        self.__port = IrcServer.DefaultPort
        self.__ssl = False
        self.__password = ""
    
    def save(self, settings):
        """
        Public method to save the server data.
        
        @param settings reference to the settings object (QSettings)
        """
        # no need to save the server name because that is the group key
        settings.setValue("Port", self.__port)
        settings.setValue("SSL", self.__ssl)
        settings.setValue("Password", self.__password)
    
    def load(self, settings):
        """
        Public method to load the server data.
        
        @param settings reference to the settings object (QSettings)
        """
        self.__port = int(settings.value("Port", IrcServer.DefaultPort))
        self.__ssl = Preferences.toBool(settings.value("SSL", False))
        self.__password = settings.value("Password", "")
    
    def getServer(self):
        """
        Public method to get the server name.
        
        @return server name (string)
        """
        return self.__server
    
    def getPort(self):
        """
        Public method to get the server port number.
        
        @return port number (integer)
        """
        return self.__port
    
    def setPort(self, port):
        """
        Public method to set the server port number.
        
        @param server port number (integer)
        """
        self.__port = port
    
    def useSSL(self):
        """
        Public method to check for SSL usage.
        
        @return flag indicating SSL usage (boolean)
        """
        return self.__ssl
    
    def setUseSSL(self, on):
        """
        Public method to set the SSL usage.
        
        @param on flag indicating SSL usage (boolean)
        """
        self.__ssl = on
    
    def setPassword(self, password):
        """
        Public method to set a new password.
        
        @param password password to set (string)
        """
        self.__password = pwConvert(password, encode=True)
    
    def getPassword(self):
        """
        Public method to get the password.
        
        @return password (string)
        """
        return pwConvert(self.__password, encode=False)


class IrcNetwork(QObject):
    """
    Class implementing the IRC identity object.
    """
    def __init__(self, name, parent=None):
        """
        Constructor
        
        @param name name of the network (string)
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__name = name
        self.__identity = ""
        self.__server = ""
        self.__channels = []
        self.__autoJoinChannels = False
    
    def save(self, settings):
        """
        Public method to save the network data.
        
        @param settings reference to the settings object (QSettings)
        """
        # no need to save the network name because that is the group key
        settings.setValue("Identity", self.__identity)
        settings.setValue("Server", self.__server)
        settings.setValue("Channels", self.__channels)
        settings.setValue("AutoJoinChannels", self.__autoJoinChannels)
    
    def load(self, settings):
        """
        Public method to load the network data.
        
        @param settings reference to the settings object (QSettings)
        """
        self.__identity = settings.value("Identity", "")
        self.__server = settings.value("Server", "")
        self.__channels = Preferences.toList(settings.value("Channels", []))
        self.__autoJoinChannels = Preferences.toBool(
            settings.value("AutoJoinChannels", False))
    
    def getName(self):
        """
        Public method to get the network name.
        
        @return network name (string)
        """
        return self.__name
    
    def setIdentityName(self, name):
        """
        Public method to set the name of the identity.
        
        @param name identity name (string)
        """
        self.__identity = name
    
    def getIdentityName(self):
        """
        Public method to get the name of the identity.
        
        @return identity name (string)
        """
        return self.__identity
    
    def setServerName(self, name):
        """
        Public method to set the server name.
        
        @param name server name (string)
        """
        self.__server = name
    
    def getServerName(self):
        """
        Public method to get the server name.
        
        @return server name (string)
        """
        return self.__server
    
    def setChannels(self, channels):
        """
        Public method to set the list of channels.
        
        @param channels list of channels (list of string)
        """
        self.__channels = channels[:]
    
    def getChannels(self):
        """
        Public method to get the list of channels.
        
        @return list of channels (list of string)
        """
        return self.__channels[:]
    
    def setAutoJoinChannels(self, on):
        """
        Public method to enable channel auto joining.
        
        @param on flag indicating to join the channels after connecting
            to the server (boolean)
        """
        self.__autoJoinChannels = on
    
    def autoJoinChannels(self):
        """
        Public method to check, if channel auto joining is enabled.
        
        @return flag indicating to join the channels after connecting
            to the server (boolean)
        """
        return self.__autoJoinChannels


class IrcNetworkManager(QObject):
    """
    Class implementing the IRC identity object.
    """
    dataChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__loaded = False
        self.__saveTimer = AutoSaver(self, self.save)
        
        self.__settings = Preferences.Prefs.settings
        
        self.__networks = {}
        self.__identities = {}
        self.__servers = {}
        
        self.dataChanged.connect(self.__saveTimer.changeOccurred)
    
    def close(self):
        """
        Public method to close the open search engines manager.
        """
        self.__saveTimer.saveIfNeccessary()
    
    def save(self):
        """
        Public slot to save the IRC data.
        """
        if not self.__loaded:
            return
        
        # save IRC data
        self.__settings.beginGroup("IRC")
        
        # identities
        self.__settings.beginGroup("Identities")
        for key in self.__identities:
            self.__settings.beginGroup(key)
            self.__identities[key].save(self.__settings)
            self.__settings.endGroup()
        self.__settings.endGroup()
        
        # servers
        self.__settings.beginGroup("Servers")
        for key in self.__servers:
            self.__settings.beginGroup(key)
            self.__servers[key].save(self.__settings)
            self.__settings.endGroup()
        self.__settings.endGroup()
        
        # networks
        self.__settings.beginGroup("Networks")
        for key in self.__networks:
            self.__settings.beginGroup(key)
            self.__networks[key].save(self.__settings)
            self.__settings.endGroup()
        self.__settings.endGroup()
        
        self.__settings.endGroup()
    
    def __load(self):
        """
        Private slot to load the IRC data.
        """
        if self.__loaded:
            return
        
        # load IRC data
        self.__settings.beginGroup("IRC")
        
        # identities
        self.__settings.beginGroup("Identities")
        for key in self.__settings.childKeys():
            self.__identities[key] = IrcIdentity(key, self)
            self.__settings.beginGroup(key)
            self.__identities[key].load(self.__settings)
            self.__settings.endGroup()
        self.__settings.endGroup()
        
        # servers
        self.__settings.beginGroup("Servers")
        for key in self.__settings.childKeys():
            self.__servers[key] = IrcServer(key, self)
            self.__settings.beginGroup(key)
            self.__servers[key].load(self.__settings)
            self.__settings.endGroup()
        self.__settings.endGroup()
        
        # networks
        self.__settings.beginGroup("Networks")
        for key in self.__settings.childKeys():
            self.__networks[key] = IrcNetwork(key, self)
            self.__settings.beginGroup(key)
            self.__networks[key].load(self.__settings)
            self.__settings.endGroup()
        self.__settings.endGroup()
        
        self.__settings.endGroup()
        
        if not self.__identities or \
           not self.__servers or \
           not self.__networks:
            # data structures got corrupted; load defaults
            self.__loadDefaults()
        
        self.__loaded = True
    
    def __loadDefaults(self):
        """
        Private method to load default values.
        """
        self.__networks = {}
        self.__identities = {}
        self.__servers = {}
        
        # identity
        userName = Utilities.getUserName()
        identity = IrcIdentity(userName, self)
        identity.setNickNames([userName, userName + "_", userName + "__"])
        self.__identities[userName] = identity
        
        # server
        serverName = "chat.freenode.net"
        server = IrcServer(serverName, self)
        server.setPort(8001)
        self.__servers[serverName] = server
        
        # network
        networkName = "Freenode"
        network = IrcNetwork(networkName, self)
        network.setIdentityName(userName)
        network.setServerName(serverName)
        network.setChannels(["#eric-ide"])
        self.__networks[networkName] = network
        
        self.dataChanged.emit()
    
    def getIdentity(self, name, create=False):
        """
        Public method to get an identity object.
        
        @param name name of the identity to get (string)
        @param create flag indicating to create a new object,
            if none exists (boolean)
        @return reference to the identity (IrcIdentity)
        """
        if not name:
            return None
        
        if not self.__loaded:
            self.__load()
        
        if name in self.__identities:
            return self.__identities[name]
        elif create:
            id = IrcIdentity(name, self)
            self.__identities[name] = id
            
            self.dataChanged.emit()
            
            return id
        else:
            return None
    
    def identityChanged(self):
        """
        Public method to indicate a change of an identity object.
        """
        self.dataChanged.emit()
    
    def getServer(self, name, create=False):
        """
        Public method to get a server object.
        
        @param name name of the server to get (string)
        @param create flag indicating to create a new object,
            if none exists (boolean)
        @return reference to the server (IrcServer)
        """
        if not name:
            return None
        
        if not self.__loaded:
            self.__load()
        
        if name in self.__servers:
            return self.__servers[name]
        elif create:
            server = IrcServer(name, self)
            self.__servers[name] = server
            
            self.dataChanged.emit()
            
            return server
        else:
            return None
    
    def serverChanged(self):
        """
        Public method to indicate a change of a server object.
        """
        self.dataChanged.emit()
    
    def getNetwork(self, name):
        """
        Public method to get a network object.
        
        @param name name of the network (string)
        @return reference to the network object (IrcNetwork)
        """
        if not self.__loaded:
            self.__load()
        
        if name in self.__networks:
            return self.__networks[name]
        else:
            return None
    
    def createNetwork(self, name, identity, server, channels=None,
                      autoJoinChannels=False):
        """
        Public method to create a new network object.
        
        @param name name of the network (string)
        @param identity reference to an identity object to associate with
            this network (IrcIdentity)
        @param server reference to a server object to associate with this
            network (IrcServer)
        @param channels list of channels for the network (list of string)
        @param autoJoinChannels flag indicating to join the channels
            automatically (boolean)
        @return reference to the created network object (IrcNetwork)
        """
        if not self.__loaded:
            self.__load()
        
        if name in self.__networks:
            return None
        
        network = IrcNetwork(name)
        network.setIdentityName(identity.getName())
        network.setServerName(server.getServer())
        network.setChannels(channels[:])
        network.setAutoJoinChannels(autoJoinChannels)
        self.__networks[name] = network
        
        self.networkChanged()
        
        return network
    
    def networkChanged(self):
        """
        Public method to indicate a change of a network object.
        """
        self.dataChanged.emit()
    
    def getNetworkNames(self):
        """
        Public method to get a list of all known network names.
        
        @return list of network names (list of string)
        """
        if not self.__loaded:
            self.__load()
        
        return sorted(self.__networks.keys())
