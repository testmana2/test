# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the writer class for writing an XML project debugger properties file.
"""

import time

from E5Gui.E5Application import e5App

from .XMLWriterBase import XMLWriterBase
from .Config import debuggerPropertiesFileFormatVersion

import Preferences

class DebuggerPropertiesWriter(XMLWriterBase):
    """
    Class implementing the writer class for writing an XML project debugger properties
    file.
    """
    def __init__(self, file, projectName):
        """
        Constructor
        
        @param file open file (like) object for writing
        @param projectName name of the project (string)
        """
        XMLWriterBase.__init__(self, file)
        
        self.name = projectName
        self.project = e5App().getObject("Project")
        
    def writeXML(self):
        """
        Public method to write the XML to the file.
        """
        XMLWriterBase.writeXML(self)
        
        self._write('<!DOCTYPE DebuggerProperties SYSTEM "DebuggerProperties-{0}.dtd">'\
            .format(debuggerPropertiesFileFormatVersion))
        
        # add some generation comments
        self._write("<!-- eric5 debugger properties file for project {0} -->"\
            .format(self.name))
        self._write("<!-- This file was generated automatically, do not edit. -->")
        if Preferences.getProject("XMLTimestamp"):
            self._write("<!-- Saved: {0} -->".format(time.strftime('%Y-%m-%d, %H:%M:%S')))
        
        # add the main tag
        self._write('<DebuggerProperties version="{0}">'.format(
            debuggerPropertiesFileFormatVersion))
        
        self._write('  <Interpreter>{0}</Interpreter>'.format(
            self.project.debugProperties["INTERPRETER"]))
        
        self._write('  <DebugClient>{0}</DebugClient>'.format(
            self.project.debugProperties["DEBUGCLIENT"]))
        
        self._write('  <Environment override="{0:d}">{1}</Environment>'.format(
            self.project.debugProperties["ENVIRONMENTOVERRIDE"],
            self.escape(self.project.debugProperties["ENVIRONMENTSTRING"])))
        
        self._write('  <RemoteDebugger on="{0:d}">'.format(
            self.project.debugProperties["REMOTEDEBUGGER"]))
        self._write('    <RemoteHost>{0}</RemoteHost>'.format(
            self.project.debugProperties["REMOTEHOST"]))
        self._write('    <RemoteCommand>{0}</RemoteCommand>'.format(
            self.escape(self.project.debugProperties["REMOTECOMMAND"])))
        self._write('  </RemoteDebugger>')
        
        self._write('  <PathTranslation on="{0:d}">'.format(
            self.project.debugProperties["PATHTRANSLATION"]))
        self._write('    <RemotePath>{0}</RemotePath>'.format(
            self.project.debugProperties["REMOTEPATH"]))
        self._write('    <LocalPath>{0}</LocalPath>'.format(
            self.project.debugProperties["LOCALPATH"]))
        self._write('  </PathTranslation>')
        
        self._write('  <ConsoleDebugger on="{0:d}">{1}</ConsoleDebugger>'.format(
            self.project.debugProperties["CONSOLEDEBUGGER"],
            self.escape(self.project.debugProperties["CONSOLECOMMAND"])))
        
        self._write('  <Redirect on="{0:d}" />'.format(
            self.project.debugProperties["REDIRECT"]))
        
        self._write('  <Noencoding on="{0:d}" />'.format(
            self.project.debugProperties["NOENCODING"]))
        
        self._write("</DebuggerProperties>", newline = False)
