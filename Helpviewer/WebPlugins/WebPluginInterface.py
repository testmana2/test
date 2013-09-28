# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the web plug-in interface.
"""

from PyQt4.QtGui import QWidget
from PyQt4.QtWebKit import QWebPluginFactory


class WebPluginInterface(object):
    """
    Class implementing the web plug-in interface.
    """
    def metaPlugin(self):
        """
        Public method to create a meta plug-in object containing plug-in info.
        
        @return meta plug-in object (QWebPluginFactory.Plugin)
        @exception NotImplementedError raised to indicate that this method
            must be implemented by subclasses
        """
        raise NotImplementedError
        return QWebPluginFactory.Plugin()
    
    def create(self, mimeType, url, argumentNames, argumentValues):
        """
        Public method to create a plug-in instance for the given data.
        
        @param mimeType MIME type for the plug-in (string)
        @param url URL for the plug-in (QUrl)
        @param argumentNames list of argument names (list of strings)
        @param argumentValues list of argument values (list of strings)
        @return reference to the created object (QWidget)
        @exception NotImplementedError raised to indicate that this method
            must be implemented by subclasses
        """
        raise NotImplementedError
        return QWidget()
    
    def configure(self):
        """
        Public method to configure the plug-in.
        
        @exception NotImplementedError raised to indicate that this method
            must be implemented by subclasses
        """
        raise NotImplementedError
    
    def isAnonymous(self):
        """
        Public method to indicate an anonymous plug-in.
        
        @return flag indicating anonymous state (boolean)
        """
        return False
