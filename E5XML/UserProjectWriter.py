# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the writer class for writing an XML user project properties file.
"""

import time

from E5Gui.E5Application import e5App

from .XMLWriterBase import XMLWriterBase
from .Config import userProjectFileFormatVersion

import Preferences

class UserProjectWriter(XMLWriterBase):
    """
    Class implementing the writer class for writing an XML user project properties  file.
    """
    def __init__(self, file, projectName):
        """
        Constructor
        
        @param file open file (like) object for writing
        @param projectName name of the project (string)
        """
        XMLWriterBase.__init__(self, file)
        
        self.pudata = e5App().getObject("Project").pudata
        self.pdata = e5App().getObject("Project").pdata
        self.name = projectName
        
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        XMLWriterBase.writeXML(self)
        
        self._write('<!DOCTYPE UserProject SYSTEM "UserProject-{0}.dtd">'.format(
            userProjectFileFormatVersion))
        
        # add some generation comments
        self._write("<!-- eric5 user project file for project {0} -->".format(self.name))
        if Preferences.getProject("XMLTimestamp"):
            self._write("<!-- Saved: {0} -->".format(time.strftime('%Y-%m-%d, %H:%M:%S')))
            self._write("<!-- Copyright (C) {0} {1}, {2} -->".format(
                    time.strftime('%Y'), 
                    self.escape(self.pdata["AUTHOR"][0]), 
                    self.escape(self.pdata["EMAIL"][0])))
        
        # add the main tag
        self._write('<UserProject version="{0}">'.format(userProjectFileFormatVersion))
        
        # do the vcs override stuff
        if self.pudata["VCSOVERRIDE"]:
            self._write("  <VcsType>{0}</VcsType>".format(self.pudata["VCSOVERRIDE"][0]))
        if self.pudata["VCSSTATUSMONITORINTERVAL"]:
            self._write('  <VcsStatusMonitorInterval value="{0:d}" />'.format(
                self.pudata["VCSSTATUSMONITORINTERVAL"][0]))
        
        self._write("</UserProject>", newline = False)
