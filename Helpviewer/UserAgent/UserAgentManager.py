# -*- coding: utf-8 -*-

# Copyright (c) 2012 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a user agent manager.
"""

import os

from PyQt4.QtCore import pyqtSignal, QObject

from E5Gui import E5MessageBox

from Utilities.AutoSaver import AutoSaver
import Utilities


class UserAgentManager(QObject):
    """
    Class implementing a user agent manager.
    
    @signal changed() emitted to indicate a change
    """
    changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super().__init__(parent)
        
        self.__agents = {}      # dictionary with agent strings indexed by host name
        self.__loaded = False
        self.__saveTimer = AutoSaver(self, self.save)
        
        self.changed.connect(self.__saveTimer.changeOccurred)
    
    def getFileName(self):
        """
        Public method to get the file name of the user agents file.
        
        @return name of the user agents file (string)
        """
        return os.path.join(Utilities.getConfigDir(), "browser", "userAgentSettings")
    
    def save(self):
        """
        Public slot to save the user agent entries to disk.
        """
        if not self.__loaded:
            return
        
        agentFile = self.getFileName()
        try:
            f = open(agentFile, "w", encoding="utf-8")
            for host, agent in self.__agents.items():
                f.write("{0}@@{1}\n".format(host, agent))
            f.close()
        except IOError as err:
            E5MessageBox.critical(None,
                self.trUtf8("Saving user agent data"),
                self.trUtf8("""<p>User agent data could not be saved to <b>{0}</b></p>"""
                            """<p>Reason: {1}</p>""").format(agentFile, str(err)))
            return
    
    def __load(self):
        """
        Private method to load the saved user agent settings.
        """
        agentFile = self.getFileName()
        if os.path.exists(agentFile):
            try:
                f = open(agentFile, "r", encoding="utf-8")
                lines = f.read()
                f.close()
            except IOError as err:
                E5MessageBox.critical(None,
                    self.trUtf8("Loading user agent data"),
                    self.trUtf8("""<p>User agent data could not be loaded """
                                """from <b>{0}</b></p>"""
                                """<p>Reason: {1}</p>""")\
                        .format(agentFile, str(err)))
                return
            
            for line in lines.splitlines():
                if not line or \
                   line.startswith("#") or \
                   "@@" not in line:
                    continue
                
                host, agent = line.split("@@", 1)
                self.__agents[host] = agent
        
        self.__loaded = True
    
    def close(self):
        """
        Public method to close the user agents manager.
        """
        self.__saveTimer.saveIfNeccessary()
    
    def removeUserAgent(self, host):
        """
        Public method to remove a user agent entry.
        
        @param host host name (string)
        """
        if host in self.__agents:
            del self.__agents[host]
            self.changed.emit()
    
    def allHostNames(self):
        """
        Public method to get a list of all host names we a user agent setting for.
        
        @return sorted list of all host names (list of strings)
        """
        if not self.__loaded:
            self.__load()
        
        return sorted(self.__agents.keys())
    
    def hostsCount(self):
        """
        Public method to get the number of available user agent settings.
        
        @return number of user agent settings (integer)
        """
        if not self.__loaded:
            self.__load()
        
        return len(self.__agents)
    
    def userAgent(self, host):
        """
        Public method to get the user agent setting for a host.
        
        @param host host name (string)
        @return user agent string (string)
        """
        if not self.__loaded:
            self.__load()
        
        if host not in self.__agents:
            return ""
        
        return self.__agents[host]
    
    def setUserAgent(self, host, agent):
        """
        Public method to set the user agent string for a host.
        
        @param host host name (string)
        @param agent user agent string (string)
        """
        if host != "" and agent != "":
            self.__agents[host] = agent
            self.changed.emit()
    
    def userAgentForUrl(self, url):
        """
        Publci method to determine the user agent for the given URL.
        
        @param url URL to determine user agent for (QUrl)
        @return user agent string (string)
        """
        if url.isValid():
            host = url.host()
            return self.userAgent(host)
        
        return ""
    
    def setUserAgentForUrl(self, url, agent):
        """
        Public method to set the user agent string for an URL.
        
        @param url URL to register user agent setting for (QUrl)
        @param agent new current user agent string (string)
        """
        if url.isValid():
            host = url.host()
            self.setUserAgent(host, agent)
