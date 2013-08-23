# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2013 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the web plug-in interface.
"""


class WebPluginInterface(object):
    """
    Class implementing the web plug-in interface.
    """
    def metaPlugin(self):
        """
        Public method to create a meta plug-in object containing plug-in info.
        
        @return meta plug-in object (QWebPluginFactory.Plugin)
        """
        raise NotImplementedError
    
    def create(self, mimeType, url, argumentNames, argumentValues):
        """
        Public method to create a plug-in instance for the given data.
        
        @param mimeType MIME type for the plug-in (string)
        @param url URL for the plug-in (QUrl)
        @param argumentNames list of argument names (list of strings)
        @param argumentValues list of argument values (list of strings)
        @return reference to the created object (QWidget)
        """
        raise NotImplementedError
    
    def configure(self):
        """
        Public method to configure the plug-in.
        """
        raise NotImplementedError
    
    def isAnonymous(self):
        """
        Public method to indicate an anonymous plug-in.
        """
        return False
