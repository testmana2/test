# -*- coding: utf-8 -*-

# Copyright (c) 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module to read the plug-in repository contents file.
"""

from .Config import pluginRepositoryFileFormatVersion
from .XMLStreamReaderBase import XMLStreamReaderBase

import Preferences

class PluginRepositoryReader(XMLStreamReaderBase):
    """
    Class to read the plug-in repository contents file.
    """
    def __init__(self, device, dlg):
        """
        Constructor
        
        @param device reference to the I/O device to read from (QIODevice)
        @param dlg reference to the plug-in repository dialog
        """
        XMLStreamReaderBase.__init__(self, device)
        
        self.dlg = dlg
        
        self.version = ""
    
    def readXML(self):
        """
        Public method to read and parse the XML document.
        """
        while not self.atEnd():
            self.readNext()
            if self.isStartElement():
                if self.name() == "Plugins":
                    self.version = self.attribute("version", 
                        pluginRepositoryFileFormatVersion)
                elif self.name() == "RepositoryUrl":
                    url = self.readElementText()
                    Preferences.setUI("PluginRepositoryUrl5", url)
                elif self.name() == "Plugin":
                    info = {"name"         : "",
                            "short"        : "",
                            "description"  : "",
                            "url"          : "",
                            "author"       : "",
                            "version"      : "", 
                            "filename"     : "",
                    }
                    info["status"] = self.attribute("status", "unknown")
                    self.__readPlugin(info)
                    self.dlg.addEntry(info["name"], info["short"], 
                                      info["description"], info["url"], 
                                      info["author"], info["version"],
                                      info["filename"], info["status"])
        
        self.showErrorMessage()
    
    def __readPlugin(self, pluginInfo):
        """
        Private method to read the plug-in info.
        
        @param pluginInfo reference to the dictionary to hold the result
        @return reference to the populated dictionary
        """
        while not self.atEnd():
            self.readNext()
            if self.isEndElement() and self.name() == "Plugin":
                return pluginInfo
            
            if self.isStartElement():
                if self.name() == "Name":
                    pluginInfo["name"] = self.readElementText()
                elif self.name() == "Short":
                    pluginInfo["short"] = self.readElementText()
                elif self.name() == "Description":
                    txt = self.readElementText()
                    pluginInfo["description"] = \
                        [line.strip() for line in txt.splitlines()]
                elif self.name() == "Url":
                    pluginInfo["url"] = self.readElementText()
                elif self.name() == "Author":
                    pluginInfo["author"] = self.readElementText()
                elif self.name() == "Version":
                    pluginInfo["version"] = self.readElementText()
                elif self.name() == "Filename":
                    pluginInfo["filename"] = self.readElementText()
